"""Ajuste fino da dificuldade: competitivo (conclusão individual) x cooperativo (vitória).

    python3 ajuste.py [N]
"""
import sys, statistics, sim
from multiprocessing import Pool
from experimentos import V05
COOP = dict(coop_shelter_cap=4, transfer_range=1)
D = {
 'v0.5': {},
 'v0.5 + água 1/2/2': dict(week_water=(1, 2, 2)),
 'v0.5 + comida 2/3/4': dict(week_food=(2, 3, 4)),
 'v0.5 + água 1/2/2 + comida 2/3/4': dict(week_water=(1, 2, 2), week_food=(2, 3, 4)),
}
def job(a):
    name, n = a
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    comp = sim.run(n, sim.Config(**V05, **D[name]), N, 91)
    coop2 = sim.run(n, sim.Config(**V05, **D[name], mode='coop', coop_shelter_cap=2, transfer_range=1), N, 91)
    coop4 = sim.run(n, sim.Config(**V05, **D[name], mode='coop', **COOP), N, 91)
    ind = statistics.mean(r['done'] for g in comp for r in g)
    s = sim.summarize(comp, None)
    w = lambda rows: sum(all(r['done'] for r in g) for g in rows) / len(rows)
    return name, n, ind, w(coop2), w(coop4), s['eliminados'], max(s['vit_assento'].values()) - min(s['vit_assento'].values()), s['vit_arquetipo']
if __name__ == '__main__':
    with Pool(4) as p:
        res = p.map(job, [(k, n) for k in D for n in (2, 3, 4)])
    for name, n, ind, c2, c4, el, seat, arch in res:
        print(f'{name:34} n={n} comp={ind:.2f} coop(abrigo p/2)={c2:.2f} coop(abrigo p/todos)={c4:.2f} elim={el:.2f} Δassento={seat:.2f} arq×n=' +
              ' '.join(f'{a[:4]}:{v * n:.2f}' for a, v in arch.items()))
