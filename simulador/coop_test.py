"""Variantes do modo cooperativo sobre as regras comuns da v0.6.

    python3 coop_test.py [N]

Meta: vitória no coop ≈ taxa de conclusão individual do competitivo, igual para 2, 3 e 4.
"""
import sys, statistics, dataclasses, sim
from multiprocessing import Pool
from experimentos import V06 as V05
C = dict(V05, mode='coop')
V = {
 'coop v0.5': C,
 'Transferir até adjacente': dict(C, transfer_range=1),
 'Transferir 0 PE, adjacente': dict(C, transfer_range=1, transfer_pe=0),
 'abrigo p/ 2 pessoas': dict(C, coop_shelter_cap=2),
 'abrigo p/ 2 + transf. adjacente': dict(C, coop_shelter_cap=2, transfer_range=1),
 'abrigo p/ todos + transf. adjacente': dict(C, coop_shelter_cap=4, transfer_range=1),
 '+ Cuidar': dict(C, coop_shelter_cap=4, transfer_range=1, care=True),
 '+ Cuidar + Juntar na Prova (v0.6)': dict(C, coop_shelter_cap=4, transfer_range=1, care=True, pool_at_check=True),
}
def job(a):
    name, n = a
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 1500
    rows = sim.run(n, sim.Config(**V[name]), games, 77)
    P = [r for g in rows for r in g]
    win = sum(all(r['done'] for r in g) for g in rows) / len(rows)
    return name, n, win, statistics.mean(r['done'] for r in P), statistics.mean(r['transfers'] for r in P), statistics.mean(r['shared'] for r in P)
if __name__ == '__main__':
    comp = {n: statistics.mean(r['done'] for g in sim.run(n, sim.Config(**V05), 800, 77) for r in g) for n in (2, 3, 4)}
    print('referência: conclusão individual no competitivo v0.5:', {n: round(v, 2) for n, v in comp.items()})
    with Pool(4) as p:
        res = p.map(job, [(k, n) for k in V for n in (2, 3, 4)])
    for name, n, w, c, t, sh in res:
        print(f'{name:36} n={n} vitória={w:.2f} indiv={c:.2f} transf/pessoa={t:.2f} abrigo dividido={sh:.2f}')
