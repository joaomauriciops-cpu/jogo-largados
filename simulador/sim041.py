"""Simulador de Largados e Pelados — manual 0.4.1 (protótipo de setembro de 2026).

Diferenças principais para o 0.4: Mover e Explorar separados, 8 Eventos coletivos
(1 por rodada, 2–9), 1 Item inicial por pessoa, fogo e teste de água sem fogo,
7 arquétipos (Explorador e Guardião do Fogo) e Desgaste no lugar de Exaustão.

    python3 sim041.py                 # métricas para 2, 3 e 4 pessoas
    python3 sim041.py --trace 4       # log de uma partida
"""
from __future__ import annotations

import argparse
import collections
import copy
import heapq
import random
import statistics
from dataclasses import dataclass, field

TILE_RES = {
    'F': {'wood': 2}, 'Ca': {'water': 3}, 'Cl': {'food': 2, 'wood': 1},
    'P': {'food': 2, 'water': 1}, 'R': {'food': 1, 'water': 1}, 'Ac': {'food': 3},
    'Re': {}, 'I': {}, 'Pa': {},
}
RISK_TILES = {'P', 'Ac'}
TILE_COUNTS = {
    2: {'F': 3, 'Ca': 2, 'Cl': 3, 'P': 2, 'R': 4, 'Ac': 2, 'Re': 2, 'I': 1, 'Pa': 1},
    3: {'F': 4, 'Ca': 3, 'Cl': 4, 'P': 3, 'R': 4, 'Ac': 3, 'Re': 2, 'I': 1, 'Pa': 1},
    4: {'F': 4, 'Ca': 4, 'Cl': 5, 'P': 3, 'R': 5, 'Ac': 4, 'Re': 3, 'I': 1, 'Pa': 1},
}
GRID = {2: (4, 5), 3: (5, 5), 4: (5, 6)}
ARCHETYPES = ['Cacador', 'Coletor', 'Pescador', 'Construtor', 'Sobrevivencialista',
              'Explorador', 'Guardiao']
ITEMS = ['faca', 'panela', 'cantil', 'rede', 'toldo']
EVENTS = list(range(1, 19))
EVENT_NAMES = {
    1: 'O olho do jacaré', 2: 'Desmaio sobre a fogueira', 3: 'Furacão', 4: 'Hienas no estoque',
    5: 'Picada na virilha', 6: 'Hipotermia', 7: 'Abrigo inundado', 8: 'Bananeira!',
    9: 'Poço de bagres', 10: 'Abrigo em chamas', 11: 'Cabeça podre de passarinho',
    12: 'A planta errada', 13: 'Canoa pelo pântano', 14: 'Em busca de água',
    15: 'Rumo à extração', 16: 'Tartaruga na armadilha', 17: 'Um jantar revigorante',
    18: 'Abrigo em cúpula',
}
RES = ('food', 'water', 'wood')
EVENTS_LEVES = {8, 9, 13, 14, 15, 16, 17, 18}          # ajudam ou dão opção sem risco
EVENTS_MISTOS = {1, 3, 7, 11, 12}                     # troca de risco por recurso / atrito leve
EVENTS_DUROS = {2, 4, 5, 6, 10}                       # custam PE, comida ou Desgaste


@dataclass
class Config:
    pe: int = 4
    rounds: int = 9
    week_food: tuple = (2, 3, 3)
    week_water: tuple = (1, 1, 2)
    shelter_levels: int = 3
    mode: str = 'comp'
    spoil: bool = False               # pedido do autor: comida não estraga
    food_cap: int = 99                # limite de comida carregada
    exh_limit: int = 3
    exh_pe: int = 1                   # com Desgaste >= exh_pe, 1 PE a menos (0 = desligado)
    rest_cost: int = 2
    transfer_pe: int = 1
    trail: bool = False               # 1 PE move até 2 tiles já explorados seguidos
    fire_cost: int = 1
    explore_cost: int = 1
    water_fire_test: bool = True      # teste de água sem fogo na Prova
    risk_fail: int = 3                # faces (de 6) que dão Desgaste no risco
    tile_counts: dict = None
    tile_res: dict = None
    events: tuple = None              # None -> as 18 cartas
    events_per_game: int = 8
    escalate: bool = False            # Eventos em 3 fases: leves (rod. 2-3), mistos (4-6), duros (7-9)
    escalate_harsh: int = 3           # quantos Eventos duros entram na semana 3
    caps: tuple = (3, 2, 2)
    ai: dict = field(default_factory=dict)

    def counts(self, n):
        return (self.tile_counts or TILE_COUNTS)[n]

    def res(self):
        return self.tile_res or TILE_RES


# ------------------------------------------------------------- hexágonos

def neighbors(c, r, cols, rows):
    if r % 2 == 0:
        d = [(-1, -1), (0, -1), (-1, 0), (1, 0), (-1, 1), (0, 1)]
    else:
        d = [(0, -1), (1, -1), (-1, 0), (1, 0), (0, 1), (1, 1)]
    return [(c + dc, r + dr) for dc, dr in d if 0 <= c + dc < cols and 0 <= r + dr < rows]


def to_cube(c, r):
    x = c - (r - (r & 1)) // 2
    return x, -x - r, r


def hexdist(a, b):
    ax, ay, az = to_cube(*a)
    bx, by, bz = to_cube(*b)
    return max(abs(ax - bx), abs(ay - by), abs(az - bz))


@dataclass
class Tile:
    kind: str
    revealed: bool = False
    tokens: dict = field(default_factory=lambda: {'food': 0, 'water': 0, 'wood': 0})
    risk: bool = False
    collected_round: int = 0


@dataclass
class Player:
    idx: int
    arch: str
    pos: tuple
    item: str = None
    food: int = 0
    water: int = 0
    wood: int = 0
    exh: int = 0
    shelter: int = 0
    shelter_pos: tuple = None
    fire: bool = False
    alive: bool = True
    ability_used: bool = False
    rest_used: bool = False
    weeks_paid: int = 0
    pe: int = 0
    # por rodada (Eventos)
    target: tuple = None
    move_credit: bool = False
    ev_used: bool = False
    turn_start_at_shelter: bool = False
    moved_this_round: bool = False
    free_build: bool = False
    turtle: bool = False
    # estatísticas
    exh_src: collections.Counter = field(default_factory=collections.Counter)
    died_round: int = 0
    ai: dict = field(default_factory=dict)

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
        center = ((self.cols - 1) / 2, (self.rows - 1) / 2)
        full = [p for p in self.cells if len(self.adj[p]) == 6]
        self.start = min(full, key=lambda p: (p[0] - center[0]) ** 2 + (p[1] - center[1]) ** 2)
        self.version = 0
        self._dcache = {}
        self.build_map()
        deck = list(EVENTS if cfg.events is None else cfg.events)
        rng.shuffle(deck)
        if cfg.escalate:
            leves = [e for e in deck if e in EVENTS_LEVES]
            mistos = [e for e in deck if e in EVENTS_MISTOS]
            duros = [e for e in deck if e in EVENTS_DUROS]
            h = cfg.escalate_harsh
            deck = duros[:h] + mistos[:6 - h] + leves[:2]   # pop() tira do fim
        self.event_deck = deck
        self.event = None
        archs = rng.sample(ARCHETYPES, n)
        items = rng.sample(ITEMS, n)
        self.players = [Player(i, archs[i], self.start, item=items[i]) for i in range(n)]
        self.round = 0
        self.claims = {}
        self.lost = False
        self.stats = collections.Counter()

    def say(self, *a):
        if self.trace:
            print(*a)

    # -- montagem conforme o manual 0.4.1
    def build_map(self):
        pool = [k for k, v in self.cfg.counts(self.n).items() for _ in range(v) if k != 'I']
        pool.remove('F')
        pool.remove('R')
        pool.remove('Re')
        self.rng.shuffle(pool)
        ring1 = list(self.adj[self.start])
        ring2 = sorted({q for p in ring1 for q in self.adj[p]} - set(ring1) - {self.start})
        self.rng.shuffle(ring2)
        first = ['F', 'R'] + [pool.pop() for _ in range(4)]
        self.rng.shuffle(first)
        second = ['Re'] + [pool.pop() for _ in range(5)]
        self.rng.shuffle(second)
        layout = dict(zip(ring1, first))
        near = ring2[:6]
        layout.update(zip(near, second))
        rest = [p for p in self.cells if p not in layout and p != self.start]
        layout.update(zip(rest, pool))
        self.near_rescue = set(near)
        self.tiles = {self.start: Tile('I', revealed=True)}
        for p, k in layout.items():
            self.tiles[p] = Tile(k)

    # -- caminhos: entrar em tile oculto custa Mover + Explorar
    def dist_map(self, src, strict=False):
        key = (src, self.version, strict)
        if key in self._dcache:
            return self._dcache[key]
        d = {src: 0}
        h = [(0, src)]
        while h:
            du, u = heapq.heappop(h)
            if du > d[u]:
                continue
            for v in self.adj[u]:
                w = (0.5 if self.cfg.trail and not strict else 1) if self.tiles[v].revealed else 1 + self.cfg.explore_cost
                if du + w < d.get(v, 1e9):
                    d[v] = du + w
                    heapq.heappush(h, (du + w, v))
        self._dcache[key] = d
        return d

    def dist(self, a, b, strict=False):
        return self.dist_map(a, strict)[b]

    def week(self):
        return (self.round - 1) // 3

    def known_rescues(self):
        return [p for p, t in self.tiles.items() if t.revealed and t.kind == 'Re']

    # -- efeitos
    def gain_exh(self, p, src, n=1):
        for _ in range(n):
            if (p.arch == 'Sobrevivencialista' and not p.ability_used
                    and src in ('risco', 'agua_sem_fogo')):
                p.ability_used = True
                self.say(f'    P{p.idx} Sobrevivencialista ignora Desgaste ({src})')
                continue
            p.exh += 1
            p.exh_src[src] += 1
            if p.exh >= self.cfg.exh_limit and p.alive:
                p.alive = False
                p.died_round = self.round
                self.say(f'    !! P{p.idx} ({p.arch}) eliminado ({src})')
                if self.cfg.mode == 'coop':
                    self.lost = True
                return

    def gain(self, p, res, n):
        p.add(res, n)
        if res == 'food' and p.food > self.cfg.food_cap:
            p.food = self.cfg.food_cap

    def d6(self):
        return self.rng.randint(1, 6)

    # -- ações
    def move_cost(self, p, use=False, dest=None):
        if (self.cfg.trail and p.move_credit and dest is not None and self.tiles[dest].revealed
                and self.tiles[p.pos].revealed):
            if use:
                p.move_credit = False
            return 0
        c = 1
        if not p.moved_this_round:
            if self.event == 3:
                c = 1 if p.turn_start_at_shelter else 2
            elif self.event == 13:
                c = 0
        if c > 0 and p.arch == 'Explorador' and not p.ability_used:
            if use:
                p.ability_used = True
            c = 0
        return c

    def move(self, p, dest):
        credit_before = p.move_credit
        c = self.move_cost(p, use=True, dest=dest)
        if self.cfg.trail and c == 1 and self.tiles[dest].revealed:
            p.move_credit = True
        elif not (credit_before and c == 0):
            p.move_credit = False
        p.pe -= c
        p.moved_this_round = True
        p.pos = dest
        self.say(f'    P{p.idx} move {dest}{"" if self.tiles[dest].revealed else " (oculto)"} [{c} PE]')

    def explore(self, p):
        p.pe -= self.cfg.explore_cost
        t = self.tiles[p.pos]
        t.revealed = True
        self.version += 1
        for k, v in self.cfg.res().get(t.kind, {}).items():
            t.tokens[k] = v
        t.risk = t.kind in RISK_TILES
        self.say(f'    P{p.idx} explora {t.kind}{p.pos}')

    def bonus_applies(self, p, kind, res):
        if p.ability_used:
            return False
        a = p.arch
        return ((a == 'Cacador' and res == 'food' and kind in ('P', 'Ac'))
                or (a == 'Coletor' and res == 'food' and kind == 'Cl')
                or (a == 'Pescador' and res == 'food' and kind == 'R')
                or (a == 'Construtor' and res == 'wood' and kind in ('F', 'Cl')))

    def collect(self, p, res):
        t = self.tiles[p.pos]
        p.pe -= 1
        t.tokens[res] -= 1
        t.collected_round = self.round
        self.gain(p, res, 1)
        extra = ''
        if self.bonus_applies(p, t.kind, res):
            p.ability_used = True
            self.gain(p, res, 1)
            extra += ' +habilidade'
        if res == 'food':
            it = 'faca' if t.kind in ('P', 'Ac') else 'rede' if t.kind == 'R' else None
            if it and p.item == it and food_value(self, p) > 2:
                p.item = None
                self.gain(p, 'food', 1)
                extra += f' +{it}'
            if self.event == 16 and not p.turtle:
                p.turtle = True
                self.gain(p, 'food', 1)
                extra += ' +tartaruga'
        if t.risk:
            t.risk = False
            roll = self.d6()
            bad = roll % 2 == 1 if self.cfg.risk_fail == 3 else roll <= self.cfg.risk_fail
            if bad:
                if p.item == 'toldo':
                    p.item = None
                    extra += f' dado {roll} (toldo)'
                else:
                    extra += f' dado {roll} DESGASTE'
                    self.gain_exh(p, 'risco')
            else:
                extra += f' dado {roll} ok'
        self.say(f'    P{p.idx} coleta {res} em {t.kind}{p.pos}{extra}')

    def build(self, p):
        if self.event == 18 and not p.free_build:
            p.free_build = True
        else:
            p.pe -= 1
        p.wood -= 1
        if p.shelter == 0:
            p.shelter_pos = p.pos
        p.shelter += 1
        p.fire = True
        self.say(f'    P{p.idx} abrigo nível {p.shelter} em {p.pos}')

    def rest_cost(self, p):
        at = p.shelter > 0 and p.shelter_pos == p.pos
        if at:
            return 2 if self.event == 7 else 1
        return self.cfg.rest_cost

    def rest(self, p):
        at = p.shelter > 0 and p.shelter_pos == p.pos
        p.pe -= self.rest_cost(p)
        p.food -= 1
        p.rest_used = True
        rem = 2 if at and p.shelter >= 2 else 1
        p.exh = max(0, p.exh - rem)
        self.say(f'    P{p.idx} descansa (-{rem})')

    def light_fire(self, p):
        p.pe -= self.cfg.fire_cost
        p.fire = True
        self.say(f'    P{p.idx} acende fogo')

    def transfer(self, p, q, give):
        p.pe -= self.cfg.transfer_pe
        for res, n in give:
            p.add(res, -n)
            self.gain(q, res, n)
        self.stats['transferencias'] += 1
        self.say(f'    P{p.idx} transfere {give} para P{q.idx}')

    def event_action(self, p, ev):
        p.ev_used = True
        e = self.event
        if e == 1:
            p.pe -= 1
            self.gain(p, 'food', 2)
            if self.d6() % 2:
                self.gain_exh(p, 'evento')
        elif e == 8:
            p.pe -= 1
            self.gain(p, 'food', 2)
        elif e == 9:
            p.pe -= 2
            self.gain(p, 'food', 1)
            self.gain(p, 'water', 1)
        elif e == 14:
            p.pe -= 1
            self.gain(p, 'water', 2 if self.tiles[p.pos].kind in ('R', 'Ca') and self.tiles[p.pos].revealed else 1)
        elif e == 11:
            self.gain(p, 'food', 2)
            self.gain_exh(p, 'evento')
        elif e == 12:
            if self.d6() % 2 == 0:
                self.gain(p, 'food', 2)
            else:
                self.gain_exh(p, 'evento')
        elif e == 17:
            p.food -= 1
            p.exh = max(0, p.exh - 1)
        self.say(f'    P{p.idx} usa o Evento {EVENT_NAMES[e]}')

    # -- Eventos: início da rodada / da vez / fim da vez
    def reveal_event(self):
        if self.round == 1 or not self.event_deck:
            self.event = None
            return
        self.event = self.event_deck.pop()
        self.stats[f'ev{self.event}'] += 1
        self.say(f'  * Evento: {EVENT_NAMES[self.event]}')
        if self.event == 10:
            for p in self.players:
                if p.alive and p.shelter > 0:
                    if p.water > 0 and water_value(self, p, -1) < 8:
                        p.water -= 1
                    elif p.water > 0 and p.exh + 1 >= self.cfg.exh_limit:
                        p.water -= 1
                    else:
                        self.gain_exh(p, 'evento')

    def start_turn(self, p):
        p.pe = pe_per_turn(self, p)
        p.moved_this_round = False
        p.ev_used = False
        p.turtle = False
        p.free_build = False
        p.turn_start_at_shelter = p.shelter > 0 and p.pos == p.shelter_pos
        e = self.event
        if e == 2:
            if p.exh == 0 and aiget(self, p, 'risk_aversion', 1.0) <= 1.0:
                if self.d6() % 2:
                    self.gain_exh(p, 'evento')
            else:
                p.pe -= 1
        elif e == 4 and p.food > 0:
            if food_value(self, p, -1) >= 6:
                p.pe -= 1
            else:
                p.food -= 1
        elif e == 5:
            if self.d6() % 2 == 0:
                p.pe -= 1
            elif p.food > 0:
                p.food -= 1
            else:
                self.gain_exh(p, 'evento')
        elif e == 15:
            hidden = [q for q in self.adj[p.pos] if not self.tiles[q].revealed]
            if hidden:
                q = self.rng.choice(hidden)
                if self.tiles[q].kind == 'Re':
                    t = self.tiles[q]
                    t.revealed = True
                    self.version += 1
                    self.say(f'    P{p.idx} revela Resgate em {q} (Rumo à extração)')
        if p.arch == 'Guardiao' and self.round in (1, 4, 7):
            p.fire = True
        p.pe = max(0, p.pe)

    def end_turn(self, p):
        if self.event == 6 and p.alive and not p.fire and not (
                p.shelter > 0 and p.pos == p.shelter_pos):
            if p.pe > 0:
                p.pe -= 1
            elif p.food > 0 and food_value(self, p, -1) < 10:
                p.food -= 1
            else:
                self.gain_exh(p, 'evento')

    # -- Prova
    def weekly_check(self):
        w = self.week()
        cfg = self.cfg
        shared = set()
        for g in self.players:
            if g.alive and g.arch == 'Guardiao' and g.fire:
                for q in self.players:
                    if q is not g and q.alive and q.pos == g.pos and not q.fire and q.water >= cfg.week_water[w]:
                        shared.add(q.idx)
                        break
        for p in self.turn_order():
            if not p.alive:
                continue
            paid = 0
            water_paid = False
            for res, req, item in (('food', cfg.week_food[w], 'panela'),
                                   ('water', cfg.week_water[w], 'cantil')):
                have = p.get(res)
                if have >= req:
                    p.add(res, -req)
                    paid += 1
                    water_paid = water_paid or res == 'water'
                elif have == req - 1 and p.item == item:
                    p.item = None
                    p.add(res, -have)
                    paid += 1
                    water_paid = water_paid or res == 'water'
                else:
                    self.gain_exh(p, 'prova_' + res)
                    if not p.alive:
                        break
            if not p.alive:
                continue
            if water_paid and cfg.water_fire_test and not p.fire and p.idx not in shared:
                if self.d6() % 2:
                    self.gain_exh(p, 'agua_sem_fogo')
                    self.stats['agua_sem_fogo_falha'] += 1
                self.stats['agua_sem_fogo_teste'] += 1
            if p.alive and paid == 2:
                p.weeks_paid += 1
            if cfg.spoil and w < 2:
                p.food = 0
        for p in self.players:
            p.fire = False
            p.ability_used = False
            p.rest_used = False
        self.say(f'  == Prova {w + 1}: ' + ', '.join(
            f'P{p.idx} d={p.exh} abr={p.shelter} c={p.food} a={p.water}{"" if p.alive else " X"}' for p in self.players))

    def turn_order(self):
        f = self.first
        return [self.players[(f + k) % self.n] for k in range(self.n)]

    def play(self):
        self.first = 0
        for self.round in range(1, self.cfg.rounds + 1):
            self.claims = {}
            self.say(f'-- Rodada {self.round}')
            self.reveal_event()
            for p in self.turn_order():
                if p.alive and not self.lost:
                    take_turn(self, p)
            if self.round % 3 == 0:
                self.weekly_check()
            self.first = (self.first + 1) % self.n
        return self.result()

    def completed(self, p):
        t = self.tiles[p.pos]
        return p.alive and p.shelter >= self.cfg.shelter_levels and t.kind == 'Re' and t.revealed

    def score(self, p):
        c = self.cfg
        s = (3 * p.weeks_paid + min(p.food, c.caps[0]) + min(p.water, c.caps[1])
             + min(p.wood, c.caps[2]) + (1 if p.item else 0) - 2 * p.exh)
        return max(0, s)

    def result(self):
        out = []
        for p in self.players:
            done = self.completed(p)
            reason = ('ok' if done else 'eliminado' if not p.alive else
                      'abrigo' if p.shelter < self.cfg.shelter_levels else 'fora_do_resgate')
            out.append(dict(idx=p.idx, arch=p.arch, done=done, reason=reason,
                            ps=self.score(p) if done else None, exh=p.exh, weeks=p.weeks_paid,
                            exh_src=dict(p.exh_src), died=p.died_round,
                            item=p.item, water=p.water, food=p.food))
        return out


# ------------------------------------------------------------------- IA

def aiget(g, p, key, default):
    return p.ai.get(key, g.cfg.ai.get(key, default))


def pe_per_turn(g, p):
    return g.cfg.pe - (1 if g.cfg.exh_pe and p.exh >= g.cfg.exh_pe else 0)


def food_value(g, p, extra=0):
    have = p.food + extra
    if have >= g.cfg.food_cap:
        return 0.0
    w = g.week()
    cur = g.cfg.week_food[w]
    if not g.cfg.spoil:
        total = sum(g.cfg.week_food[w:])
    else:
        total = cur
    if have < cur:
        return 10.0
    if have < total:
        return 5.0
    if have < total + g.cfg.caps[0] and (g.week() == 2 or not g.cfg.spoil):
        return 1.5
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


def res_value(g, p, res, extra=0):
    v = VALUE_FN[res](g, p, extra)
    if v < 3 and g.cfg.mode == 'coop':
        for q in g.players:
            if q is not p and q.alive and VALUE_FN[res](g, q) >= 6:
                v = max(v, 3.5)
    return v


def exh_cost(g, p):
    if p.exh + 1 >= g.cfg.exh_limit:
        return 40.0
    turns_left = g.cfg.rounds - g.round + 1
    pe_loss = 2.0 * turns_left if g.cfg.exh_pe and p.exh + 1 >= g.cfg.exh_pe and p.exh < g.cfg.exh_pe else 0.0
    return 5.0 + 4.0 * p.exh + pe_loss


def risk_penalty(g, p):
    if p.arch == 'Sobrevivencialista' and not p.ability_used:
        return 0.0
    if p.item == 'toldo':
        return 0.5
    return g.cfg.risk_fail / 6 * exh_cost(g, p) * aiget(g, p, 'risk_aversion', 1.0)


def tile_collect_value(g, p, pos):
    t = g.tiles[pos]
    best = (0.0, None)
    for res in RES:
        if t.tokens[res] <= 0:
            continue
        v = res_value(g, p, res)
        if v <= 0:
            continue
        if g.bonus_applies(p, t.kind, res):
            v += 0.9 * res_value(g, p, res, 1)
        if res == 'food' and g.event == 16 and not p.turtle:
            v += 0.9 * res_value(g, p, res, 1)
        if t.risk:
            v -= risk_penalty(g, p)
        if v > best[0]:
            best = (v, res)
    return best


def kind_values(g, p):
    res = g.cfg.res()
    rp = risk_penalty(g, p)
    rv = {r: res_value(g, p, r) for r in RES}
    out = {}
    for k in TILE_RES:
        tv = 0.0
        for r, n in res.get(k, {}).items():
            if n > 0:
                tv = max(tv, rv[r] * min(n, 2) * 0.45)
        if k in RISK_TILES:
            tv -= 0.3 * rp
        out[k] = tv
    return out


def explore_value(g, p, pos, pool, kv, has_rescue):
    bonus = 0.0
    if not has_rescue:
        bonus = 3.0 + 3.0 * g.round
        if pos in g.near_rescue:
            bonus *= 2.0
    tot = sum(pool.values()) or 1
    v = sum(c / tot * (kv[k] + (bonus if k == 'Re' else 0.0)) for k, c in pool.items())
    return v * aiget(g, p, 'explore_weight', 1.8)


def nearest_wood(g, pos):
    dm = g.dist_map(pos)
    cands = [q for q, t in g.tiles.items() if t.revealed and t.tokens['wood'] > 0]
    return min(cands, key=lambda q: dm[q]) if cands else None


def required_end_cost(g, p, pos, shelter=None, shelter_pos=None):
    shelter = p.shelter if shelter is None else shelter
    shelter_pos = p.shelter_pos if shelter_pos is None else shelter_pos
    L = g.cfg.shelter_levels
    res = g.known_rescues()
    if res:
        def dres(x):
            dm = g.dist_map(x, strict=True)
            return min(dm[r] for r in res)
    else:
        def dres(x):
            dm = g.dist_map(x, strict=True)
            hidden = [q for q in g.near_rescue if not g.tiles[q].revealed]
            return min((dm[q] for q in hidden), default=3) + 2
    if shelter >= L:
        return dres(pos)
    builds = L - shelter
    missing = builds - p.wood
    via, fetch = pos, 0
    if missing > 0:
        w = nearest_wood(g, pos)
        if w is not None:
            fetch = g.dist(pos, w, True) + missing
            via = w
    if shelter == 0:
        return fetch + builds + dres(via)
    return fetch + g.dist(via, shelter_pos, True) + builds + dres(shelter_pos)


def future_budget(g, p):
    return pe_per_turn(g, p) * (g.cfg.rounds - g.round)


def step_toward(g, p, tgt):
    dm = g.dist_map(tgt)
    return min(g.adj[p.pos], key=lambda q: (dm[q], not g.tiles[q].revealed))


def fire_value(g, p):
    if p.fire:
        return 0.0
    v = 0.0
    w = g.week()
    if g.cfg.water_fire_test and p.water >= g.cfg.week_water[w] - (1 if p.item == 'cantil' else 0):
        v = 0.5 * exh_cost(g, p) if not (p.arch == 'Sobrevivencialista' and not p.ability_used) else 0.5
        v *= 1.0 if g.round % 3 == 0 else 0.5
    if g.event == 6 and not (p.shelter > 0 and p.pos == p.shelter_pos):
        v += 0.8 * exh_cost(g, p)
    return v


def event_candidates(g, p):
    e = g.event
    if p.ev_used or e is None:
        return []
    out = []
    fv = res_value(g, p, 'food')
    fv2 = fv + res_value(g, p, 'food', 1)
    if e == 8 and p.pe >= 1 and fv > 0:
        out.append((fv2, ('event',)))
    elif e == 1 and p.pe >= 1 and fv > 0:
        out.append((fv2 - 0.5 * exh_cost(g, p), ('event',)))
    elif e == 9 and p.pe >= 2:
        v = fv + res_value(g, p, 'water')
        out.append((v / 2, ('event',)))
    elif e == 14 and p.pe >= 1:
        v = res_value(g, p, 'water')
        if g.tiles[p.pos].revealed and g.tiles[p.pos].kind in ('R', 'Ca'):
            v += res_value(g, p, 'water', 1)
        out.append((v, ('event',)))
    elif e == 11:
        out.append((fv2 - exh_cost(g, p), ('event',)))
    elif e == 12:
        out.append((0.5 * fv2 - 0.5 * exh_cost(g, p), ('event',)))
    elif e == 17 and p.exh > 0 and p.food > 0:
        out.append((exh_cost(g, p) * 0.7 - food_value(g, p, -1) * 0.5, ('event',)))
    return out


def candidate_actions(g, p):
    cfg = g.cfg
    L = cfg.shelter_levels
    here = g.tiles[p.pos]
    cands = []
    if not here.revealed:
        return [(100.0, ('explore',), None)]
    if here.collected_round != g.round:
        v, r = tile_collect_value(g, p, p.pos)
        if r:
            cands.append((v, ('collect', r), None))
    if p.wood > 0 and p.shelter < L:
        rs = g.known_rescues()
        if p.shelter == 0:
            ok = here.kind != 'Re' and (
                min(g.dist(p.pos, r) for r in rs) <= aiget(g, p, 'build_radius', 1) if rs
                else hexdist(p.pos, g.start) <= 2)
        else:
            ok = p.pos == p.shelter_pos
        if ok:
            cands.append((9.0 if not (g.event == 18 and not p.free_build) else 30.0, ('build',), None))
    if p.exh > 0 and not p.rest_used and p.food > 0:
        cost = g.rest_cost(p)
        if cost <= p.pe:
            at = p.shelter > 0 and p.shelter_pos == p.pos
            gain = exh_cost(g, p) * (1.6 if at and p.shelter >= 2 and p.exh >= 2 else 1) * 0.6
            val = gain - food_value(g, p, -1) * 0.4
            if val > 0:
                cands.append((val / cost, ('rest',), None))
    fv = fire_value(g, p)
    if fv > 0 and p.pe >= cfg.fire_cost:
        cands.append((fv / max(1, cfg.fire_cost), ('fire',), None))
    for v, act in event_candidates(g, p):
        if v > 0:
            cands.append((v, act, None))
    if cfg.mode == 'coop':
        for q in g.players:
            if q is p or not q.alive or q.pos != p.pos:
                continue
            give = []
            for res in RES:
                n = min(2 - sum(x[1] for x in give), team_need(g, q, res), team_surplus(g, p, res))
                if n > 0:
                    give.append((res, n))
            if give:
                cands.append((9.5 * sum(x[1] for x in give), ('transfer', q, give), None))
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
            if v > 0:
                cands.append((v / d, ('goto', pos), pos))
            continue
        v, r = tile_collect_value(g, p, pos)
        if r:
            if t.collected_round == g.round or d + 1 > p.pe:
                v *= 0.75
            cands.append((v / (d + 1), ('goto', pos), pos))
    if 0 < p.shelter < L and p.wood > 0 and p.pos != p.shelter_pos:
        cands.append((9.0 / (dm[p.shelter_pos] + 1), ('goto', p.shelter_pos), None))
    if cfg.mode == 'coop':
        for q in g.players:
            if q is p or not q.alive or q.pos == p.pos:
                continue
            n = sum(min(2, team_need(g, q, r), team_surplus(g, p, r)) for r in RES)
            if n > 0:
                cands.append((9.0 * min(n, 2) / (dm[q.pos] + 1), ('goto', q.pos), None))
    return cands


def team_need(g, q, res):
    w = g.week()
    if res == 'food':
        return max(0, g.cfg.week_food[w] - q.food)
    if res == 'water':
        return max(0, g.cfg.week_water[w] - q.water)
    return max(0, g.cfg.shelter_levels - q.shelter - q.wood) if g.round >= 5 else 0


def team_surplus(g, p, res):
    w = g.week()
    if res == 'food':
        return max(0, p.food - g.cfg.week_food[w])
    if res == 'water':
        return max(0, p.water - sum(g.cfg.week_water[w:]))
    return max(0, p.wood - (g.cfg.shelter_levels - p.shelter))


def apply_action(g, p, act):
    k = act[0]
    if k != 'goto':
        p.move_credit = False
    if k == 'collect':
        g.collect(p, act[1])
    elif k == 'build':
        g.build(p)
    elif k == 'rest':
        g.rest(p)
    elif k == 'fire':
        g.light_fire(p)
    elif k == 'explore':
        g.explore(p)
    elif k == 'event':
        g.event_action(p, g.event)
    elif k == 'transfer':
        g.transfer(p, act[1], act[2])
    elif k == 'goto':
        g.move(p, step_toward(g, p, act[1]))


def action_cost(g, p, act):
    k = act[0]
    if k == 'goto':
        return g.move_cost(p, dest=step_toward(g, p, act[1]))
    if k == 'rest':
        return g.rest_cost(p)
    if k == 'fire':
        return g.cfg.fire_cost
    if k == 'explore':
        return g.cfg.explore_cost
    if k == 'build':
        return 0 if g.event == 18 and not p.free_build else 1
    if k == 'event':
        return {1: 1, 8: 1, 9: 2, 14: 1}.get(g.event, 0)
    if k == 'transfer':
        return g.cfg.transfer_pe
    return 1


def feasible(g, p, act):
    cost = action_cost(g, p, act)
    if cost > p.pe:
        return False
    k = act[0]
    pos, sh, shpos = p.pos, p.shelter, p.shelter_pos
    if k == 'goto':
        pos = step_toward(g, p, act[1])
        if not g.tiles[pos].revealed:
            cost += g.cfg.explore_cost
    elif k == 'build':
        sh, shpos = p.shelter + 1, p.shelter_pos or p.pos
    need = required_end_cost(g, p, pos, sh, shpos)
    return need + aiget(g, p, 'end_margin', 0) <= p.pe - cost + future_budget(g, p)


def plan_step(g, p):
    L = g.cfg.shelter_levels
    here = g.tiles[p.pos]
    if not here.revealed:
        return ('explore',)
    if p.shelter + p.wood < L:
        if here.tokens['wood'] > 0 and here.collected_round != g.round:
            return ('collect', 'wood')
        w = nearest_wood(g, p.pos)
        if w is not None and w != p.pos:
            return ('goto', w)
    if p.shelter < L and p.wood > 0:
        if p.shelter == 0 and here.kind != 'Re':
            return ('build',)
        if p.shelter > 0 and p.pos == p.shelter_pos:
            return ('build',)
    if 0 < p.shelter < L and p.wood >= L - p.shelter:
        return ('goto', p.shelter_pos)
    rs = g.known_rescues()
    if rs:
        tgt = min(rs, key=lambda r: g.dist(p.pos, r))
        return ('goto', tgt) if tgt != p.pos else None
    hidden = [q for q in g.near_rescue if not g.tiles[q].revealed]
    if hidden:
        return ('goto', min(hidden, key=lambda q: g.dist(p.pos, q)))
    return None


def take_turn(g, p):
    g.start_turn(p)
    p.move_credit = False
    guard = 0
    while p.pe > 0 and p.alive and guard < 25 and not g.lost:
        guard += 1
        cands = sorted(candidate_actions(g, p), key=lambda c: -c[0])
        chosen = None
        if p.target is not None and cands and cands[0][1][0] == 'goto':
            best = cands[0][0]
            for ratio, act, claim in cands:
                if act == ('goto', p.target) and ratio >= 0.6 * best and feasible(g, p, act):
                    chosen = (act, claim)
                    break
        for ratio, act, claim in ([] if chosen else cands):
            if ratio < aiget(g, p, 'min_ratio', 0.25):
                break
            if feasible(g, p, act):
                chosen = (act, claim)
                break
        if chosen is None:
            act = plan_step(g, p)
            if act is None or action_cost(g, p, act) > p.pe:
                break
            need = required_end_cost(g, p, p.pos)
            if need <= future_budget(g, p) and g.round < g.cfg.rounds and act[0] != 'explore':
                break
            chosen = (act, None)
        act, claim = chosen
        if (g.event == 6 and not p.fire and p.pe == 1 and act[0] not in ('fire', 'explore')
                and not (p.shelter > 0 and p.pos == p.shelter_pos)
                and not (act[0] == 'goto' and step_toward(g, p, act[1]) == p.shelter_pos)):
            break  # guarda 1 PE para a Hipotermia
        if claim is not None:
            g.claims[claim] = p.idx
        p.target = act[1] if act[0] == 'goto' else None
        apply_action(g, p, act)
        if p.target == p.pos:
            p.target = None
    g.end_turn(p)


# ------------------------------------------------------------ relatório

def run(n, cfg, games, seed=1):
    rng = random.Random(seed)
    rows = []
    for _ in range(games):
        g = Game(n, cfg, random.Random(rng.random()))
        res = g.play()
        for seat, r in enumerate(res):
            r['seat'] = seat
            r['lost'] = g.lost
        rows.append(res)
    return rows


def summarize(rows):
    n = len(rows[0])
    P = [r for g in rows for r in g]
    done = [r for r in P if r['done']]
    s = {
        'conclui': sum(r['done'] for r in P) / len(P),
        'todos': sum(all(r['done'] for r in g) for g in rows) / len(rows),
        'eliminados': sum(r['reason'] == 'eliminado' for r in P) / len(P),
        'motivos': collections.Counter(r['reason'] for r in P),
        'ps': statistics.mean(r['ps'] for r in done) if done else 0,
    }
    src = collections.Counter()
    for r in P:
        src.update(r['exh_src'])
    s['desgaste_por_pessoa'] = {k: round(v / len(P), 3) for k, v in src.most_common()}
    wins, games_a, seat = collections.Counter(), collections.Counter(), collections.Counter()
    ties = 0
    for g in rows:
        for r in g:
            games_a[r['arch']] += 1
        fin = [r for r in g if r['done']]
        if not fin:
            continue
        best = max(r['ps'] for r in fin)
        top = [r for r in fin if r['ps'] == best]
        ties += len(top) > 1
        for r in top:
            wins[r['arch']] += 1 / len(top)
            seat[r['seat']] += 1 / len(top)
    s['empate'] = ties / len(rows)
    s['vit_arq_x_n'] = {a: round(wins[a] / games_a[a] * n, 2) for a in ARCHETYPES if games_a[a]}
    s['conc_arq'] = {a: round(sum(r['done'] for r in P if r['arch'] == a) / games_a[a], 2)
                     for a in ARCHETYPES if games_a[a]}
    s['vit_assento'] = {k: round(seat[k] / len(rows), 3) for k in range(n)}
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--games', type=int, default=1000)
    ap.add_argument('--trace', type=int, default=0)
    ap.add_argument('--seed', type=int, default=7)
    ap.add_argument('--mode', default='comp')
    a = ap.parse_args()
    cfg = Config(mode=a.mode)
    if a.trace:
        g = Game(a.trace, cfg, random.Random(a.seed), trace=True)
        for r in range(g.rows):
            print(' ' * (2 * (r % 2)) + ' '.join(f'{g.tiles[(c, r)].kind:>3}' for c in range(g.cols)))
        print([(p.arch, p.item) for p in g.players])
        for r in g.play():
            print(r)
        return
    for n in (2, 3, 4):
        s = summarize(run(n, cfg, a.games, a.seed))
        print(f'\n=== {n} pessoas | {cfg.mode} ===')
        for k, v in s.items():
            print(f'  {k:22} {v:.3f}' if isinstance(v, float) else f'  {k:22} {v}')


if __name__ == '__main__':
    main()
