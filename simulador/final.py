"""Comparação final: v0.4 x v0.6 (competitivo e cooperativo).

    python3 final.py [N]
"""
import sys, statistics, sim
from multiprocessing import Pool
from experimentos import V06, COOP06
V = {
 'v0.4 competitivo': dict(),
 'v0.4 cooperativo': dict(mode='coop'),
 'v0.6 competitivo': V06,
 'v0.6 cooperativo (abrigo p/ 2)': dict(V06, mode='coop', **dict(COOP06, coop_shelter_cap=2)),
 'v0.6 cooperativo (abrigo do grupo)': dict(V06, mode='coop', **COOP06),
}
def job(a):
    name, n = a
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    rows = sim.run(n, sim.Config(**V[name]), N, 4242)
    s = sim.summarize(rows, None)
    return name, n, s
if __name__ == '__main__':
    with Pool(4) as p:
        res = p.map(job, [(k, n) for k in V for n in (2, 3, 4)])
    for name, n, s in res:
        seat = s['vit_assento'].values(); arch = s['vit_arquetipo']
        line = f'{name:36} n={n} conclui={s["conclusao_individual"]:.2f} todos={s["todos_concluem"]:.2f} elim={s["eliminados"]:.2f}'
        if 'compet' in name:
            line += (f' PS={s["ps_medio"]:.1f} empate={s["empates_no_topo"]:.2f} Δassento={max(seat) - min(seat):.2f} arq×n=' +
                     ' '.join(f'{a[:4]}:{v * n:.2f}' for a, v in arch.items()))
        print(line)
