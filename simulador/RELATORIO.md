# Análise por simulação — Largados e Pelados v0.4

Objetivos informados pelo autor:
- **modos:** competitivo e cooperativo com o mesmo peso;
- **dificuldade:** um jogador competente conclui a prova em **60–70%** das partidas;
- **público:** gamers, partidas de 45–75 min;
- **interação entre jogadores:** a decidir com base nos dados.

## Como a simulação foi feita

`sim.py` implementa as regras do manual 0.4:
- mapa de hexágonos com linhas deslocadas e as restrições de montagem;
- Eventos, itens, arquétipos, risco, Exaustão, descanso, Prova Semanal, comida que estraga, Resgate e PS;
- o modo cooperativo com Transferir.

Cada jogador é uma IA heurística:
- a cada PE, compara o valor de coletar, construir, descansar ou explorar dividido pelo custo em PE;
- tem uma restrição de fim de jogo: nunca se afasta a ponto de não conseguir buscar madeira, terminar o abrigo e chegar ao Resgate.

Foram milhares de partidas por configuração (1.000 a 3.000 por célula).

**Cuidado ao ler os números:** a IA não é um humano.
- **Onde ela é mais forte que um humano:** calcula rotas sem errar e não esquece regras.
- **Onde ela é mais fraca:** não blefa, não planeja a semana inteira e coopera mal.

As tendências e as comparações entre variantes são mais confiáveis que os valores absolutos. O próprio manual relata "todos concluem" em 34% das partidas com 4 PE. A IA daqui chega a 65%, porque é mais competente que a estratégia simples usada no manual.

## Resultado principal (v0.4 como está no manual)

| jogadores | conclui (indiv.) | todos concluem | coop vence | eliminados | PS médio | empate no topo | Δ assentos | Δ arquétipos |
|---|---|---|---|---|---|---|---|---|
| 2 | 94% | 89% | 91% | 5% | 8,9 | 8% | 3 p.p. | 16 p.p. |
| 3 | 93% | 79% | 85% | 6% | 8,6 | 14% | 6 p.p. | 14 p.p. |
| 4 | 91% | 66% | 74% | 7% | 8,1 | 15% | **12 p.p.** | 14 p.p. |

*Δ = diferença, em pontos percentuais (p.p.), entre o assento ou arquétipo que mais vence e o que menos vence.*

### O que funciona
- **Economia coerente.** Comida, água e madeira do mapa bastam, e o gargalo muda ao longo da partida: água na semana 1, comida na semana 3, madeira no fim. Quase ninguém fica sem PE para fazer nada; a IA desperdiçou menos de 0,3 PE por partida.
- **A duração bate com a meta.** São 36 vezes de 4 ações com 4 pessoas, perto de 45–60 min com pessoas experientes.
- **Empates** no topo em 8–15% das partidas, que o desempate resolve.
- **Não há estratégia degenerada óbvia.** No torneio de estilos (`estilos.py`), o jogo equilibrado venceu 37%. Explorar demais foi claramente pior (12% de vitória, só 66% concluem), e ser cauteloso ou arrojado com o risco ficou no meio.

### Problemas encontrados

1. **Fácil demais.** Cerca de 90% concluem, bem acima da meta de 60–70%.

2. **A energia (PE) é um degrau, não um ajuste fino.** Com 3 PE, cerca de 50% concluem e 40% são eliminados; com 4 PE, 90% concluem; com 5 PE, 99%. Mexer na PE global não chega na meta.

3. **Vantagem de assento com 4 jogadores.** O 3º e o 4º a jogar vencem 29–31% das vezes; o 1º e o 2º, só 20%. Testei a causa isolando cada fator:
   - trocar a rotação por ordem serpente ou catch-up **não mudou nada**, nem remover o limite de coleta;
   - com ordem **aleatória a cada rodada**, todos ficam em 25%;
   - **invertendo só a rodada 1**, a vantagem troca de lado.

   **Causa:** quem joga por último na rodada 1 vê o que os outros revelaram em volta do Início. Vai direto aos recursos certos e usa os Eventos com mais eficiência. A vantagem vira mais revelações e mais comida na semana 3.

4. **O Sobrevivencialista é o arquétipo mais fraco.** Vence 0,66–0,86× a taxa justa. A habilidade só evita a Exaustão do dado de risco, que acontece cerca de 0,35 vez por partida. As outras habilidades dão +1 recurso por semana, garantido.

5. **A sorte pesa bastante para um público gamer.**
   - quem tira 2 Eventos ruins (Atraso, Cansaço, Vazamento) vence 14% das vezes; com nenhum, 39%;
   - uma Exaustão pelo dado de risco derruba a chance de vitória de 33% para 22%.

6. **A pontuação tem pouca variedade.** Na prática, PS ≈ 3 × semanas pagas − 2 × Exaustões; sobras e itens somam cerca de 2 pontos. Quem vence é quem evita azar, não quem escolhe um caminho de pontuação diferente.

7. **O cooperativo quase não tem cooperação.** A vitória no coop fica perto da taxa "todos concluem" do competitivo (74% contra 66% com 4 pessoas; com as regras propostas, 31% contra 29%). Transferir exige estar no mesmo tile e gastar 1 PE, e só move recursos. Na prática, o coop vira "4 partidas solo em que todos precisam acertar", e a dificuldade despenca com mais jogadores (≈ p^n). Parte disso pode ser limitação da IA cooperativa.

## Variantes testadas (4 jogadores, resumo)

| variante | conclui | coop | Δ assentos | observação |
|---|---|---|---|---|
| v0.4 | 91% | 74% | 12 p.p. | |
| 3 PE | 49% | 3% | 12 | brutal, 39% eliminados |
| 5 PE | 99% | 99% | 13 | sem tensão |
| ordem serpente | 91% | 74% | 12 | não resolve assento |
| ordem catch-up | 91% | 77% | 12 | não resolve assento |
| ordem aleatória | — | — | **0** | confirma a causa (rodada 1) |
| vizinhos do Início revelados | 90% | — | 6 | resolve a maior parte |
| vizinhos revelados + serpente | 90% | — | **4** | quase zera |
| reposição +1 comida/semana | 91% | 79% | 11 | fica mais fácil |
| água 1/2/2 | 85% | 57% | 11 | |
| semana 3 = 4 comidas | 87% | 65% | 10 | |
| Exaustão elimina em 2 | 75% | 36% | 9 | eliminação de 22% (punitivo) |
| **com Exaustão, recebe 3 PE** | **~70%** | ~20–50% | — | acerta a meta, com efeito de "espiral" temático |

Efeito colateral da regra "Exaustão tira 1 PE": o **Caçador** despenca (0,65×), porque a habilidade o empurra para os tiles de risco. Dar a ele imunidade total ao risco foi exagero (1,6×). Falhar só com o resultado 1 ficou equilibrado.

## Proposta v0.5 (testada)

1. **Os 6 vizinhos do Início começam revelados**, com as fichas colocadas e sem comprar Evento. Corrige a vantagem de assento e deixa a abertura menos cega.
2. **Ordem serpente**: 1-2-3-4, depois 4-3-2-1, e o primeiro jogador avança a cada duas rodadas.
3. **Exaustão cansa**: quem tem 1 ou mais Exaustões recebe **3 PE** em vez de 4. É o ajuste de dificuldade, e dá peso real à ação Descansar.
4. **Caçador**: no dado de risco dos tiles da habilidade dele, só o resultado **1** dá Exaustão.
5. **Construtor**: começa com **1 madeira**.
6. **Sobrevivencialista**: uma vez por semana, ignore **uma Exaustão de qualquer fonte**, exceto a Prova Semanal com as duas categorias em falta.

   *No simulador, a habilidade vale para dado, Evento e Prova.*

| jogadores | conclui | todos concluem | coop vence | eliminados | PS médio | empate | Δ assentos | Δ arquétipos |
|---|---|---|---|---|---|---|---|---|
| 2 | 78% | 60% | 60% | 12% | 9,0 | 4% | 0 p.p. | 9 p.p. |
| 3 | 77% | 44% | 44% | 12% | 8,8 | 9% | 2 p.p. | 11 p.p. |
| 4 | 75% | 29% | 31% | 12% | 8,5 | 12% | 4 p.p. | 13 p.p. |

Arquétipos com 4 jogadores (vitória ÷ taxa justa): Caçador 1,16 · Coletor 1,22 · Pescador 0,93 · Construtor 0,84 · Sobrevivencialista 0,85. Antes a faixa era 0,57–1,40.

A IA conclui em ~75%. Pessoas cometem mais erros de rota que a IA, então a taxa real deve ficar na faixa de 60–70% que você quer. Confirme em mesa.

## O que ainda precisa de trabalho (não testado)

- **Cooperativo com a mesma dificuldade para 2 e 4 jogadores.** Hoje a chance de vitória cai muito com mais gente. Ideias:
  - **abrigo compartilhado**: duas pessoas no mesmo abrigo nível 3 dividem o custo;
  - Transferir entre tiles adjacentes;
  - "o grupo vence se até 1 pessoa desistir, com penalidade".
- **Mais caminhos de pontuação para gamers.** Por exemplo:
  - pontos de "audiência" por revelar tiles, arriscar e ajudar alguém;
  - objetivos secretos por arquétipo.

  Isso cria dilemas entre segurança e pontos. Hoje o PS mede basicamente "quem teve menos azar".
- **Menos variância nos Eventos.** Trocar Cansaço/Vazamento por escolhas ("perca 1 água OU 1 PE") mantém a tensão e tira parte da sorte pura.
- **Interação.** Os dados mostram só uma corrida indireta: tiles finitos e uma coleta por rodada. Se quiser mais conflito, cartas de "edição do programa" (câmera, tempestade no tile de alguém) seriam o lugar natural.

## Pontos do manual que ficaram ambíguos (e como o simulador interpretou)

1. Panela ou Cantil completando o pagamento contam como semana "integralmente paga" (+3 PS)? **Assumido: sim.**
2. Descansar mais barato vale só no **próprio** abrigo? **Assumido: sim.**
3. Vários abrigos podem ocupar o mesmo tile? **Assumido: sim.**
4. Transferir "até dois recursos" podem ser de tipos diferentes? **Assumido: mesmo tipo.**
5. "Os 12 tiles mais próximos do Início": com empates de distância, quais contam? **Assumido: sorteio entre os empatados.**
6. Vale definir no manual se o mapa usa linhas pares ou ímpares deslocadas; a adjacência muda.

## Como rodar

```bash
cd simulador
python3 sim.py                  # métricas v0.4 para 2, 3 e 4 pessoas
python3 sim.py --v05            # mesmas métricas com a proposta
python3 sim.py --trace 4        # log completo de uma partida
python3 experimentos.py         # todas as variantes (demora alguns minutos)
python3 final.py                # v0.4 contra a proposta v0.5
python3 estilos.py              # torneio de estilos de jogo
```

Cada regra nova é um campo de `Config` em `sim.py`: `pe`, `week_food`, `week_water`, `order`, `exh_pe`, `reveal_ring1`, `restock`, `collect_limit`, `surv_mode`, `hunter_fail_faces`, `builder_start_wood` etc. Para testar uma ideia nova, basta criar uma entrada em `VARIANTS`.
