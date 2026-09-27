"""Evidências de simulação para o raio-X do curso (mecânicas, jornada, ritmo).

    python3 evidencias_sea.py [N]

Usa a proposta 0.4.2 (modo avançado) como base e mede:
- como as pessoas gastam a energia (mistura de ações);
- a espiral de Desgaste (chance de concluir x Desgaste depois da 1ª Prova);
- o ritmo de descobertas e de eliminações ao longo das rodadas;
- o efeito das Trilhas (1 PE move até 2 tiles explorados).
"""
import collections
import random
import statistics
import sys

import sim041 as S
from final041 import BASE, COMP, TC_CLAREIRA

N = int(sys.argv[1]) if len(sys.argv) > 1 else 600


def instrumented(cfg, n, games, seed=5):
    acts = collections.Counter()
    reveals = collections.Counter()
    elim = collections.Counter()
    after1 = collections.Counter()
    done_after1 = collections.Counter()
    turns_out = []
    rng = random.Random(seed)
    orig_apply = S.apply_action

    def apply(g, p, act):
        k = act[0]
        if k == 'goto':
            k = 'mover (grátis)' if g.move_cost(p, dest=S.step_toward(g, p, act[1])) == 0 else 'mover'
        acts[k] += 1
        if act[0] == 'explore':
            reveals[g.round] += 1
        orig_apply(g, p, act)

    S.apply_action = apply
    try:
        for _ in range(games):
            g = S.Game(n, cfg, random.Random(rng.random()))
            snap = {}
            orig_check = g.weekly_check

            def check(g=g, snap=snap, orig=orig_check):
                orig()
                if g.round == 3:
                    for p in g.players:
                        snap[p.idx] = p.exh if p.alive else None
            g.weekly_check = check
            res = g.play()
            for r in res:
                if r['reason'] == 'eliminado':
                    elim[r['died']] += 1
                    turns_out.append(g.cfg.rounds - r['died'])
                d = snap.get(r['idx'])
                if d is not None:
                    key = min(d, 2)
                    after1[key] += 1
                    done_after1[key] += r['done']
    finally:
        S.apply_action = orig_apply
    people = games * n
    return dict(
        acoes={k: round(v / people, 1) for k, v in acts.most_common()},
        descobertas_por_rodada={r: round(reveals[r] / people, 2) for r in range(1, 10)},
        eliminacoes_por_rodada={r: round(elim[r] / people, 3) for r in range(1, 10) if elim[r]},
        rodadas_fora_media=round(statistics.mean(turns_out), 1) if turns_out else 0,
        conclui_por_desgaste_apos_prova1={k: (round(done_after1[k] / after1[k], 2), after1[k]) for k in sorted(after1)},
    )


if __name__ == '__main__':
    adv = S.Config(**BASE, **COMP, tile_counts=TC_CLAREIRA)
    print('=== Modo avançado (proposta 0.4.2), 4 pessoas, competitivo')
    for k, v in instrumented(adv, 4, N).items():
        print(f'  {k}: {v}')
    trail = S.Config(**BASE, **COMP, tile_counts=TC_CLAREIRA, trail=True)
    print('=== Com Trilhas (1 PE move até 2 tiles explorados)')
    for k, v in instrumented(trail, 4, N).items():
        if k in ('acoes',):
            print(f'  {k}: {v}')
    for n in (2, 3, 4):
        a = S.summarize(S.run(n, adv, N, 9))
        t = S.summarize(S.run(n, trail, N, 9))
        print(f'  {n}p conclui: sem trilhas {a["conclui"]:.2f} | com trilhas {t["conclui"]:.2f}')
