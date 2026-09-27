"""Ajuste de dificuldade do manual 0.4.1 (sem comida estragando, Desgaste reduz PE).

    python3 ajuste041.py [N]

Metas do autor: ~50% de conclusão individual no competitivo e ~40% de vitória no
cooperativo, iguais para 2, 3 e 4 pessoas.
"""
import sys
import sim041 as S
from multiprocessing import Pool

V = {
    '0.4.1': {},
    'comida 2/2/3': dict(week_food=(2, 2, 3)),
    'comida 1/2/3': dict(week_food=(1, 2, 3)),
    'comida 1/2/2': dict(week_food=(1, 2, 2)),
    'água 1/1/1': dict(week_water=(1, 1, 1)),
    'comida 2/2/3 + água 1/1/1': dict(week_food=(2, 2, 3), week_water=(1, 1, 1)),
    'comida 1/2/2 + água 1/1/1': dict(week_food=(1, 2, 2), week_water=(1, 1, 1)),
    'Explorar grátis': dict(explore_cost=0),
}


def job(a):
    k, n, mode = a
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    s = S.summarize(S.run(n, S.Config(mode=mode, **V[k]), N, 21))
    return k, n, mode, s['conclui'] if mode == 'comp' else s['todos'], s['eliminados']


if __name__ == '__main__':
    jobs = [(k, n, m) for k in V for m in ('comp', 'coop') for n in (2, 3, 4)]
    with Pool(4) as p:
        res = {(k, n, m): (v, e) for k, n, m, v, e in p.map(job, jobs)}
    print(f'{"variante":28} | competitivo (conclui)   | cooperativo (vence)')
    print(f'{"":28} |   2p    3p    4p        |   2p    3p    4p')
    for k in V:
        c = ' '.join(f'{res[(k, n, "comp")][0]:5.2f}' for n in (2, 3, 4))
        o = ' '.join(f'{res[(k, n, "coop")][0]:5.2f}' for n in (2, 3, 4))
        print(f'{k:28} | {c}       | {o}')
