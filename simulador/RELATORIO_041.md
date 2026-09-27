# Análise por simulação — manual 0.4.1

Pedidos do autor para esta rodada:
- rodar sem a regra da comida estragando depois da Prova Semanal, com **limite de carga** de comida;
- meta de **~50% de conclusão** individual no competitivo e **~40% de vitória** no cooperativo, **iguais para 2, 3 e 4 jogadores**;
- das correções anteriores, manter **só a de Desgaste reduzindo PE** (com 1 Desgaste ou mais, a vez tem 3 PE);
- alavancas liberadas: exigências da Prova, Eventos, recursos do mapa e custos das ações.

## O simulador do 0.4.1

`sim041.py` foi reescrito para o manual novo:
- **Ações:** Mover e Explorar custam 1 PE cada; não dá para sair nem coletar em um tile oculto antes de explorá-lo.
- **Eventos:** as 18 cartas coletivas estão implementadas, uma por rodada da 2 à 9.
- **Itens:** cada pessoa começa com 1 Item.
- **Fogo:** o fogo tem custo, e a Prova tem o teste de água sem fogo.
- **Arquétipos:** os 7, incluindo Explorador e Guardião do Fogo.
- **Montagem:** Floresta e Rio no primeiro anel; Resgate entre 6 tiles do segundo anel.

A IA foi calibrada testando estilos diferentes; o mais competente explora bastante e constrói o abrigo perto do Resgate. Ela avalia os Eventos opcionais levando em conta que cada Desgaste custa 1 PE por vez pelo resto da partida. Também guarda 1 PE para pagar a Hipotermia.

**Cuidado ao ler os números:** a IA é um jogador razoável, não um humano. Pessoas planejam melhor alguns pontos, como a cooperação e o uso dos Eventos, e erram mais em outros, como rotas e contas. As comparações entre versões são mais confiáveis que os valores absolutos.

## O manual 0.4.1 como está (sem estragar comida)

| jogadores | competitivo: conclui | cooperativo: vence | eliminados (comp.) |
|---|---|---|---|
| 2 | 25% | 8% | 58% |
| 3 | 25% | 3% | 57% |
| 4 | 23% | 1% | 51% |

O 0.4.1 ficou **muito mais difícil** que o 0.4, onde ~90% concluíam. Três motivos:

1. **Explorar custa uma ação a mais.** Entrar num tile novo agora custa 2 PE.
2. **Revelar tiles não dá mais nada extra.** No 0.4, cada tile revelado comprava um Evento, que quase sempre trazia comida, água, madeira ou Item. Agora os Eventos coletivos são, em média, mais negativos que positivos.
3. **Desgaste reduzindo PE vira uma espiral.** Sem essa regra, a conclusão sobe de ~25% para ~40%.

As maiores fontes de Desgaste por pessoa são: falta de comida na Prova (1,1), falta de água (0,75), Eventos (0,65), risco (0,1) e água sem fogo (0,07).

### Eventos que mais causam Desgaste (média por pessoa, cada vez que a carta aparece)
- Cabeça podre de passarinho e Olho do jacaré: só quando a pessoa aceita; a IA aceita pouco.
- Abrigo em chamas: 0,47. Pune quem já construiu e está sem água.
- Hipotermia: 0,2 a 0,25. Pune quem não guardou PE nem acendeu o fogo.
- Desmaio sobre a fogueira, Picada na virilha e A planta errada: 0,15 a 0,2.

### Limite de carga de comida
Testei limites de 3, 4, 5, 6 e sem limite: **não muda nada** (diferença menor que 1 p.p.). A comida é tão escassa que ninguém acumula. **Recomendo limite de 4** só para evitar abusos em mesa, mas ele é opcional.

## Por que o cooperativo cai com mais jogadores

A equipe só vence se **todos** concluírem. Com a mesma dificuldade individual, a chance de vitória despenca com mais gente. Além disso, com 4 pessoas **falta madeira**:

| jogadores | madeira no mapa | madeira necessária (3 por pessoa) |
|---|---|---|
| 2 | 9 | 6 |
| 3 | 12 | 9 |
| 4 | 13 | 12 |

Com 4 pessoas, seria preciso coletar quase toda a madeira do mapa, inclusive a dos tiles escondidos. Mesmo com Prova quase vazia (comida 0/1/1, água 0/1/1), o cooperativo com 4 pessoas não passava de 36%, e a maior causa era abrigo incompleto.

## Proposta 0.4.2

### Para os dois modos
1. **Comida não estraga**; cada pessoa carrega no máximo **4 comidas**.
2. **Desgaste cansa**: com 1 Desgaste ou mais, a vez tem **3 PE**.
3. **Floresta = 3 madeiras** (era 2).
4. **Mapa de 4 pessoas: troque o Pasto por uma Clareira** (Clareira 6, Pasto 0).

### Prova Semanal — competitivo (igual para 2, 3 e 4 pessoas)

| semana | comida | água |
|---|---|---|
| 1 | 2 | 1 |
| 2 | 2 | 1 |
| 3 | 2 | 1 |

### Prova Semanal — cooperativo (por número de pessoas)

| pessoas | comida (sem. 1/2/3) | água (sem. 1/2/3) |
|---|---|---|
| 2 | 1 / 2 / 2 | 1 / 1 / 1 |
| 3 | 1 / 1 / 2 | 1 / 1 / 1 |
| 4 | 1 / 1 / 1 | 1 / 1 / 1 |

A lógica é simples: **no cooperativo, a comida pedida cai conforme o grupo cresce**, porque todos precisam sobreviver.

### Resultado (1.500 partidas por célula)

| jogadores | competitivo: conclui | cooperativo: vence | eliminados (comp.) | PS médio | empate |
|---|---|---|---|---|---|
| 2 | 52% | 45% | 31% | 6,6 | 3% |
| 3 | 54% | 46% | 29% | 6,7 | 5% |
| 4 | 54% | 44% | 24% | 7,3 | 8% |

- **Assentos:** diferença de no máximo 2 p.p. Com as novas regras de montagem e sem compra de Eventos ao explorar, a vantagem de assento do 0.4 sumiu.
- **Eliminações:** cerca de 2/3 acontecem na Prova final (rodada 9).
- **Sem a troca de Pasto por Clareira:** o competitivo fica igual, mas o cooperativo com 4 pessoas cai para 35%.

## Pontos de atenção

1. **Arquétipos desequilibrados.** Com 4 pessoas (vitória × n, média ~0,93):

   | arquétipo | vitória × n |
   |---|---|
   | Coletor | 1,30 |
   | Caçador | 1,05 |
   | Construtor | 1,01 |
   | Pescador | 0,91 |
   | Sobrevivencialista | 0,83 |
   | Explorador | 0,72 |
   | Guardião do Fogo | 0,67 |

   Guardião e Explorador rendem pouco:
   - o Guardião economiza ~3 PE de fogo por partida e protege um teste de água que só falha em ~7% das Provas;
   - o Explorador economiza 3 PE.

   As habilidades que dão +1 recurso escasso por semana valem mais. Ideias a testar:
   - Guardião compartilha o fogo com **todas** as pessoas no tile e ignora a Hipotermia e o Abrigo em chamas;
   - Explorador tem Mover grátis **duas vezes** por semana, ou Explorar grátis uma vez por semana.
2. **Eliminação alta no competitivo** (24–31%). Com gamers, verifique em mesa se a pessoa eliminada cedo fica entediada. Na simulação, ~1/3 das eliminações acontece antes da rodada 9.
3. **O cooperativo pode ficar mais fácil em mesa.** Pessoas combinam planos e dividem madeira melhor que a IA. Se passar de 50%, suba 1 comida na semana 3 da tabela do cooperativo.

## Pontos do manual 0.4.1 interpretados pelo simulador
1. "Seis espaços próximos ao primeiro anel": 6 casas sorteadas entre as do segundo anel.
2. Explorador: o Mover grátis é usado automaticamente no primeiro Mover da semana. Canoa pelo pântano tem prioridade.
3. Furacão: "começou a vez no tile do próprio abrigo" é verificado no início da vez.
4. Guardião: compartilha o fogo com a primeira pessoa sem fogo no mesmo tile que tenha água para pagar.
5. Rumo à extração: o tile olhado é sorteado entre os ocultos adjacentes.

## Como rodar

```bash
cd simulador
python3 sim041.py               # 0.4.1 como está (sem estragar), 2/3/4 pessoas
python3 sim041.py --trace 4     # log de uma partida
python3 ajuste041.py            # grade de dificuldade (competitivo e cooperativo)
python3 final041.py             # 0.4.1 x proposta 0.4.2
```
