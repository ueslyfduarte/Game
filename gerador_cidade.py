import json
import random

# ================= CONFIG =================
TAMANHO_QUARTEIRAO = 8
LARGURA_RUA = 2.5
NUM_QUARTEIRÕES = 10  # 10x10 = 100 quarteirões
NUM_ZUMBIS = 25000

TIPOS_PREDIO = {
    "casa":    {"peso": 50, "altura": (2, 4), "cor": "#f4d03f"},
    "apartamento": {"peso": 25, "altura": (6, 12), "cor": "#85c1e9"},
    "mercado": {"peso": 10, "altura": (4, 6), "cor": "#f1948a"},
    "escola":  {"peso": 8,  "altura": (5, 8), "cor": "#82e0aa"},
    "hospital":{"peso": 5,  "altura": (8, 15), "cor": "#ffffff"},
    "igreja":  {"peso": 2,  "altura": (10, 20), "cor": "#d7bde2"},
}

# Tipos de interações (5 por prédio)
INTERACOES_BASE = [
    {"tipo": "loot", "desc": "Você encontra uma lata de comida enlatada e um pouco de munição."},
    {"tipo": "zumbi", "desc": "2 zumbis estão escondidos atrás da porta! Rolagem de combate."},
    {"tipo": "safe", "desc": "O local está silencioso. Você pode descansar por algumas horas."},
    {"tipo": "trap", "desc": "Uma armadilha de arame farpado se rompe! Você sofre ferimentos."},
    {"tipo": "npc", "desc": "Um sobrevivente ferido pede ajuda. Ele oferece um mapa em troca."},
    {"tipo": "loot_arma", "desc": "Você encontra uma pistola 9mm com 3 balas."},
    {"tipo": "horda", "desc": "Uma horda de 5 zumbis está no quintal! Fuja ou lute."},
    {"tipo": "medicina", "desc": "Kit de primeiros socorros encontrado. +10 de vida."},
]

def escolher_tipo():
    tipos_lista = []
    for t, d in TIPOS_PREDIO.items():
        tipos_lista.extend([t] * d["peso"])
    return random.choice(tipos_lista)

def gerar_interacoes(seed):
    random.seed(seed)  # Para ser consistente por prédio
    num = random.randint(4, 6)  # entre 4 e 6 interações
    return random.sample(INTERACOES_BASE, num)

# ================= GERAR PRÉDIOS =================
predios = []
id_counter = 0
limites_quarteiroes = []  # para colocar zumbis nas ruas

for qx in range(NUM_QUARTEIRÕES):
    for qz in range(NUM_QUARTEIRÕES):
        base_x = qx * (TAMANHO_QUARTEIRAO + LARGURA_RUA) + LARGURA_RUA
        base_z = qz * (TAMANHO_QUARTEIRAO + LARGURA_RUA) + LARGURA_RUA
        limites_quarteiroes.append((base_x, base_z))  # canto inferior esquerdo

        num_predios = random.randint(4, 12)
        for _ in range(num_predios):
            tipo = escolher_tipo()
            dados = TIPOS_PREDIO[tipo]
            
            offset_x = random.uniform(0.5, TAMANHO_QUARTEIRAO - 0.5)
            offset_z = random.uniform(0.5, TAMANHO_QUARTEIRAO - 0.5)
            
            largura = random.uniform(0.8, 2.0)
            profundidade = random.uniform(0.8, 2.0)
            altura = random.uniform(*dados["altura"])
            
            interacoes = gerar_interacoes(id_counter)
            
            predios.append({
                "id": id_counter,
                "x": round(base_x + offset_x, 2),
                "z": round(base_z + offset_z, 2),
                "largura": round(largura, 2),
                "profundidade": round(profundidade, 2),
                "altura": round(altura, 2),
                "tipo": tipo,
                "cor": dados["cor"],
                "interacoes": interacoes,
                "nome": f"{tipo.capitalize()} {id_counter}"
            })
            id_counter += 1

# ================= GERAR ZUMBIS (nas ruas) =================
zumbis = []
for _ in range(NUM_ZUMBIS):
    # Escolhe um quarteirão aleatório
    qx = random.randint(0, NUM_QUARTEIRÕES - 1)
    qz = random.randint(0, NUM_QUARTEIRÕES - 1)
    base_x = qx * (TAMANHO_QUARTEIRAO + LARGURA_RUA)
    base_z = qz * (TAMANHO_QUARTEIRAO + LARGURA_RUA)
    
    # Decide se coloca na rua horizontal (entre quarteirões) ou vertical
    # 60% de chance de estar na rua, 40% nos cantos/calçadas
    if random.random() < 0.6:
        # Rua horizontal (eixo X variável, Z fixo na borda)
        x = random.uniform(base_x, base_x + TAMANHO_QUARTEIRAO + LARGURA_RUA)
        if random.random() < 0.5:
            z = base_z - random.uniform(0.5, LARGURA_RUA - 0.5)  # rua de baixo
        else:
            z = base_z + TAMANHO_QUARTEIRAO + random.uniform(0.5, LARGURA_RUA - 0.5)  # rua de cima
    else:
        # Rua vertical (eixo Z variável, X fixo na borda)
        z = random.uniform(base_z, base_z + TAMANHO_QUARTEIRAO + LARGURA_RUA)
        if random.random() < 0.5:
            x = base_x - random.uniform(0.5, LARGURA_RUA - 0.5)
        else:
            x = base_x + TAMANHO_QUARTEIRAO + random.uniform(0.5, LARGURA_RUA - 0.5)
    
    zumbis.append({
        "x": round(x, 2),
        "z": round(z, 2),
        "offset_y": random.uniform(0, 0.5)  # pequena variação de altura
    })

# ================= SALVAR =================
dados_completos = {
    "predios": predios,
    "zumbis": zumbis,
    "config": {
        "num_predios": len(predios),
        "num_zumbis": len(zumbis)
    }
}

with open("cidade_rpg.json", "w") as f:
    json.dump(dados_completos, f, indent=2)

print(f"Cidade gerada: {len(predios)} prédios e {len(zumbis)} zumbis!")
