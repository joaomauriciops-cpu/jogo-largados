"""Comparação final: regras v0.4 contra a proposta v0.5 (2000 partidas por célula)."""
import sys, sim, experimentos
from multiprocessing import Pool
from experimentos import V05
V = {'v0.4 (manual)': {}, 'proposta v0.5': V05}
def job(a):
    name, n = a
    return name, n, experimentos.measure(sim.Config(**V[name]), n, int(sys.argv[1]) if len(sys.argv) > 1 else 2000, 4242)
if __name__ == '__main__':
    cols = ['conc', 'todos', 'coop', 'elim', 'PS', 'emp', 'assento', 'arq', 'sobrev']
    with Pool(4) as p:
        res = p.map(job, [(v, n) for v in V for n in (2, 3, 4)])
    last = None
    for name, n, m in res:
        if name != last:
            print(f'\n### {name}\nn   ' + ' '.join(f'{c:>7}' for c in cols)); last = name
        print(f'{n}   ' + ' '.join(f'{m[c]:7.2f}' if c == 'sobrev' else f'{m[c]:7.1f}' for c in cols))
