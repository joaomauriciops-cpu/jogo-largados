"""Torneio de estilos: quatro IAs com prioridades diferentes na mesma mesa.

    python3 estilos.py [--games N]
"""
import argparse
import collections
import random

import sim

STYLES = {
    'equilibrado': {},
    'explorador': {'explore_weight': 2.0},
    'caseiro': {'explore_weight': 0.4},
    'arrojado': {'risk_aversion': 0.2},
    'cauteloso': {'risk_aversion': 2.5, 'end_margin': 2},
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--games', type=int, default=2000)
    ap.add_argument('--n', type=int, default=4)
    a = ap.parse_args()
    rng = random.Random(99)
    cfg = sim.Config()
    win, games, done, ps = (collections.Counter() for _ in range(4))
    names = list(STYLES)
    for _ in range(a.games):
        g = sim.Game(a.n, cfg, random.Random(rng.random()))
        pick = rng.sample(names, a.n)
        for p, st in zip(g.players, pick):
            p.ai = STYLES[st]
        res = g.play()
        fin = [r for r in res if r['done']]
        best = max((r['ps'] for r in fin), default=None)
        top = [r for r in fin if r['ps'] == best]
        for r, st in zip(res, pick):
            games[st] += 1
            done[st] += r['done']
            ps[st] += r['ps'] or 0
            if r in top:
                win[st] += 1 / len(top)
    print(f'{"estilo":12} {"vitória":>8} {"conclui":>8} {"PS médio":>9}   (taxa justa de vitória = {1 / a.n:.2f})')
    for st in names:
        print(f'{st:12} {win[st] / games[st]:8.3f} {done[st] / games[st]:8.3f} {ps[st] / max(1, done[st]):9.2f}')


if __name__ == '__main__':
    main()
