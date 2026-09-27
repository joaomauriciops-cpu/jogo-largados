"""Conteúdo de todos os componentes do protótipo 0.5 (fonte única para o kit de impressão)."""

# ------------------------------------------------------------------ tiles
BIOMAS = {
    # tipo: (nome, cor de fundo, cor do texto, recursos, risco, contagem 2/3/4)
    'F': ('Floresta', '#2f6b3a', '#ffffff', {'madeira': 3}, False, (3, 4, 4)),
    'Ca': ('Cachoeira', '#2f7fb8', '#ffffff', {'agua': 3}, False, (2, 3, 4)),
    'Cl': ('Clareira', '#9cc56a', '#1f2a14', {'comida': 2, 'madeira': 1}, False, (3, 4, 6)),
    'P': ('Pântano', '#6b6a3a', '#ffffff', {'comida': 2, 'agua': 1}, True, (2, 3, 3)),
    'R': ('Rio', '#3aa3a0', '#ffffff', {'comida': 1, 'agua': 1}, False, (4, 4, 5)),
    'Ac': ('Área de caça', '#b0672c', '#ffffff', {'comida': 3}, True, (2, 3, 4)),
    'Re': ('Resgate', '#c8362f', '#ffffff', {}, False, (2, 2, 3)),
    'I': ('Início', '#7a7a70', '#ffffff', {}, False, (1, 1, 1)),
    'Pa': ('Pasto', '#e3d59a', '#3b3520', {}, False, (1, 1, 0)),
}
ORDEM_BIOMAS = ['I', 'Re', 'F', 'Ca', 'Cl', 'P', 'R', 'Ac', 'Pa']


def tiles():
    """Lista de (tipo, índice, jogadores que usam esta cópia)."""
    out = []
    for k in ORDEM_BIOMAS:
        cont = BIOMAS[k][5]
        for i in range(1, max(cont) + 1):
            usa = [n for n, c in zip((2, 3, 4), cont) if i <= c]
            out.append((k, i, usa))
    return out


# ---------------------------------------------------------------- eventos
FASES = {
    'Leve': ('#3f9e4d', 'Rodadas 2–3'),
    'Mista': ('#d19a2a', 'Rodadas 4–6 (coop: 4–7)'),
    'Dura': ('#c0392b', 'Rodadas 7–9 (coop: 8–9)'),
}

EVENTOS = [
    (1, 'O olho do jacaré', 'Mista', 'Na sua vez (opcional)',
     'Você pode gastar 1 PE para receber 2 comidas da reserva. Se aceitar, lance 1 d6: ímpar dá 1 Desgaste.',
     'Os olhos brilham na água. O jantar pode ser você.'),
    (2, 'Desmaio sobre a fogueira', 'Dura', 'Começo da vez',
     'Escolha: jogar com 1 PE a menos sem lançar o dado, ou jogar normalmente e lançar 1 d6 (ímpar dá 1 Desgaste).',
     'A fome bateu forte. Alguém segura a câmera?'),
    (3, 'Furacão', 'Mista', 'Durante a rodada',
     'Sua primeira ação Mover nesta rodada custa 2 PE. Se começou a vez no tile do próprio abrigo, custa 1 PE. Explorar continua custando mais 1 PE.',
     'Vento, chuva e nenhum guarda-chuva no contrato.'),
    (4, 'Hienas no estoque', 'Dura', 'Começo da vez',
     'Se tiver pelo menos 1 comida, escolha: descartar 1 comida ou jogar com 1 PE a menos. Sem comida, esta carta não te afeta.',
     'Você piscou. Elas não.'),
    (5, 'Picada na virilha', 'Dura', 'Começo da vez',
     'Lance 1 d6. Par: jogue com 1 PE a menos. Ímpar: descarte 1 comida ou receba 1 Desgaste (sem comida, receba o Desgaste).',
     'O lugar errado para um inseto certo.'),
    (6, 'Hipotermia', 'Dura', 'Fim da vez',
     'Se não estiver no tile do próprio abrigo e seu fogo estiver apagado, escolha: gastar 1 PE que sobrou, descartar 1 comida ou receber 1 Desgaste.',
     'A noite chegou antes do fogo.'),
    (7, 'Abrigo inundado', 'Mista', 'Durante a rodada',
     'Nesta rodada, Descansar no próprio abrigo custa 2 PE (mais 1 comida), em qualquer nível. O Desgaste removido continua dependendo do nível.',
     'Goteira é elogio.'),
    (8, 'Bananeira!', 'Leve', 'Na sua vez (opcional)',
     'Você pode gastar 1 PE para receber 2 comidas da reserva.',
     'Um cacho maduro. A produção adorou o close.'),
    (9, 'Poço de bagres', 'Leve', 'Na sua vez (opcional)',
     'Você pode gastar 2 PE para receber 1 comida e 1 água da reserva.',
     'Mãos na lama, peixe na mão.'),
    (10, 'Abrigo em chamas', 'Dura', 'Ao revelar',
     'Cada pessoa que já construiu abrigo escolhe: descartar 1 água ou receber 1 Desgaste (sem água, recebe o Desgaste). O abrigo e o fogo não mudam.',
     'A fogueira ficou perto demais do teto de palha.'),
    (11, 'Cabeça podre de passarinho', 'Mista', 'Na sua vez (opcional)',
     'Você pode receber 2 comidas da reserva e 1 Desgaste. Se recusar, nada acontece.',
     'Proteína é proteína. Seu estômago discorda.'),
    (12, 'A planta errada', 'Mista', 'Na sua vez (opcional)',
     'Você pode lançar 1 d6. Par: receba 2 comidas. Ímpar: receba 1 Desgaste. Se não arriscar, nada acontece.',
     'Parece comestível. Parece.'),
    (13, 'Canoa pelo pântano', 'Leve', 'Durante a rodada',
     'Sua primeira ação Mover nesta rodada não custa PE. Explorar um tile oculto ainda custa 1 PE.',
     'Um tronco oco vira transporte público.'),
    (14, 'Em busca de água', 'Leve', 'Na sua vez (opcional)',
     'Você pode gastar 1 PE para receber 1 água da reserva — 2 águas se estiver em Rio ou Cachoeira.',
     'Seguindo o som da água corrente.'),
    (15, 'Rumo à extração', 'Leve', 'Na sua vez',
     'Olhe secretamente 1 tile oculto adjacente. Se for Resgate, pode revelá-lo sem gastar PE e sem entrar nele; se não for, devolva-o oculto.',
     'Um helicóptero ao longe. Ou foi imaginação?'),
    (16, 'Tartaruga na armadilha', 'Leve', 'Na sua vez',
     'Depois da sua primeira coleta de comida nesta rodada, receba +1 comida da reserva.',
     'A armadilha de ontem finalmente funcionou.'),
    (17, 'Um jantar revigorante', 'Leve', 'Na sua vez (opcional)',
     'Uma vez, você pode descartar 1 comida para remover 1 Desgaste, sem gastar PE. Não conta como Descansar.',
     'Barriga cheia, ânimo renovado.'),
    (18, 'Abrigo em cúpula', 'Leve', 'Na sua vez (opcional)',
     'Uma vez, você pode Construir ou Melhorar sem gastar o PE da ação. Pague 1 madeira; respeite o limite do modo (Avançado 3, Sofá 2).',
     'Galhos curvados, técnica ancestral, zero pregos.'),
]

# ------------------------------------------------------------------ itens
ITENS = [
    ('Faca', 'Depois de coletar 1 comida em Pântano ou Área de caça, descarte a Faca para receber +1 comida da reserva.',
     'Afiada, pequena e a coisa mais valiosa da mochila.'),
    ('Panela', 'Numa Prova em que falta exatamente 1 comida, descarte a Panela: ela substitui essa comida e a categoria conta como paga.',
     'Um ensopado rende mais do que parece.'),
    ('Cantil', 'Numa Prova em que falta exatamente 1 água, descarte o Cantil: ele substitui essa água e a categoria conta como paga. No Avançado, sem fogo, faça o teste de água.',
     'Cada gole guardado é um dia a mais.'),
    ('Rede de pesca', 'Depois de coletar 1 comida no Rio, descarte a Rede para receber +1 comida da reserva.',
     'Paciência e um nó bem dado.'),
    ('Toldo', 'Depois de um resultado ímpar no teste de risco, descarte o Toldo para ignorar o Desgaste. Não protege do teste de água nem de Eventos.',
     'Uma lona entre você e o pior da natureza.'),
]

# -------------------------------------------------------------- arquétipos
ARQUETIPOS = [
    ('Caçador', 'Uma vez por semana, depois de coletar comida no Pântano ou na Área de caça, receba +1 comida da reserva.',
     'Rastros, paciência e um bom arremesso.', False),
    ('Coletor', 'Uma vez por semana, depois de coletar comida na Clareira, receba +1 comida da reserva.',
     'Sabe o que é fruta e o que é veneno.', False),
    ('Pescador', 'Uma vez por semana, depois de coletar comida no Rio, receba +1 comida da reserva.',
     'Onde há correnteza, há almoço.', False),
    ('Construtor', 'Uma vez por semana, depois de coletar madeira na Floresta ou na Clareira, receba +1 madeira da reserva.',
     'Três galhos e um cipó viram uma casa.', False),
    ('Sobrevivencialista', 'Uma vez por semana, ignore 1 Desgaste causado por teste de risco, por pagar água sem fogo ou por um Evento.',
     'Já passou por coisa pior. Muito pior.', False),
    ('Explorador', 'Uma vez por semana, Mova-se sem gastar PE. Também uma vez por semana, Explore sem gastar PE. Os dois usos são independentes.',
     'Sempre quer saber o que tem atrás da próxima árvore.', False),
    ('Guardião do Fogo', 'Seu fogo acende de graça no início das rodadas 1, 4 e 7. Na Prova, uma outra pessoa no seu tile pode usar seu fogo. Ignore Desmaio sobre a fogueira, Hipotermia e Abrigo em chamas.',
     'Pedra, graveto e muita teimosia.', True),
]

CORES_JOGADORES = [('Vermelho', '#d64545'), ('Azul', '#3a78c2'), ('Verde', '#3f9e4d'), ('Amarelo', '#e0b92c')]

ACOES = [
    ('Mover', '1 PE', 'Tile adjacente. Não sai de tile oculto antes de explorá-lo.'),
    ('Explorar', '1 PE', 'Vire o tile oculto onde está; ponha recursos e Risco.'),
    ('Coletar', '1 PE', '1 ficha do tile; ponha um Coletado.'),
    ('Construir', '1 PE + 1 madeira', 'Nível 0→1 onde está; demais níveis no seu abrigo. Acende o fogo.'),
    ('Acender fogo', '1 PE', 'Só no Avançado.'),
    ('Descansar', '2 PE + 1 comida', 'No abrigo: 1 PE. Abrigo 2+: tira até 2. 1×/semana.'),
    ('Transferir', '1 PE', 'Coop: até 2 fichas a alguém no seu tile.'),
]
