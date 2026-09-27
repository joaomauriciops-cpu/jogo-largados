"""Regras do manual 0.5 (consolidação das propostas testadas) e validação.

    python3 v05.py [N]
"""
import sys
from multiprocessing import Pool

import sim041 as S
from final041 import FLORESTA3, TC_CLAREIRA

ARQ = dict(guardian_mode='fire_events', surv_events=True, explorer_mode='both')
AVANCADO = dict(food_cap=4, tile_res=FLORESTA3, tile_counts=TC_CLAREIRA, escalate=True,
                escalate_harsh=2, **ARQ)
AV_COMP = dict(week_food=(2, 2, 2), week_water=(1, 1, 1))
AV_COOP = {2: dict(week_food=(1, 2, 2), week_water=(1, 1, 1)),
           3: dict(week_food=(1, 1, 2), week_water=(1, 1, 1)),
           4: dict(week_food=(1, 1, 1), week_water=(1, 1, 1))}
SOFA = dict(AVANCADO, rounds=6, shelter_levels=2, water_fire_test=False, exh_pe=0,
            escalate=False, archetypes=tuple(a for a in S.ARCHETYPES if a != 'Guardiao'))
SF_COMP = dict(week_food=(2, 3), week_water=(1, 1))
SF_COOP = {2: dict(week_food=(2, 3), week_water=(1, 1)),
           3: dict(week_food=(2, 2), week_water=(1, 1)),
           4: dict(week_food=(2, 2), week_water=(1, 1))}


def cfg(modo, mode, n):
    if modo == 'avancado':
        # competitivo: 3 Eventos Duros na semana 3; cooperativo: 2 (a rodada 7 usa um Misto)
        kw = dict(AVANCADO, escalate_harsh=3 if mode == 'comp' else 2)
        return S.Config(mode=mode, **kw, **(AV_COMP if mode == 'comp' else AV_COOP[n]))
    return S.Config(mode=mode, **SOFA, **(SF_COMP if mode == 'comp' else SF_COOP[n]))


def job(a):
    modo, mode, n = a
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    s = S.summarize(S.run(n, cfg(modo, mode, n), N, 2026))
    return modo, mode, n, s


if __name__ == '__main__':
    jobs = [(m, md, n) for m in ('avancado', 'sofa') for md in ('comp', 'coop') for n in (2, 3, 4)]
    with Pool(4) as p:
        for modo, mode, n, s in p.map(job, jobs):
            if mode == 'comp':
                a = s['vit_arq_x_n']
                m = sum(a.values()) / len(a)
                print(f'{modo:9} {n}p COMP conclui={s["conclui"]:.2f} elim={s["eliminados"]:.2f} PS={s["ps"]:.1f} '
                      f'arq={min(a.values()) / m:.2f}–{max(a.values()) / m:.2f}')
            else:
                print(f'{modo:9} {n}p COOP vence={s["todos"]:.2f}')
