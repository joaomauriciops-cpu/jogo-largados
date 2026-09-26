"""Simulador de Largados e Pelados — regras v0.4.

Implementa as regras do manual 0.4 e uma IA heurística (gulosa, com
planejamento de fim de jogo) para rodar milhares de partidas e medir
taxa de conclusão, pontuação, equilíbrio de arquétipos e de assentos.

Uso rápido:
    python3 sim.py                # relatório padrão
    python3 sim.py --trace 4      # imprime o log de uma partida com 4 pessoas
    python3 sim.py --v06          # mesmas medições com a proposta v0.6
"""
from __future__ import annotations

import argparse
import collections
import copy
import random
import statistics
from dataclasses import dataclass, field

# ---------------------------------------------------------------- regras

TILE_RES = {
    'F': {'wood': 2},
    'Ca': {'water': 3},
    'Cl': {'food': 2, 'wood': 1},
    'P': {'food': 2, 'water': 1},
    'R': {'food': 1, 'water': 1},
    'Ac': {'food': 3},
    'Re': {}, 'I': {}, 'Pa': {},
}
RISK_TILES = {'P', 'Ac'}
TILE_COUNTS = {
    2: {'F': 3, 'Ca': 2, 'Cl': 3, 'P': 2, 'R': 3, 'Ac': 2, 'Re': 2, 'I': 1, 'Pa': 2},
    3: {'F': 4, 'Ca': 3, 'Cl': 4, 'P': 3, 'R': 4, 'Ac': 3, 'Re': 2, 'I': 1, 'Pa': 1},
    4: {'F': 4, 'Ca': 4, 'Cl': 5, 'P': 3, 'R': 5, 'Ac': 4, 'Re': 3, 'I': 1, 'Pa': 1},
}
GRID = {2: (4, 5), 3: (5, 5), 4: (5, 6)}
EVENTS = {
    'comida': 6, 'agua': 4, 'madeira': 3,
    'faca': 1, 'panela': 1, 'cantil': 1, 'rede': 1, 'toldo': 1,
    'pista': 4, 'nada': 4, 'atraso': 2, 'cansaco': 1, 'vazamento': 1,
}
ITEMS = {'faca', 'panela', 'cantil', 'rede', 'toldo'}
ARCHETYPES = ['Cacador', 'Coletor', 'Pescador', 'Construtor', 'Sobrevivencialista']
RES = ('food', 'water', 'wood')


@dataclass
class Config:
    pe: int = 4
    rounds: int = 9
    week_food: tuple = (2, 3, 3)
    week_water: tuple = (1, 1, 2)
    shelter_levels: int = 3
    tile_counts: dict = None          # None -> TILE_COUNTS
    tile_res: dict = None             # None -> TILE_RES
    events: dict = None               # None -> EVENTS
    mode: str = 'comp'                # 'comp' ou 'coop'
    spoil: bool = True
    exh_limit: int = 3
    rest_cost: int = 2
    week_points: int = 3
    exh_penalty: int = 2
    caps: tuple = (3, 2, 2)           # limites de pontuação food/water/wood
    # variantes de regra (propostas)
    order: str = 'rotate'             # 'rotate' | 'snake' | 'catchup'
    restock: int = 0                  # comida devolvida a cada tile de comida no início das semanas 2 e 3
    exh_pe: int = 0                   # se >0: com essa Exaustão ou mais, recebe 1 PE a menos por vez
    hunter_safe: bool = False         # Caçador não rola o dado de risco
    hunter_fail_faces: int = 0        # se >0: Caçador só falha o risco com resultado <= esse valor
    builder_start_wood: int = 0       # Construtor começa com essa madeira
    coop_shelter_cap: int = 0         # coop: até N pessoas podem morar no mesmo abrigo (0 = desligado)
    transfer_range: int = 0           # coop: 0 = mesmo tile, 1 = também tiles adjacentes
    transfer_pe: int = 1              # coop: custo de Transferir
    pool_at_check: bool = False       # coop: na Prova, quem divide o tile junta comida e água
    care: bool = False                # coop: Cuidar (1 PE + 1 comida sua: colega no mesmo tile perde 1 Exaustão)
    reveal_ring1: bool = False        # vizinhos do Início começam revelados (sem Evento)
    collect_limit: str = 'tile'       # 'tile' (manual) | 'player' | 'none'
    surv_mode: str = 'risk'           # 'risk' (manual) | 'any' (qualquer Exaustão de dado/evento)
    # IA
    ai: dict = field(default_factory=dict)

    def counts(self, n):
        return (self.tile_counts or TILE_COUNTS)[n]

    def res(self):
        return self.tile_res or TILE_RES


# ------------------------------------------------------------- hexágonos

def neighbors(c, r, cols, rows):
    # linhas ímpares deslocadas para a direita (odd-r)
    if r % 2 == 0:
        d = [(-1, -1), (0, -1), (-1, 0), (1, 0), (-1, 1), (0, 1)]
    else:
        d = [(0, -1), (1, -1), (-1, 0), (1, 0), (0, 1), (1, 1)]
    out = []
    for dc, dr in d:
        nc, nr = c + dc, r + dr
        if 0 <= nc < cols and 0 <= nr < rows:
            out.append((nc, nr))
    return out


def to_cube(c, r):
    x = c - (r - (r & 1)) // 2
    z = r
    return x, -x - z, z


def hexdist(a, b):
    ax, ay, az = to_cube(*a)
    bx, by, bz = to_cube(*b)
    return max(abs(ax - bx), abs(ay - by), abs(az - bz))


# ----------------------------------------------------------------- estado

@dataclass
class Tile:
    kind: str
    revealed: bool = False
    tokens: dict = field(default_factory=lambda: {'food': 0, 'water': 0, 'wood': 0})
    risk: bool = False
    collected_round: int = 0
    collected_by: set = field(default_factory=set)


@dataclass
class Player:
    idx: int
    arch: str
    pos: tuple
    food: int = 0
    water: int = 0
    wood: int = 0
    items: list = field(default_factory=list)
    exh: int = 0
    shelter_pos: tuple = None
    shelter: int = 0
    alive: bool = True
    ability_used: bool = False
    rest_used: bool = False
    weeks_paid: int = 0
    pe: int = 0
    known: dict = field(default_factory=dict)   # pistas: pos -> tipo
    ai: dict = field(default_factory=dict)      # parâmetros de IA deste jogador
    group: list = None                          # moradores do mesmo abrigo (coop)
    transfers: int = 0
    cared: bool = False                         # já recebeu Cuidar nesta semana
    cares: int = 0
    # estatísticas
    exh_src: collections.Counter = field(default_factory=collections.Counter)
    pe_unused: int = 0
    reveals: int = 0
    collects: int = 0
    died_round: int = 0
    good_ev: int = 0
    bad_ev: int = 0

    def get(self, r):
        return getattr(self, r)

    def add(self, r, n):
        setattr(self, r, getattr(self, r) + n)


class Game:
    def __init__(self, n, cfg: Config, rng: random.Random, trace=False):
        self.n, self.cfg, self.rng, self.trace = n, cfg, rng, trace
        self.cols, self.rows = GRID[n]
        self.cells = [(c, r) for r in range(self.rows) for c in range(self.cols)]
        self.adj = {p: neighbors(*p, self.cols, self.rows) for p in self.cells}
        self.start = (self.cols // 2, (self.rows - 1) // 2)
        self._dist_cache = {}
        self.build_map()
        deck = [k for k, v in (cfg.events or EVENTS).items() for _ in range(v)]
        rng.shuffle(deck)
        self.deck, self.discard = deck, []
        archs = rng.sample(ARCHETYPES, n)
        self.players = [Player(i, archs[i], self.start) for i in range(n)]
        for p in self.players:
            if p.arch == 'Construtor':
                p.wood += cfg.builder_start_wood
        self.round = 0
        self.claims = {}
        self.log = []

    # -- montagem
    def build_map(self):
        cfg, rng = self.cfg, self.rng
        pool = [k for k, v in cfg.counts(self.n).items() for _ in range(v) if k != 'I']
        others = [p for p in self.cells if p != self.start]
        order = sorted(others, key=lambda p: (hexdist(p, self.start), rng.random()))
        near12 = set(order[:12])
        ring1 = set(self.adj[self.start])
        res = cfg.res()
        for _ in range(10000):
            rng.shuffle(pool)
            layout = dict(zip(others, pool))
            kinds1 = [layout[p] for p in ring1]
            ok = (any(res[k].get('food') for k in kinds1)
                  and any(res[k].get('water') for k in kinds1)
                  and any(res[k].get('wood') for k in kinds1)
                  and any(layout[p] == 'Re' for p in near12))
            if ok:
                break
        self.near12 = near12
        self.tiles = {self.start: Tile('I', revealed=True)}
        for p, k in layout.items():
            self.tiles[p] = Tile(k)
        if cfg.reveal_ring1:
            for p in ring1:
                t = self.tiles[p]
                t.revealed = True
                for r, v in res.get(t.kind, {}).items():
                    t.tokens[r] = v
                t.risk = t.kind in RISK_TILES

    def dist_map(self, src):
        if src in self._dist_cache:
            return self._dist_cache[src]
        d = {src: 0}
        q = collections.deque([src])
        while q:
            u = q.popleft()
            for v in self.adj[u]:
                if v not in d:
                    d[v] = d[u] + 1
                    q.append(v)
        self._dist_cache[src] = d
        return d

    def dist(self, a, b):
        return self.dist_map(a)[b]

    def week(self):
        return (self.round - 1) // 3

    def known_rescues(self):
        return [p for p, t in self.tiles.items() if t.revealed and t.kind == 'Re']

    def say(self, *a):
        if self.trace:
            print(*a)

    # -- ações
    def draw(self):
        if not self.deck:
            self.deck, self.discard = self.discard, []
            self.rng.shuffle(self.deck)
        return self.deck.pop() if self.deck else 'nada'

    def gain_exh(self, p, src):
        if ((src == 'evento' and self.cfg.surv_mode == 'any'
             or src != 'risco' and self.cfg.surv_mode == 'all')
                and p.arch == 'Sobrevivencialista' and not p.ability_used):
            p.ability_used = True
            return
        p.exh += 1
        p.exh_src[src] += 1
        if p.exh >= self.cfg.exh_limit and p.alive:
            p.alive = False
            p.died_round = self.round
            self.say(f'    !! P{p.idx} ({p.arch}) eliminado por Exaustão ({src})')

    def gain_item(self, p, it):
        p.items.append(it)
        if len(p.items) > 2:
            # descarta o menos valioso
            worst = min(p.items, key=lambda i: item_value(self, p, i))
            p.items.remove(worst)

    def move(self, p, dest):
        p.pe -= 1
        p.pos = dest
        t = self.tiles[dest]
        if not t.revealed:
            t.revealed = True
            p.reveals += 1
            for k, v in self.cfg.res().get(t.kind, {}).items():
                t.tokens[k] = v
            t.risk = t.kind in RISK_TILES
            for q in self.players:
                q.known.pop(dest, None)
            msg = f'entra em {t.kind}{dest}'
            if t.kind not in ('Re', 'I'):
                ev = self.draw()
                msg += f' evento={ev}'
                self.resolve_event(p, ev)
            self.say(f'    P{p.idx} {msg}')
        else:
            self.say(f'    P{p.idx} move {dest}')

    def resolve_event(self, p, ev):
        if ev in ('comida', 'agua', 'madeira') or ev in ITEMS:
            p.good_ev += 1
        elif ev in ('atraso', 'cansaco', 'vazamento'):
            p.bad_ev += 1
        if ev == 'comida':
            p.food += 1
        elif ev == 'agua':
            p.water += 1
        elif ev == 'madeira':
            p.wood += 1
        elif ev in ITEMS:
            self.gain_item(p, ev)
            return
        elif ev == 'pista':
            hidden = [q for q in self.adj[p.pos] if not self.tiles[q].revealed]
            if hidden:
                q = self.rng.choice(hidden)
                p.known[q] = self.tiles[q].kind
        elif ev == 'atraso':
            p.pe = max(0, p.pe - 1)
        elif ev == 'cansaco':
            self.gain_exh(p, 'evento')
        elif ev == 'vazamento':
            if p.water > 0:
                p.water -= 1
            else:
                self.gain_exh(p, 'evento')
        self.discard.append(ev)

    def bonus_applies(self, p, kind, res):
        if p.ability_used:
            return False
        a = p.arch
        return ((a == 'Cacador' and res == 'food' and kind in ('P', 'Ac'))
                or (a == 'Coletor' and res == 'food' and kind == 'Cl')
                or (a == 'Pescador' and res == 'food' and kind == 'R')
                or (a == 'Construtor' and res == 'wood' and kind in ('F', 'Cl')))

    def can_collect(self, p, pos):
        t = self.tiles[pos]
        lim = self.cfg.collect_limit
        if lim == 'none' or t.collected_round != self.round:
            return True
        if lim == 'player':
            return p.idx not in t.collected_by
        return False

    def collect(self, p, res):
        t = self.tiles[p.pos]
        p.pe -= 1
        t.tokens[res] -= 1
        if t.collected_round != self.round:
            t.collected_by = set()
        t.collected_round = self.round
        t.collected_by.add(p.idx)
        p.add(res, 1)
        p.collects += 1
        extra = ''
        if self.bonus_applies(p, t.kind, res):
            p.ability_used = True
            p.add(res, 1)
            extra += ' +bonus'
        if res == 'food':
            it = 'faca' if t.kind in ('P', 'Ac') else 'rede' if t.kind == 'R' else None
            if it and it in p.items and food_value(self, p, extra=0) > 0:
                p.items.remove(it)
                p.food += 1
                self.discard.append(it)
                extra += f' +{it}'
        if t.risk and self.cfg.hunter_safe and p.arch == 'Cacador':
            t.risk = False
            extra += ' (caçador: sem risco)'
        if t.risk:
            t.risk = False
            roll = self.rng.randint(1, 6)
            bad = roll % 2 == 1
            if self.cfg.hunter_fail_faces and p.arch == 'Cacador':
                bad = roll <= self.cfg.hunter_fail_faces
            if bad:
                if p.arch == 'Sobrevivencialista' and not p.ability_used:
                    p.ability_used = True
                    extra += f' dado {roll} ignorado'
                elif 'toldo' in p.items:
                    p.items.remove('toldo')
                    self.discard.append('toldo')
                    extra += f' dado {roll} toldo'
                else:
                    extra += f' dado {roll} EXAUSTÃO'
                    self.gain_exh(p, 'risco')
            else:
                extra += f' dado {roll} ok'
        self.say(f'    P{p.idx} coleta {res} em {t.kind}{p.pos}{extra}')

    def build(self, p):
        p.pe -= 1
        p.wood -= 1
        if p.shelter == 0:
            p.shelter_pos = p.pos
        p.shelter += 1
        if p.group is None:
            p.group = [p]
        for q in p.group:
            q.shelter, q.shelter_pos = p.shelter, p.shelter_pos
        self.say(f'    P{p.idx} abrigo nível {p.shelter} em {p.pos}')

    def join(self, p, host):
        p.pe -= 1
        host.group.append(p)
        p.group = host.group
        p.shelter, p.shelter_pos = host.shelter, host.shelter_pos
        self.say(f'    P{p.idx} passa a morar no abrigo de P{host.idx} (nível {host.shelter})')

    def rest(self, p):
        at = p.shelter > 0 and p.shelter_pos == p.pos
        p.pe -= 1 if at else self.cfg.rest_cost
        p.food -= 1
        p.rest_used = True
        rem = 2 if at and p.shelter >= 2 else 1
        p.exh = max(0, p.exh - rem)
        self.say(f'    P{p.idx} descansa (-{rem} exaustão)')

    def care(self, p, q):
        p.pe -= 1
        p.food -= 1
        p.cares += 1
        q.cared = True
        q.exh = max(0, q.exh - 1)
        self.say(f'    P{p.idx} cuida de P{q.idx} (-1 exaustão)')

    def transfer(self, p, q, res, n):
        p.pe -= self.cfg.transfer_pe
        p.transfers += 1
        p.add(res, -n)
        q.add(res, n)
        self.say(f'    P{p.idx} transfere {n} {res} para P{q.idx}')

    # -- fluxo
    def pool_resources(self):
        w = self.week()
        cfg = self.cfg
        groups = collections.defaultdict(list)
        for p in self.players:
            if p.alive:
                groups[p.pos].append(p)
        for members in groups.values():
            if len(members) < 2:
                continue
            for res, req in (('food', cfg.week_food[w]), ('water', cfg.week_water[w])):
                short = sorted((q for q in members if q.get(res) < req), key=lambda q: req - q.get(res))
                for q in short:
                    need = req - q.get(res)
                    donors = sorted((d for d in members if d.get(res) > req), key=lambda d: -d.get(res))
                    avail = sum(d.get(res) - req for d in donors)
                    if avail < need:
                        break
                    for d in donors:
                        give = min(need, d.get(res) - req)
                        d.add(res, -give)
                        q.add(res, give)
                        need -= give
                        if need == 0:
                            break

    def weekly_check(self):
        w = self.week()
        cfg = self.cfg
        if cfg.mode == 'coop' and cfg.pool_at_check:
            self.pool_resources()
        for p in self.players:
            if not p.alive:
                continue
            paid = 0
            for res, req, item in (('food', cfg.week_food[w], 'panela'),
                                   ('water', cfg.week_water[w], 'cantil')):
                have = p.get(res)
                if have >= req:
                    p.add(res, -req)
                    paid += 1
                elif have == req - 1 and item in p.items:
                    p.items.remove(item)
                    p.add(res, -have)
                    paid += 1
                else:
                    self.gain_exh(p, 'prova_' + res)
            if paid == 2:
                p.weeks_paid += 1
            if cfg.spoil and w < 2:
                p.food = 0
            p.ability_used = False
            p.rest_used = False
            p.cared = False
        self.say(f'  == Prova semana {w + 1}: ' + ', '.join(
            f'P{p.idx} exh={p.exh} abr={p.shelter}{"" if p.alive else " X"}' for p in self.players))

    def turn_order(self, first):
        cfg = self.cfg
        base = [self.players[(first + k) % self.n] for k in range(self.n)]
        if cfg.order == 'snake':
            # 1-2-3-4 / 4-3-2-1 ... e o primeiro avança a cada par de rodadas
            b = [self.players[((self.round - 1) // 2 + k) % self.n] for k in range(self.n)]
            return b if self.round % 2 == 1 else b[::-1]
        if cfg.order == 'random':
            b = base[:]
            self.rng.shuffle(b)
            return b
        if cfg.order == 'r1_reverse' and self.round == 1:
            return base[::-1]
        if cfg.order == 'catchup':
            # quem está pior (mais Exaustão, menos semanas pagas) joga antes
            return sorted(base, key=lambda p: (-p.exh, p.weeks_paid))
        return base

    def restock_tiles(self):
        full = self.cfg.res()
        for t in self.tiles.values():
            if t.revealed and full.get(t.kind, {}).get('food'):
                t.tokens['food'] = min(full[t.kind]['food'], t.tokens['food'] + self.cfg.restock)

    def play(self):
        cfg = self.cfg
        first = 0
        for self.round in range(1, cfg.rounds + 1):
            self.claims = {}
            if cfg.restock and self.round in (4, 7):
                self.restock_tiles()
            self.say(f'-- Rodada {self.round}')
            for p in self.turn_order(first):
                if p.alive:
                    take_turn(self, p)
            if self.round % 3 == 0:
                self.weekly_check()
            first = (first + 1) % self.n
        return self.result()

    def completed(self, p):
        if not p.alive or p.shelter < 3:
            return False
        t = self.tiles[p.pos]
        return t.kind == 'Re' and t.revealed

    def score(self, p):
        c = self.cfg
        s = (c.week_points * p.weeks_paid + min(p.food, c.caps[0]) + min(p.water, c.caps[1])
             + min(p.wood, c.caps[2]) + len(p.items) - c.exh_penalty * p.exh)
        return max(0, s)

    def result(self):
        out = []
        for p in self.players:
            done = self.completed(p)
            if done:
                reason = 'ok'
            elif not p.alive:
                reason = 'eliminado'
            elif p.shelter < 3:
                reason = 'abrigo'
            else:
                reason = 'fora_do_resgate'
            out.append(dict(idx=p.idx, arch=p.arch, done=done, reason=reason,
                            ps=self.score(p) if done else None, exh=p.exh,
                            weeks=p.weeks_paid, exh_src=dict(p.exh_src),
                            pe_unused=p.pe_unused, reveals=p.reveals, collects=p.collects,
                            items=len(p.items), died=p.died_round,
                            left=p.food + p.water + p.wood,
                            good_ev=p.good_ev, bad_ev=p.bad_ev, transfers=p.transfers,
                            shared=p.group is not None and len(p.group) > 1))
        return out


# ------------------------------------------------------------------- IA

def aiget(g, p, key, default):
    if key in p.ai:
        return p.ai[key]
    return g.cfg.ai.get(key, default)


def cur_food_req(g):
    return g.cfg.week_food[g.week()]


def food_value(g, p, extra=0):
    have = p.food + extra
    req = cur_food_req(g)
    if have < req:
        return 10.0
    if g.week() == 2 and have < req + g.cfg.caps[0]:
        return 2.0
    return 0.0


def water_value(g, p, extra=0):
    w = g.week()
    have = p.water + extra
    cur = g.cfg.week_water[w]
    total = sum(g.cfg.week_water[w:])
    if have < cur:
        return 10.0
    if have < total:
        return 6.0
    if have < total + g.cfg.caps[1]:
        return 1.5
    return 0.0


def wood_value(g, p, extra=0):
    need = g.cfg.shelter_levels - p.shelter - (p.wood + extra)
    if need > 0:
        return 8.0 + 1.5 * g.week()
    if p.wood + extra < (g.cfg.shelter_levels - p.shelter) + g.cfg.caps[2]:
        return 1.5
    return 0.0


VALUE_FN = {'food': food_value, 'water': water_value, 'wood': wood_value}


def team_bonus(g, p, res):
    """No cooperativo, recurso sobrando ainda vale para quem precisa."""
    if g.cfg.mode != 'coop':
        return 0.0
    best = 0.0
    for q in g.players:
        if q is p or not q.alive:
            continue
        v = VALUE_FN[res](g, q)
        if v >= 6:
            best = max(best, 3.5)
    return best


def res_value(g, p, res, extra=0):
    v = VALUE_FN[res](g, p, extra)
    if v < 3:
        v = max(v, team_bonus(g, p, res))
    return v


def item_value(g, p, it):
    return {'toldo': 2.0, 'panela': 1.6, 'cantil': 1.6, 'faca': 1.3, 'rede': 1.3}[it]


def exh_cost(p, cfg):
    if p.exh + 1 >= cfg.exh_limit:
        return 40.0
    return 5.0 + 3.0 * p.exh


def risk_penalty(g, p):
    if g.cfg.hunter_safe and p.arch == 'Cacador':
        return 0.0
    if g.cfg.hunter_fail_faces and p.arch == 'Cacador':
        return g.cfg.hunter_fail_faces / 6 * exh_cost(p, g.cfg) * aiget(g, p, 'risk_aversion', 1.0)
    if p.arch == 'Sobrevivencialista' and not p.ability_used:
        return 0.0
    if 'toldo' in p.items:
        return 0.8
    return 0.5 * exh_cost(p, g.cfg) * aiget(g, p, 'risk_aversion', 1.0)


def tile_collect_value(g, p, pos):
    """Melhor valor de coleta num tile revelado. Retorna (valor, recurso)."""
    t = g.tiles[pos]
    best = (0.0, None)
    for res in RES:
        if t.tokens[res] <= 0:
            continue
        v = res_value(g, p, res)
        if v <= 0:
            continue
        if g.bonus_applies(p, t.kind, res):
            v += res_value(g, p, res, extra=1) * 0.9
        if res == 'food' and ((t.kind in ('P', 'Ac') and 'faca' in p.items)
                              or (t.kind == 'R' and 'rede' in p.items)):
            v += 0.5 * res_value(g, p, res, extra=1)
        if t.risk:
            v -= risk_penalty(g, p)
        if v > best[0]:
            best = (v, res)
    return best


def event_ev(g, p):
    deck = collections.Counter(g.deck) if g.deck else collections.Counter(EVENTS)
    tot = sum(deck.values()) or 1
    v = 0.0
    for ev, c in deck.items():
        pr = c / tot
        if ev == 'comida':
            v += pr * res_value(g, p, 'food')
        elif ev == 'agua':
            v += pr * res_value(g, p, 'water')
        elif ev == 'madeira':
            v += pr * res_value(g, p, 'wood')
        elif ev in ITEMS:
            v += pr * 1.5
        elif ev == 'pista':
            v += pr * 0.3
        elif ev == 'atraso':
            v -= pr * 0.8
        elif ev == 'cansaco':
            v -= pr * exh_cost(p, g.cfg)
        elif ev == 'vazamento':
            v -= pr * (res_value(g, p, 'water', -1) if p.water else exh_cost(p, g.cfg))
    return v


def kind_values(g, p):
    """Valor de revelar cada tipo de tile (sem o bônus de achar o Resgate)."""
    ev = event_ev(g, p)
    res = g.cfg.res()
    rp = risk_penalty(g, p)
    rv = {r: res_value(g, p, r) for r in RES}
    out = {}
    for k in set(TILE_RES) | set(res):
        tv = 0.0
        for r, n in res.get(k, {}).items():
            if n > 0:
                tv = max(tv, rv[r] * min(n, 2) * 0.45)
        if k in RISK_TILES:
            tv -= 0.3 * rp
        if k not in ('Re', 'I'):
            tv += ev
        out[k] = tv
    return out


def explore_value(g, p, pos, unrevealed_pool, kv, has_rescue):
    kind = p.known.get(pos)
    rescue_bonus = 0.0
    if not has_rescue:
        rescue_bonus = 2.0 + 1.5 * g.round
        if pos in g.near12:
            rescue_bonus *= 1.5
    if kind:
        dist = {kind: 1.0}
    else:
        tot = sum(unrevealed_pool.values()) or 1
        dist = {k: c / tot for k, c in unrevealed_pool.items()}
    v = 0.0
    for k, pr in dist.items():
        v += pr * (kv[k] + (rescue_bonus if k == 'Re' else 0.0))
    return v * aiget(g, p, 'explore_weight', 1.0)


def nearest_wood(g, pos):
    best = None
    dm = g.dist_map(pos)
    for q, t in g.tiles.items():
        if t.revealed and t.tokens['wood'] > 0:
            if best is None or dm[q] < dm[best]:
                best = q
    return best


def required_end_cost(g, p, pos):
    """PE mínima para, a partir de pos, buscar a madeira que falta, terminar o
    abrigo e chegar ao Resgate."""
    res = g.known_rescues()
    L = g.cfg.shelter_levels
    if res:
        def dres(x):
            return min(g.dist(x, r) for r in res)
    else:
        def dres(x):
            hidden = [q for q in g.near12 if not g.tiles[q].revealed]
            return min((g.dist(x, q) for q in hidden), default=2)
    if p.shelter >= L:
        return dres(pos)
    builds = L - p.shelter
    missing = builds - p.wood
    via = pos
    fetch = 0
    if missing > 0:
        w = nearest_wood(g, pos)
        if w is not None:
            fetch = g.dist(pos, w) + missing
            via = w
    if p.shelter == 0:
        extra = 1 if g.tiles[via].kind == 'Re' and g.tiles[via].revealed else 0
        return fetch + builds + extra + dres(via)
    return fetch + g.dist(via, p.shelter_pos) + builds + dres(p.shelter_pos)


def pe_per_turn(g, p):
    return g.cfg.pe - (1 if g.cfg.exh_pe and p.exh >= g.cfg.exh_pe else 0)


def future_budget(g, p):
    return pe_per_turn(g, p) * (g.cfg.rounds - g.round)


def plan_step(g, p):
    """Passo obrigatório quando o fim de jogo aperta."""
    L = g.cfg.shelter_levels
    if p.shelter + p.wood < L:
        here = g.tiles[p.pos]
        if here.tokens['wood'] > 0 and g.can_collect(p, p.pos):
            return ('collect', 'wood')
        w = nearest_wood(g, p.pos)
        if w is not None and w != p.pos:
            return ('goto', w)
    if p.shelter < L and p.wood > 0:
        if p.shelter == 0 and not (g.tiles[p.pos].kind == 'Re'):
            return ('build',)
        if p.shelter > 0 and p.pos == p.shelter_pos:
            return ('build',)
    if p.shelter < L and p.shelter > 0 and p.wood >= L - p.shelter:
        return ('goto', p.shelter_pos)
    res = g.known_rescues()
    if res:
        tgt = min(res, key=lambda r: g.dist(p.pos, r))
        if p.pos != tgt:
            return ('goto', tgt)
        return None
    hidden = [q for q in g.near12 if not g.tiles[q].revealed]
    if hidden:
        return ('goto', min(hidden, key=lambda q: g.dist(p.pos, q)))
    return None


def step_toward(g, p, tgt):
    dm = g.dist_map(tgt)
    return min(g.adj[p.pos], key=lambda q: (dm[q], g.tiles[q].revealed))


def candidate_actions(g, p):
    cfg = g.cfg
    L = cfg.shelter_levels
    cands = []  # (ratio, action, target_for_claim)
    here = g.tiles[p.pos]
    # coletar aqui
    if g.can_collect(p, p.pos):
        v, r = tile_collect_value(g, p, p.pos)
        if r:
            cands.append((v, ('collect', r), None))
    # construir
    if p.wood > 0 and p.shelter < L:
        site_ok = False
        if p.shelter == 0:
            site_ok = (here.kind != 'Re' and
                       g.dist(p.pos, g.start) <= aiget(g, p, 'build_radius', 2))
            if g.known_rescues():
                site_ok = here.kind != 'Re' and min(
                    g.dist(p.pos, r) for r in g.known_rescues()) <= aiget(g, p, 'build_radius', 2)
        else:
            site_ok = p.pos == p.shelter_pos
        if site_ok:
            cands.append((9.0, ('build',), None))
    # descansar
    if p.exh > 0 and not p.rest_used and p.food > 0:
        at = p.shelter > 0 and p.shelter_pos == p.pos
        cost = 1 if at else cfg.rest_cost
        if cost <= p.pe:
            spare = p.food > cur_food_req(g)
            gain = exh_cost(p, cfg) * (2 if at and p.shelter >= 2 and p.exh >= 2 else 1) * 0.6
            food_loss = 0 if spare else food_value(g, p, extra=-1)
            val = gain - food_loss * 0.5
            if val > 0:
                cands.append((val / cost, ('rest',), None))
    # transferir (coop)
    if cfg.mode == 'coop' and cfg.coop_shelter_cap and p.shelter == 0:
        for q in g.players:
            if (q is p or q.shelter == 0 or q.group is None
                    or len(q.group) >= cfg.coop_shelter_cap):
                continue
            d = g.dist(p.pos, q.shelter_pos)
            if d == 0:
                cands.append((12.0, ('join', q), None))
            else:
                cands.append((10.0 / (d + 1), ('goto', q.shelter_pos), None))
    if cfg.mode == 'coop' and cfg.care and p.food > 0:
        spare = p.food > cur_food_req(g)
        for q in g.players:
            if q is p or not q.alive or q.exh == 0 or q.cared:
                continue
            gain = exh_cost(q, cfg) * 0.6
            val = gain - (0 if spare else food_value(g, p, extra=-1) * 0.5)
            if val <= 0:
                continue
            d = g.dist(p.pos, q.pos)
            if d == 0:
                cands.append((val, ('care', q), None))
            elif q.exh >= 2:
                cands.append((val / (d + 1), ('goto', q.pos), None))
    if cfg.mode == 'coop' and p.pe >= cfg.transfer_pe:
        for q in g.players:
            if q is p or not q.alive or g.dist(q.pos, p.pos) > cfg.transfer_range:
                continue
            for res in RES:
                need_q = team_need(g, q, res)
                sur = team_surplus(g, p, res)
                n = min(2, need_q, sur)
                if n > 0:
                    cands.append((9.5 * n, ('transfer', q, res, n), None))
    # alvos remotos
    pool = collections.Counter(t.kind for t in g.tiles.values() if not t.revealed)
    dm = g.dist_map(p.pos)
    kv = kind_values(g, p)
    has_rescue = bool(g.known_rescues())
    for pos, t in g.tiles.items():
        d = dm[pos]
        if d == 0:
            continue
        if cfg.mode == 'coop' and g.claims.get(pos, p.idx) != p.idx:
            continue
        if not t.revealed:
            v = explore_value(g, p, pos, pool, kv, has_rescue)
            cost = d
            if v > 0:
                cands.append((v / cost, ('goto', pos), pos))
            continue
        v, r = tile_collect_value(g, p, pos)
        if r:
            # coleta no mesmo turno só se o tile ainda não foi usado nesta rodada
            if not g.can_collect(p, pos) or d + 1 > p.pe:
                v *= 0.75
            cands.append((v / (d + 1), ('goto', pos), pos))
    # ir ao próprio abrigo para subir de nível
    if p.shelter > 0 and p.shelter < L and p.wood > 0 and p.pos != p.shelter_pos:
        d = dm[p.shelter_pos]
        cands.append((9.0 / (d + 1), ('goto', p.shelter_pos), None))
    # levar recursos a um aliado (coop)
    if cfg.mode == 'coop':
        for q in g.players:
            if q is p or not q.alive or g.dist(q.pos, p.pos) <= cfg.transfer_range:
                continue
            for res in RES:
                n = min(2, team_need(g, q, res), team_surplus(g, p, res))
                if n > 0:
                    d = dm[q.pos]
                    cands.append((9.0 * n / (d + 1), ('goto', q.pos), None))
    return cands


def team_need(g, q, res):
    w = g.week()
    urgent = g.round % 3 == 0 or aiget(g, q, 'coop_eager', True)
    if res == 'food':
        return max(0, g.cfg.week_food[w] - q.food) if urgent else 0
    if res == 'water':
        return max(0, g.cfg.week_water[w] - q.water) if urgent else 0
    return max(0, g.cfg.shelter_levels - q.shelter - q.wood) if g.round >= 5 else 0


def team_surplus(g, p, res):
    w = g.week()
    if res == 'food':
        return max(0, p.food - g.cfg.week_food[w])
    if res == 'water':
        return max(0, p.water - sum(g.cfg.week_water[w:]))
    return max(0, p.wood - (g.cfg.shelter_levels - p.shelter))


def apply_action(g, p, act):
    kind = act[0]
    if kind == 'collect':
        g.collect(p, act[1])
    elif kind == 'build':
        g.build(p)
    elif kind == 'rest':
        g.rest(p)
    elif kind == 'care':
        g.care(p, act[1])
    elif kind == 'join':
        g.join(p, act[1])
    elif kind == 'transfer':
        g.transfer(p, *act[1:])
    elif kind == 'goto':
        g.move(p, step_toward(g, p, act[1]))


def sim_after(g, p, act):
    """Posição e PE depois da ação (para checar a restrição de fim de jogo)."""
    kind = act[0]
    if kind == 'goto':
        return step_toward(g, p, act[1]), p.pe - 1, p.shelter, p.shelter_pos
    if kind == 'rest':
        at = p.shelter > 0 and p.shelter_pos == p.pos
        return p.pos, p.pe - (1 if at else g.cfg.rest_cost), p.shelter, p.shelter_pos
    if kind == 'build':
        return p.pos, p.pe - 1, p.shelter + 1, p.shelter_pos or p.pos
    if kind == 'join':
        return p.pos, p.pe - 1, act[1].shelter, act[1].shelter_pos
    if kind == 'transfer':
        return p.pos, p.pe - g.cfg.transfer_pe, p.shelter, p.shelter_pos
    return p.pos, p.pe - 1, p.shelter, p.shelter_pos


def feasible(g, p, act):
    pos, pe_after, sh, shpos = sim_after(g, p, act)
    fake = copy.copy(p)
    fake.shelter, fake.shelter_pos = sh, shpos
    margin = aiget(g, p, 'end_margin', 0)
    return required_end_cost(g, fake, pos) + margin <= pe_after + future_budget(g, p)


def take_turn(g, p):
    p.pe = pe_per_turn(g, p)
    guard = 0
    while p.pe > 0 and p.alive and guard < 20:
        guard += 1
        cands = candidate_actions(g, p)
        cands.sort(key=lambda c: -c[0])
        chosen = None
        for ratio, act, claim in cands:
            if ratio < aiget(g, p, 'min_ratio', 0.25):
                break
            if feasible(g, p, act):
                chosen = (act, claim)
                break
        if chosen is None:
            need = required_end_cost(g, p, p.pos)
            if need > future_budget(g, p) - aiget(g, p, 'end_margin', 0) or g.round == g.cfg.rounds:
                act = plan_step(g, p)
                if act is None:
                    break
                chosen = (act, None)
            else:
                break
        act, claim = chosen
        if claim is not None:
            g.claims[claim] = p.idx
        apply_action(g, p, act)
    p.pe_unused += max(0, p.pe)


# ------------------------------------------------------------ relatório

def run(n, cfg, games, seed=1):
    rng = random.Random(seed)
    rows = []
    for gi in range(games):
        g = Game(n, cfg, random.Random(rng.random()))
        res = g.play()
        left = {k: sum(t.tokens[k] for t in g.tiles.values() if t.revealed)
                + sum(g.cfg.res().get(t.kind, {}).get(k, 0) for t in g.tiles.values() if not t.revealed)
                for k in RES}
        for seat, r in enumerate(res):
            r['seat'] = seat
            r['game'] = gi
            r['map_left'] = left
        rows.append(res)
    return rows


def summarize(rows, cfg):
    n = len(rows[0])
    P = [r for g in rows for r in g]
    done = [r for r in P if r['done']]
    s = {}
    s['conclusao_individual'] = len(done) / len(P)
    s['todos_concluem'] = sum(all(r['done'] for r in g) for g in rows) / len(rows)
    s['ninguem_conclui'] = sum(not any(r['done'] for r in g) for g in rows) / len(rows)
    s['motivos'] = collections.Counter(r['reason'] for r in P)
    s['eliminados'] = sum(r['reason'] == 'eliminado' for r in P) / len(P)
    s['ps_medio'] = statistics.mean(r['ps'] for r in done) if done else 0
    s['ps_dp'] = statistics.pstdev([r['ps'] for r in done]) if done else 0
    s['exh_media'] = statistics.mean(r['exh'] for r in P)
    src = collections.Counter()
    for r in P:
        src.update(r['exh_src'])
    s['exh_fontes'] = {k: v / len(P) for k, v in src.most_common()}
    s['pe_ociosa_por_jogador'] = statistics.mean(r['pe_unused'] for r in P)
    s['semanas_pagas'] = statistics.mean(r['weeks'] for r in P)
    s['sobra_no_mapa'] = {k: statistics.mean(g[0]['map_left'][k] for g in rows) for k in RES}
    s['mapa_sem_madeira'] = sum(g[0]['map_left']['wood'] == 0 for g in rows) / len(rows)
    # vitórias
    wins_arch, wins_seat = collections.Counter(), collections.Counter()
    games_arch = collections.Counter()
    ties = margins = 0
    margin_list = []
    for g in rows:
        for r in g:
            games_arch[r['arch']] += 1
        fin = [r for r in g if r['done']]
        if not fin:
            continue
        best = max(r['ps'] for r in fin)
        top = [r for r in fin if r['ps'] == best]
        if len(top) > 1:
            ties += 1
        for r in top:
            wins_arch[r['arch']] += 1 / len(top)
            wins_seat[r['seat']] += 1 / len(top)
        others = sorted((r['ps'] for r in fin), reverse=True)
        if len(others) > 1:
            margin_list.append(others[0] - others[1])
    s['empates_no_topo'] = ties / len(rows)
    s['margem_vitoria_media'] = statistics.mean(margin_list) if margin_list else 0
    s['vit_arquetipo'] = {a: wins_arch[a] / games_arch[a] for a in ARCHETYPES if games_arch[a]}
    s['conc_arquetipo'] = {a: sum(r['done'] for r in P if r['arch'] == a) /
                           max(1, sum(1 for r in P if r['arch'] == a)) for a in ARCHETYPES}
    s['vit_assento'] = {k: wins_seat[k] / len(rows) for k in range(n)}
    s['conc_assento'] = {k: sum(r['done'] for r in P if r['seat'] == k) / len(rows) for k in range(n)}
    return s


def fmt(s):
    lines = []
    for k, v in s.items():
        if isinstance(v, float):
            lines.append(f'  {k:28s} {v:.3f}')
        elif isinstance(v, dict) or isinstance(v, collections.Counter):
            inner = ', '.join(f'{a}={b:.3f}' if isinstance(b, float) else f'{a}={b}' for a, b in v.items())
            lines.append(f'  {k:28s} {inner}')
        else:
            lines.append(f'  {k:28s} {v}')
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--games', type=int, default=2000)
    ap.add_argument('--trace', type=int, default=0)
    ap.add_argument('--seed', type=int, default=7)
    ap.add_argument('--mode', default='comp')
    ap.add_argument('--pe', type=int, default=4)
    ap.add_argument('--v06', action='store_true', help='usa a proposta de regras v0.6')
    a = ap.parse_args()
    cfg = Config(pe=a.pe, mode=a.mode)
    if a.v06:
        from experimentos import V06, COOP06
        extra = COOP06 if a.mode == 'coop' else {}
        cfg = Config(pe=a.pe, mode=a.mode, **V06, **extra)
    if a.trace:
        g = Game(a.trace, cfg, random.Random(a.seed), trace=True)
        for r in range(g.rows):
            print(' ' * (2 * (r % 2)) + ' '.join(f'{g.tiles[(c, r)].kind:>3}' for c in range(g.cols)))
        print('arquétipos:', [p.arch for p in g.players])
        res = g.play()
        for r in res:
            print(r)
        return
    for n in (2, 3, 4):
        rows = run(n, cfg, a.games, a.seed)
        print(f'\n=== {n} jogadores | modo {cfg.mode} | PE {cfg.pe} ===')
        print(fmt(summarize(rows, cfg)))


if __name__ == '__main__':
    main()
