import streamlit as st
from player import Player
from mapa_gerador import gerar_mundo, gerar_zumbis, get_loot_table
from PIL import Image, ImageDraw
import random
import math

# ---------- Configurações da imagem do mapa ----------
MAP_SIZE = 1000          # pixels (quadrado)
KM = 100                 # pixels por km (10 km = 1000 px)
BUILDING_RADIUS = 3      # tamanho dos prédios na imagem

# ---------- Funções auxiliares ----------
def distance(x1, y1, x2, y2):
    return math.sqrt((x1-x2)**2 + (y1-y2)**2)

def get_relation(player_idx, other_idx):
    if player_idx == other_idx: return 'self'
    return st.session_state.player_relations.get(player_idx, {}).get(other_idx, 'ally')

def diario(entrada):
    st.session_state.diary.append(f"Dia {st.session_state.day}: {entrada}")

def world_to_pixel(x, y):
    """Converte coordenadas do mundo (0-10) para pixels (0-MAP_SIZE)."""
    px = int(x * KM)
    py = int(y * KM)
    return px, py

# ---------- Inicialização de estado ----------
if "players" not in st.session_state:
    st.session_state.players = []
if "player_positions" not in st.session_state:
    st.session_state.player_positions = {}
if "current_player_index" not in st.session_state:
    st.session_state.current_player_index = 0
if "diary" not in st.session_state:
    st.session_state.diary = []
if "player_relations" not in st.session_state:
    st.session_state.player_relations = {}
if "world" not in st.session_state:
    predios, ruas, pois = gerar_mundo()
    st.session_state.world = (predios, ruas, pois)
if "zombies" not in st.session_state:
    st.session_state.zombies = gerar_zumbis()
if "visited" not in st.session_state:
    st.session_state.visited = set()
if "day" not in st.session_state:
    st.session_state.day = 1

st.set_page_config(page_title="Cidade Silenciosa – Mapa Tático", layout="wide")
st.title("🏙️ Cidade Silenciosa – Mapa da Cidade")

# ---------- Tela de criação de grupo ----------
if len(st.session_state.players) == 0:
    st.subheader("Forme seu grupo de sobreviventes")
    nome = st.text_input("Nome do sobrevivente:", key="new")
    if st.button("Adicionar ao grupo"):
        if nome:
            idx = len(st.session_state.players)
            p = Player(nome)
            st.session_state.players.append(p)
            st.session_state.player_positions[idx] = (5.0, 0.5)  # sul
            for i in range(idx):
                st.session_state.player_relations.setdefault(i, {})[idx] = 'ally'
                st.session_state.player_relations.setdefault(idx, {})[i] = 'ally'
            diario(f"{nome} se junta ao grupo no sul da cidade.")
            st.rerun()
    if len(st.session_state.players) > 0:
        if st.button("Iniciar jornada"):
            st.session_state.current_player_index = 0
            st.rerun()
else:
    # ---------- Jogo em andamento ----------
    total = len(st.session_state.players)
    atual = st.session_state.current_player_index
    jogador = st.session_state.players[atual]
    x, y = st.session_state.player_positions[atual]

    # Sidebar
    with st.sidebar:
        st.subheader("👥 Grupo")
        for i, p in enumerate(st.session_state.players):
            rel = get_relation(atual, i)
            icone = "👉" if i == atual else ("🔵" if rel == 'ally' else "🔴")
            st.write(f"{icone} {p.name} (HP:{p.hp})")
        if st.button("Passar vez ➡️"):
            st.session_state.current_player_index = (atual + 1) % total
            st.rerun()
        st.markdown("---")
        st.subheader("🤝 Relações")
        for i, p in enumerate(st.session_state.players):
            if i != atual:
                rel = get_relation(atual, i)
                nova = st.radio(f"Com {p.name}", ['ally','enemy'], index=0 if rel=='ally' else 1, key=f"rel_{i}")
                if nova != rel:
                    st.session_state.player_relations.setdefault(atual, {})[i] = nova
                    st.session_state.player_relations.setdefault(i, {})[atual] = nova
                    diario(f"{jogador.name} agora é {'aliado' if nova=='ally' else 'inimigo'} de {p.name}.")
                    st.rerun()

    # Painel do personagem
    st.header(f"Dia {st.session_state.day} – Vez de {jogador.name}")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("❤️ HP", f"{jogador.hp}/{jogador.max_hp}")
        st.metric("⚡ Stamina", f"{jogador.stamina}/{jogador.max_stamina}")
        st.metric("🎒 Peso", f"{jogador.current_weight:.1f}/{jogador.max_weight} kg")
    with col2:
        st.metric("🍖 Fome", f"{jogador.hunger}/100")
        st.metric("💧 Sede", f"{jogador.thirst}/100")
    with col3:
        st.metric("🦠 Infecção", f"{jogador.infection}/100")
        st.metric("🌡️ Temp", f"{jogador.temperature}/100")
    with col4:
        st.write("**Habilidades**")
        for sk, val in jogador.skills.items():
            st.text(f"{sk}: {val}")
        arma = jogador.equipped_weapon['nome'] if jogador.equipped_weapon else "Desarmado"
        st.write(f"**Arma:** {arma}")

    # Abas: Inventário / Diário
    tab1, tab2 = st.tabs(["🎒 Inventário", "📜 Diário"])
    with tab1:
        if not jogador.inventory:
            st.write("Vazio.")
        else:
            for item in jogador.inventory:
                st.write(f"{item['nome']} x{item['quantidade']} ({item['tipo']}, {item['peso']}kg)")
        st.write("---")
        st.write("**Usar item:**")
        itens_nomes = [item['nome'] for item in jogador.inventory]
        if itens_nomes:
            item_escolhido = st.selectbox("Item:", itens_nomes)
            if st.button("Usar"):
                for it in jogador.inventory:
                    if it['nome'] == item_escolhido:
                        tipo = it['tipo']
                        if tipo == 'comida':
                            jogador.eat(25, 'bom')
                            diario(f"{jogador.name} comeu {item_escolhido}.")
                        elif tipo == 'água':
                            jogador.drink(40, 'limpa')
                            diario(f"{jogador.name} bebeu {item_escolhido}.")
                        elif tipo == 'medicamento':
                            jogador.treat_infection(40)
                            diario(f"{jogador.name} usou {item_escolhido}.")
                        elif tipo in ('arma_branca', 'arma_fogo'):
                            jogador.equipped_weapon = it
                            diario(f"{jogador.name} equipou {item_escolhido}.")
                        else:
                            st.warning("Item não utilizável.")
                            break
                        jogador.remove_item(item_escolhido, 1)
                        st.rerun()
        else:
            st.write("Nenhum item para usar.")

    with tab2:
        for msg in reversed(st.session_state.diary[-30:]):
            st.write(msg)

    # Ações principais
    st.subheader("Ações")
    cA, cB, cC = st.columns(3)
    with cA:
        if st.button("⚔️ Atacar (8 ST)"):
            if jogador.stamina < 8:
                st.warning("Sem estamina!")
            else:
                custo = jogador.use_stamina(8, 'direct')
                dano = jogador.get_attack_damage()
                zumbi_perto = False
                for z in st.session_state.zombies:
                    if distance(x, y, z['x'], z['y']) < 0.05:
                        zumbi_perto = True
                        break
                if zumbi_perto:
                    jogador.take_damage(5, reason="zumbi")
                    diario(f"{jogador.name} ataca um zumbi causando {dano} de dano, mas sofre um arranhão.")
                else:
                    diario(f"{jogador.name} golpeia o ar. Nenhum zumbi por perto.")
                st.rerun()
        if st.button("🛡️ Defender (5 ST)"):
            if jogador.stamina < 5:
                st.warning("Sem estamina!")
            else:
                jogador.use_stamina(5, 'direct')
                diario(f"{jogador.name} fica em posição defensiva.")
                st.rerun()
    with cB:
        if st.button("💤 Descansar"):
            jogador.rest()
            st.session_state.day += 1
            diario(f"{jogador.name} descansa. Um novo dia amanhece.")
            if random.randint(1,3) == 1:
                jogador.degrade_skills()
            st.rerun()
    with cC:
        if st.button("🔍 Vasculhar área (5 ST)"):
            if jogador.stamina < 5:
                st.warning("Sem estamina!")
            else:
                jogador.use_stamina(5, 'other')
                pois = st.session_state.world[2]
                for poi in pois:
                    if not poi['looted'] and distance(x, y, poi['x'], poi['y']) < 0.03:
                        tabela = get_loot_table(poi['tipo'], poi['tier'])
                        total_chance = sum(p for _, p in tabela)
                        if total_chance == 0:
                            diario(f"{jogador.name} vasculha um(a) {poi['tipo']}, mas está vazio.")
                        else:
                            r = random.random() * total_chance
                            acum = 0
                            for item, prob in tabela:
                                acum += prob
                                if r <= acum:
                                    peso = 0.5
                                    if 'arma' in item.lower():
                                        peso = 2.0
                                    elif 'munição' in item.lower():
                                        peso = 0.1
                                    elif 'garrafa' in item.lower() or 'lata' in item.lower():
                                        peso = 0.3
                                    if jogador.add_item(item, 'diverso', 1, peso):
                                        diario(f"{jogador.name} encontra {item} em um(a) {poi['tipo']}.")
                                    else:
                                        diario(f"{jogador.name} encontra {item}, mas está sobrecarregado e não pode carregar.")
                                    break
                            else:
                                diario(f"{jogador.name} vasculha, mas não acha nada útil.")
                        poi['looted'] = True
                        st.rerun()
                diario(f"{jogador.name} não há nada para vasculhar nas proximidades.")
                st.rerun()

    # Movimentação
    st.subheader(f"Mover {jogador.name} (custa 2 ST)")
    cols_m = st.columns(4)
    passo = 0.1
    sem_st = jogador.stamina < 2
    with cols_m[0]:
        if st.button("⬆️ Norte", disabled=sem_st):
            jogador.use_stamina(2, 'other')
            st.session_state.player_positions[atual] = (x, min(9.9, y + passo))
            st.rerun()
    with cols_m[1]:
        if st.button("⬇️ Sul", disabled=sem_st):
            jogador.use_stamina(2, 'other')
            st.session_state.player_positions[atual] = (x, max(0.1, y - passo))
            st.rerun()
    with cols_m[2]:
        if st.button("➡️ Leste", disabled=sem_st):
            jogador.use_stamina(2, 'other')
            st.session_state.player_positions[atual] = (min(9.9, x + passo), y)
            st.rerun()
    with cols_m[3]:
        if st.button("⬅️ Oeste", disabled=sem_st):
            jogador.use_stamina(2, 'other')
            st.session_state.player_positions[atual] = (max(0.1, x - passo), y)
            st.rerun()

    # ---------- DESENHO DO MAPA DA CIDADE ----------
    st.markdown("---")
    st.subheader("🗺️ Mapa da Cidade")

    # Criar imagem base (fundo preto)
    img = Image.new('RGB', (MAP_SIZE, MAP_SIZE), color=(20, 20, 20))
    draw = ImageDraw.Draw(img)

    # Desenhar ruas
    predios, ruas, pois = st.session_state.world
    for r in ruas:
        x1, y1 = world_to_pixel(r['x1'], r['y1'])
        x2, y2 = world_to_pixel(r['x2'], r['y2'])
        draw.line([(x1, y1), (x2, y2)], fill=(80, 80, 80), width=1)

    # Desenhar prédios
    cores_tipo = {
        'residencial': (160, 160, 160),
        'comercial': (200, 200, 100),
        'industrial': (180, 140, 80),
        'medico': (220, 80, 80),
        'policial': (80, 80, 220),
        'escola': (100, 200, 100),
        'restaurante': (200, 150, 100)
    }
    for b in predios:
        px, py = world_to_pixel(b['x'], b['y'])
        cor = cores_tipo.get(b['tipo'], (150, 150, 150))
        draw.rectangle(
            [(px - BUILDING_RADIUS, py - BUILDING_RADIUS),
             (px + BUILDING_RADIUS, py + BUILDING_RADIUS)],
            fill=cor,
            outline=(50, 50, 50)
        )

    # Zumbis próximos
    for z in st.session_state.zombies:
        if distance(x, y, z['x'], z['y']) < 0.3:
            zx, zy = world_to_pixel(z['x'], z['y'])
            draw.ellipse([(zx-1, zy-1), (zx+1, zy+1)], fill=(0, 0, 0))

    # Outros jogadores
    for i, p in enumerate(st.session_state.players):
        if i != atual:
            px, py = world_to_pixel(*st.session_state.player_positions[i])
            rel = get_relation(atual, i)
            cor = (0, 0, 255) if rel == 'ally' else (255, 0, 0)
            draw.ellipse([(px-5, py-5), (px+5, py+5)], fill=cor, outline=(255, 255, 255))

    # Jogador atual
    px, py = world_to_pixel(x, y)
    draw.ellipse([(px-6, py-6), (px+6, py+6)], fill=(0, 255, 0), outline=(255, 255, 255), width=2)

    # Exibir imagem corrigida
    st.image(img, use_container_width=True, caption="Cidade Silenciosa – 10×10 km")

    # Verificar mortes
    for i, p in enumerate(st.session_state.players):
        if not p.is_alive():
            st.error(f"💀 {p.name} morreu!")
