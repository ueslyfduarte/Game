import streamlit as st
from player import Player
from mapa_gerador import gerar_mundo, gerar_zumbis, get_loot_table
import pydeck as pdk
import random
import math

# ---------- Funções auxiliares ----------
def distance(x1, y1, x2, y2):
    return math.sqrt((x1-x2)**2 + (y1-y2)**2)

def get_relation(player_idx, other_idx):
    if player_idx == other_idx: return 'self'
    return st.session_state.player_relations.get(player_idx, {}).get(other_idx, 'ally')

def make_noise(radius, turns=1):
    st.session_state.action_noise[st.session_state.current_player_index] = {
        'radius': radius, 'turns_left': turns
    }

def update_visited(x, y):
    cx = int(x * 10)
    cy = int(y * 10)
    st.session_state.visited.add((cx, cy))

def is_visible(x, y):
    cx = int(x * 10)
    cy = int(y * 10)
    return (cx, cy) in st.session_state.visited

def diario(entrada):
    st.session_state.diary.append(f"Dia {st.session_state.day}: {entrada}")

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
if "action_noise" not in st.session_state:
    st.session_state.action_noise = {}
if "world" not in st.session_state:
    predios, ruas, pois = gerar_mundo()
    st.session_state.world = (predios, ruas, pois)
if "zombies" not in st.session_state:
    st.session_state.zombies = gerar_zumbis()
if "visited" not in st.session_state:
    st.session_state.visited = set()
if "day" not in st.session_state:
    st.session_state.day = 1

st.set_page_config(page_title="Cidade Silenciosa – 2.5D", layout="wide")
st.title("🏙️ Cidade Silenciosa – Mapa 2.5D Isométrico")

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

    # Atualizar visitado
    update_visited(x, y)

    # Sidebar
    with st.sidebar:
        st.subheader("👥 Grupo")
        for i, p in enumerate(st.session_state.players):
            rel = get_relation(atual, i)
            icone = "👉" if i == atual else ("🔵" if rel == 'ally' else "🔴")
            st.write(f"{icone} {p.name} (HP:{p.hp})")
        if st.button("Passar vez ➡️"):
            for idx in list(st.session_state.action_noise.keys()):
                st.session_state.action_noise[idx]['turns_left'] -= 1
                if st.session_state.action_noise[idx]['turns_left'] <= 0:
                    del st.session_state.action_noise[idx]
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

    # ---------- MAPA 2.5D (ISOMÉTRICO) ----------
    st.markdown("---")
    predios, ruas, _ = st.session_state.world

    # Aplica névoa de guerra: prédios escurecidos se não visitados e distantes
    predios_vis = []
    for b in predios:
        visivel = is_visible(b['x'], b['y']) or distance(x, y, b['x'], b['y']) < 0.3
        if visivel:
            cor = [120, 120, 120]       # cinza padrão
            if b['tipo'] == 'policial': cor = [70, 70, 180]
            elif b['tipo'] == 'medico': cor = [180, 70, 70]
        else:
            cor = [50, 50, 50]           # invisível = escuro
        predios_vis.append({**b, 'cor': cor})

    layer_predios = pdk.Layer(
        "ColumnLayer",
        data=predios_vis,
        get_position="[x, y]",
        get_elevation="altura",
        elevation_scale=25,
        radius=0.06,
        get_fill_color="cor",
        pickable=False,
        auto_highlight=False,
    )

    # Ruas (linhas suaves)
    linhas = [{'start': [r['x1'], r['y1']], 'end': [r['x2'], r['y2']]} for r in ruas]
    layer_ruas = pdk.Layer(
        "LineLayer",
        data=linhas,
        get_source_position="start",
        get_target_position="end",
        get_color="[180, 180, 180, 200]",
        get_width=2,
    )

    # Zumbis próximos (pontos pretos)
    zumbis_vis = [z for z in st.session_state.zombies if distance(x, y, z['x'], z['y']) < 0.3]
    layer_zumbis = pdk.Layer(
        "ScatterplotLayer",
        data=zumbis_vis,
        get_position="[x, y]",
        get_radius=0.02,
        radius_scale=20,
        get_fill_color="[0, 0, 0, 220]",
    )

    # Jogador atual (esfera verde)
    layer_jogador = pdk.Layer(
        "ScatterplotLayer",
        data=[{'x': x, 'y': y, 'cor': [0, 255, 0]}],
        get_position="[x, y]",
        get_radius=0.06,
        radius_scale=25,
        get_fill_color="cor",
    )

    # Outros jogadores
    outros = []
    for i, p in enumerate(st.session_state.players):
        if i != atual:
            px, py = st.session_state.player_positions[i]
            rel = get_relation(atual, i)
            cor = [0, 0, 255] if rel == 'ally' else [255, 0, 0]
            outros.append({'x': px, 'y': py, 'cor': cor})
    layer_outros = pdk.Layer(
        "ScatterplotLayer",
        data=outros,
        get_position="[x, y]",
        get_radius=0.06,
        radius_scale=25,
        get_fill_color="cor",
    )

    # Configuração da câmera ISOMÉTRICA (2.5D)
    view_state = pdk.ViewState(
        longitude=x,
        latitude=y,
        zoom=12,
        pitch=60,          # inclinação isométrica
        bearing=45,        # giro diagonal
    )

    deck = pdk.Deck(
        layers=[layer_predios, layer_ruas, layer_zumbis, layer_jogador, layer_outros],
        initial_view_state=view_state,
        map_style=None,                     # sem mapa real!
        parameters={"clearColor": [20, 20, 20, 255]}  # fundo escuro
    )
    st.pydeck_chart(deck, use_container_width=True)

    # Verificar mortes
    for i, p in enumerate(st.session_state.players):
        if not p.is_alive():
            st.error(f"💀 {p.name} morreu!")
