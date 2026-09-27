"""Validação da proposta 0.4.2 sobre o manual 0.4.1.

    python3 final041.py [N]

Base comum (pedida pelo autor): comida não estraga (limite de 4 comidas carregadas)
e Desgaste >= 1 reduz a vez para 3 PE.
"""
import collections
import copy
import statistics
import sys
from multiprocessing import Pool

import sim041 as S

FLORESTA3 = dict(S.TILE_RES, F={'wood': 3})
TC_CLAREIRA = copy.deepcopy(S.TILE_COUNTS)
TC_CLAREIRA[4]['Pa'] = 0
TC_CLAREIRA[4]['Cl'] += 1

BASE = dict(food_cap=4, tile_res=FLORESTA3)
COMP = dict(week_food=(2, 2, 2), week_water=(1, 1, 1))
COOP = {2: dict(week_food=(1, 2, 2), week_water=(1, 1, 1)),
        3: dict(week_food=(1, 1, 2), week_water=(1, 1, 1)),
        4: dict(week_food=(1, 1, 1), week_water=(1, 1, 1))}

V = {
    '0.4.1 manual (sem estragar)': lambda n, m: dict(mode=m, food_cap=4),
    '0.4.2 proposta': lambda n, m: dict(BASE, mode=m, **(COMP if m == 'comp' else COOP[n])),
    '0.4.2 + Pasto→Clareira (4p)': lambda n, m: dict(BASE, mode=m, tile_counts=TC_CLAREIRA,
                                                     **(COMP if m == 'comp' else COOP[n])),
}


def job(a):
    k, n, m = a
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 1500
    rows = S.run(n, S.Config(**V[k](n, m)), N, 777)
    s = S.summarize(rows)
    died = collections.Counter(r['died'] for g in rows for r in g if r['reason'] == 'eliminado')
    return k, n, m, s, died


if __name__ == '__main__':
    jobs = [(k, n, m) for k in V for m in ('comp', 'coop') for n in (2, 3, 4)]
    with Pool(4) as p:
        res = p.map(job, jobs)
    for k, n, m, s, died in res:
        if m == 'comp':
            seat = s['vit_assento'].values()
            elim9 = died[9] / max(1, sum(died.values()))
            print(f'{k:30} {n}p COMP conclui={s["conclui"]:.2f} elim={s["eliminados"]:.2f} '
                  f'(na rodada 9: {elim9:.0%}) PS={s["ps"]:.1f} empate={s["empate"]:.2f} '
                  f'Δassento={max(seat) - min(seat):.2f}')
            print(f'{"":30}    arquétipos (vitória × n): {s["vit_arq_x_n"]}')
            print(f'{"":30}    desgaste/pessoa: {s["desgaste_por_pessoa"]}')
        else:
            print(f'{k:30} {n}p COOP vence={s["todos"]:.2f}')
