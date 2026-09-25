"""Bateria de experimentos sobre o simulador (regras v0.4 e variantes).

    python3 experimentos.py [--games N]

Cada linha resume N partidas por contagem de jogadores. Colunas:
  conc   = % de jogadores que concluem a prova (competitivo)
  todos  = % de partidas em que todos concluem (= vitória no cooperativo com IA competitiva)
  coop   = % de vitórias no modo cooperativo (IA cooperativa, com Transferir)
  elim   = % de jogadores eliminados
  PS     = pontuação média de quem conclui
  emp    = % de partidas com empate no topo
  assento= diferença entre o assento que mais vence e o que menos vence (p.p.)
  arq    = diferença entre o arquétipo que mais vence e o que menos vence (p.p.)
  sobrev = taxa de vitória do Sobrevivencialista ÷ taxa justa (1/n)
"""
import argparse
import dataclasses
import random
import statistics

import sim


def measure(cfg, n, games, seed):
    rows = sim.run(n, cfg, games, seed)
    s = sim.summarize(rows, cfg)
    coop_cfg = dataclasses.replace(cfg, mode='coop')
    coop = sim.run(n, coop_cfg, games, seed)
    coop_win = sum(all(r['done'] for r in g) for g in coop) / len(coop)
    seat = s['vit_assento'].values()
    arch = s['vit_arquetipo']
    return dict(
        conc=100 * s['conclusao_individual'], todos=100 * s['todos_concluem'],
        coop=100 * coop_win, elim=100 * s['eliminados'], PS=s['ps_medio'],
        emp=100 * s['empates_no_topo'],
        assento=100 * (max(seat) - min(seat)),
        arq=100 * (max(arch.values()) - min(arch.values())),
        sobrev=arch.get('Sobrevivencialista', 0) * n,
    )


V05 = dict(reveal_ring1=True, order='snake', exh_pe=1,
           hunter_fail_faces=1, builder_start_wood=1, surv_mode='all')

VARIANTS = {
    'v0.4 (manual)': dict(),
    '3 PE': dict(pe=3),
    '5 PE': dict(pe=5),
    'ordem serpente': dict(order='snake'),
    'ordem catch-up': dict(order='catchup'),
    'ordem aleatória a cada rodada': dict(order='random'),
    'vizinhos do Início revelados': dict(reveal_ring1=True),
    'vizinhos revelados + serpente': dict(reveal_ring1=True, order='snake'),
    'coleta 1 por pessoa/rodada': dict(collect_limit='player'),
    'reposição +1 comida/semana': dict(restock=1),
    'semana 3 = 4 comidas': dict(week_food=(2, 3, 4)),
    'água 1/2/2': dict(week_water=(1, 2, 2)),
    'Exaustão elimina em 2': dict(exh_limit=2),
    'com Exaustão, 3 PE': dict(exh_pe=1),
    'proposta v0.5': V05,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--games', type=int, default=1500)
    ap.add_argument('--seed', type=int, default=2024)
    ap.add_argument('--only', default='')
    a = ap.parse_args()
    cols = ['conc', 'todos', 'coop', 'elim', 'PS', 'emp', 'assento', 'arq', 'sobrev']
    for name, kw in VARIANTS.items():
        if a.only and a.only not in name:
            continue
        cfg = sim.Config(**kw)
        print(f'\n### {name}')
        print('n   ' + ' '.join(f'{c:>7}' for c in cols))
        for n in (2, 3, 4):
            m = measure(cfg, n, a.games, a.seed)
            print(f'{n}   ' + ' '.join(f'{m[c]:7.1f}' if c != 'sobrev' else f'{m[c]:7.2f}' for c in cols))


if __name__ == '__main__':
    main()
