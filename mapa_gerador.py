import random

# Definições de armas para loot
ARMAS_BRANCAS = [
    {"nome": "Faca de cozinha", "dano": (4, 8), "peso": 0.5, "raridade": "comum"},
    {"nome": "Cano de ferro", "dano": (6, 12), "peso": 2.0, "raridade": "comum"},
    {"nome": "Machado de bombeiro", "dano": (10, 18), "peso": 3.0, "raridade": "incomum"},
    {"nome": "Pé de cabra", "dano": (8, 14), "peso": 2.5, "raridade": "incomum"},
    {"nome": "Katana", "dano": (15, 25), "peso": 1.5, "raridade": "raro"},
    {"nome": "Serra elétrica", "dano": (20, 30), "peso": 5.0, "raridade": "raro"},
    {"nome": "Lança improvisada", "dano": (5, 10), "peso": 1.5, "raridade": "comum"},
    {"nome": "Taco de beisebol", "dano": (7, 13), "peso": 1.5, "raridade": "comum"},
    {"nome": "Marreta", "dano": (12, 20), "peso": 4.0, "raridade": "incomum"},
    {"nome": "Espada de treino", "dano": (10, 16), "peso": 1.8, "raridade": "raro"}
]

ARMAS_FOGO = [
    {"nome": "Pistola 9mm", "calibre": "9mm", "dano": (10, 16), "pente": 15, "peso": 1.0, "raridade": "comum"},
    {"nome": "Revólver .38", "calibre": ".38", "dano": (12, 18), "pente": 6, "peso": 1.2, "raridade": "comum"},
    {"nome": "Pistola .45", "calibre": ".45", "dano": (14, 20), "pente": 8, "peso": 1.1, "raridade": "incomum"},
    {"nome": "Espingarda 12ga", "calibre": "12ga", "dano": (18, 30), "pente": 5, "peso": 3.5, "raridade": "comum"},
    {"nome": "Carabina .22", "calibre": ".22", "dano": (8, 14), "pente": 10, "peso": 2.5, "raridade": "comum"},
    {"nome": "Rifle de caça .308", "calibre": ".308", "dano": (20, 35), "pente": 5, "peso": 3.0, "raridade": "incomum"},
    {"nome": "Submetralhadora 9mm", "calibre": "9mm", "dano": (12, 20), "pente": 25, "peso": 3.0, "raridade": "raro"},
    {"nome": "Rifle de assalto 5.56mm", "calibre": "5.56mm", "dano": (22, 35), "pente": 30, "peso": 3.5, "raridade": "raro"},
    {"nome": "Rifle sniper .50", "calibre": ".50", "dano": (40, 60), "pente": 5, "peso": 6.0, "raridade": "extremamente raro"},
    {"nome": "Escopeta automática", "calibre": "12ga", "dano": (20, 35), "pente": 8, "peso": 4.0, "raridade": "raro"}
]

MUNICOES = {
    "9mm": {"peso": 0.01},
    ".38": {"peso": 0.015},
    ".45": {"peso": 0.02},
    "12ga": {"peso": 0.05},
    ".22": {"peso": 0.005},
    ".308": {"peso": 0.03},
    "5.56mm": {"peso": 0.012},
    ".50": {"peso": 0.06}
}

def gerar_mundo():
    predios = []
    ruas = []
    pois = []
    # Ruas: grade de 100x100 (10 km)
    for i in range(0, 101, 2):
        x = i * 0.1
        ruas.append({'x1': x, 'y1': 0, 'x2': x, 'y2': 10})
    for j in range(0, 101, 2):
        y = j * 0.1
        ruas.append({'x1': 0, 'y1': y, 'x2': 10, 'y2': y})

    # Tipos de prédios com pesos
    tipos = (
        ['residencial'] * 40 +
        ['comercial'] * 25 +
        ['industrial'] * 15 +
        ['medico'] * 5 +
        ['policial'] * 3 +
        ['escola'] * 7 +
        ['restaurante'] * 5
    )
    # Gera 3000 prédios
    for _ in range(3000):
        x = random.uniform(0.2, 9.8)
        y = random.uniform(0.2, 9.8)
        # Altura varia conforme região (centro mais alto)
        if 3 <= y <= 7:
            altura = random.uniform(3, 12)
        else:
            altura = random.uniform(1, 5)
        tipo = random.choice(tipos)
        predios.append({'x': x, 'y': y, 'altura': altura, 'tipo': tipo})
        # 80% viram pontos de interesse acessíveis
        if random.random() < 0.8:
            # Define tier baseado na latitude (y)
            if y < 3:
                tier = 1   # sul (fazendas)
            elif y < 7:
                tier = 2   # centro
            else:
                tier = 3   # norte (zona de quarentena)
            pois.append({
                'id': len(pois),
                'x': x,
                'y': y,
                'tipo': tipo,
                'tier': tier,
                'looted': False
            })
    return predios, ruas, pois

def gerar_zumbis():
    zumbis = []
    for _ in range(25000):
        # distribuição: sul (0-3) 10%, centro (3-7) 60%, norte (7-10) 30%
        r = random.random()
        if r < 0.1:
            y = random.uniform(0, 3)
        elif r < 0.7:
            y = random.uniform(3, 7)
        else:
            y = random.uniform(7, 10)
        x = random.uniform(0, 10)
        zumbis.append({'x': x, 'y': y})
    return zumbis

# Tabelas de loot por tipo de prédio e tier (probabilidades cumulativas)
def get_loot_table(tipo, tier):
    """Retorna uma lista de (item, probabilidade) onde a soma das probabilidades é a chance total de encontrar algo."""
    # Itens comuns a todos
    base = []
    if tipo == 'residencial':
        base = [
            ("Lata de feijão", 0.08),
            ("Lata de sardinha", 0.08),
            ("Garrafa de água (500ml)", 0.10),
            ("Bandagem", 0.05),
            ("Revista velha", 0.15),
            ("Roupas velhas", 0.10),
            ("Pilhas", 0.05)
        ]
    elif tipo == 'comercial':
        base = [
            ("Lata de atum", 0.07),
            ("Macarrão instantâneo", 0.08),
            ("Refrigerante", 0.07),
            ("Garrafa de água (1L)", 0.06),
            ("Pão mofado", 0.10),
            ("Fósforos", 0.10),
            ("Mochila pequena", 0.03)
        ]
    elif tipo == 'industrial':
        base = [
            ("Ferramenta multiuso", 0.05),
            ("Corda", 0.08),
            ("Luvas de trabalho", 0.06),
            ("Gasolina (1L)", 0.04),
            ("Peça de metal", 0.10),
            ("Lata de comida enlatada", 0.05)
        ]
    elif tipo == 'medico':
        base = [
            ("Bandagem esterilizada", 0.10),
            ("Antibiótico", 0.03),
            ("Analgésico", 0.08),
            ("Soro fisiológico", 0.06),
            ("Luvas cirúrgicas", 0.05)
        ]
    elif tipo == 'policial':
        base = [
            ("Coldre vazio", 0.10),
            ("Algemas", 0.12),
            ("Colete leve", 0.03),
            ("Rádio quebrado", 0.08)
        ]
    elif tipo == 'escola':
        base = [
            ("Livro didático", 0.10),
            ("Mochila escolar", 0.04),
            ("Lápis e papel", 0.12),
            ("Garrafa de água", 0.06),
            ("Lanche vencido", 0.08)
        ]
    elif tipo == 'restaurante':
        base = [
            ("Lata de óleo", 0.07),
            ("Pacote de arroz", 0.06),
            ("Tempero", 0.10),
            ("Garrafa de vinho", 0.04),
            ("Comida pronta (estragada)", 0.08)
        ]

    # Adiciona armas de fogo e brancas conforme tier (apenas em certos locais)
    armas_extras = []
    if tipo in ('residencial', 'comercial') and tier >= 2:
        armas_extras.append(("Faca de cozinha", 0.02))
    if tipo == 'policial':
        if tier >= 2:
            armas_extras += [
                ("Pistola 9mm", 0.01),
                ("Munição 9mm", 0.03),
                ("Revólver .38", 0.005)
            ]
        if tier == 3:
            armas_extras += [
                ("Espingarda 12ga", 0.005),
                ("Munição 12ga", 0.01)
            ]
    if tipo == 'industrial' and tier >= 2:
        armas_extras.append(("Machado de bombeiro", 0.01))
    if tipo == 'medico' and tier == 3:
        armas_extras.append(("Kit cirúrgico", 0.01))
    if tipo == 'escola' and tier == 3:
        armas_extras.append(("Faca de cozinha", 0.01))

    # Combina listas
    tabela = base + armas_extras
    # Ajusta probabilidades para que a soma total não ultrapasse 1.0 (100%)
    total_chance = sum(p for _, p in tabela)
    if total_chance > 0.6:  # limite máximo de chance de achar algo (60% no máximo)
        fator = 0.6 / total_chance
        tabela = [(item, p * fator) for item, p in tabela]
    return tabela
