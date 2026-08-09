import streamlit as st
from player import Player
from mapa_gerador import criar_mapa_base
import folium
from streamlit_folium import st_folium
import random
import math
import base64
from io import BytesIO

# ---------- Funções auxiliares ----------
def distance(pos1, pos2):
    return math.sqrt((pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2)

def get_relation(player_idx, other_idx):
    if player_idx == other_idx:
        return 'self'
    relations = st.session_state.player_relations.get(player_idx, {})
    return relations.get(other_idx, 'ally')

def make_noise(radius, turns=1):
    st.session_state.action_noise[st.session_state.current_player_index] = {
        'radius': radius,
        'turns_left': turns
    }

def gerar_zumbis(density):
    zombies = []
    num = density * 3
    for _ in range(num):
        regiao = random.choices(
            ['sul', 'centro', 'norte'],
            weights=[0.1, 0.5, 0.4]
        )[0]
        if regiao == 'sul':
            lat = random.uniform(0, 1)
            lon = random.uniform(0.4, 1.0)   # sul
        elif regiao == 'centro':
            lat = random.uniform(0, 1)
            lon = random.uniform(0.85, 0.4)  # centro
        else:
            lat = random.uniform(0, 1)
            lon = random.uniform(0, 0.85)    # norte
        zombies.append([lat, lon])
    return zombies

def gerar_pois():
    pois = []
    # POIs normais (800) – no centro (lat 0.4 a 0.85, lon 0.15 a 0.85)
    for _ in range(800):
        lat = random.uniform(0.15, 0.85)
        lon = random.uniform(0.4, 0.85)
        chance = random.uniform(0, 0.6)
        pois.append({
            'pos': [lat, lon],
            'chance': chance,
            'looted': False,
            'tipo': 'normal'
        })
    # POIs avançados (200) – apenas no norte (lon 0.85 a 1.0, lat 0.15 a 0.85)
    for _ in range(200):
        lat = random.uniform(0.15, 0.85)
        lon = random.uniform(0.85, 1.0)
        pois.append({
            'pos': [lat, lon],
            'chance': 0.8,
            'looted': False,
            'tipo': 'avancado'
        })
    random.shuffle(pois)
    return pois

def vasculhar_ponto(player, poi):
    cost = player.use_stamina(5, 'other')
    make_noise(radius=0.003)

    if poi['tipo'] == 'avancado' and random.random() < 0.3:
        player.take_damage(15, reason="zumbi")
        make_noise(radius=0.015)
        return f"{player.name} é atacado por um Juggernaut enquanto vasculha! (-15 HP)"
    if poi['tipo'] == 'normal' and random.random() < 0.1:
        player.take_damage(8, reason="zumbi")
        make_noise(radius=0.01)
        return f"{player.name} encontra um zumbi escondido. (-8 HP)"

    if random.random() < poi['chance']:
        if poi['tipo'] == 'normal':
            tipo = random.choices(['comida', 'água', 'remédio'], weights=[50, 30, 20])[0]
            if tipo == 'comida':
                amount = random.randint(20, 30)
                player.eat(amount, "bom")
                return f"{player.name} acha comida (+{amount} fome)."
            elif tipo == 'água':
                amount = random.randint(20, 30)
                player.drink(amount, "limpa")
                return f"{player.name} encontra água (+{amount} sede)."
            else:
                player.treat_infection(30)
                player.gain_skill_xp("medicina")
                return f"{player.name} pega um kit médico (-30 infecção)."
        else:  # avançado
            loot = random.choices(
                ['arma_branca', 'arma_fogo', 'colete', 'municao'],
                weights=[30, 20, 20, 30]
            )[0]
            if loot == 'arma_branca':
                player.gain_skill_xp("armas_brancas", 2)
                return f"{player.name} encontra uma faca tática! (+2 XP armas brancas)"
            elif loot == 'arma_fogo':
                player.gain_skill_xp("armas_fogo", 2)
                return f"{player.name} acha uma pistola danificada, mas útil! (+2 XP armas de fogo)"
            elif loot == 'colete':
                player.temp_defense = 0.2
                return f"{player.name} veste um colete leve (reduz dano em 20% temporariamente)."
            else:
                return f"{player.name} encontra uma caixa de munição (9mm)."
    else:
        falhas = [
            f"{player.name} revira escombros, mas não encontra nada útil.",
            f"{player.name} vasculha um armário vazio.",
            f"{player.name} só encontra poeira e insetos."
        ]
        return random.choice(falhas)

# ---------- Inicialização de estado ----------
if "players" not in st.session_state:
    st.session_state.players = []
if "player_positions" not in st.session_state:
    st.session_state.player_positions = {}
if "current_player_index" not in st.session_state:
    st.session_state.current_player_index = 0
if "game_log" not in st.session_state:
    st.session_state.game_log = []
if "player_relations" not in st.session_state:
    st.session_state.player_relations = {}
if "action_noise" not in st.session_state:
    st.session_state.action_noise = {}
if "zombie_positions" not in st.session_state:
    st.session_state.zombie_positions = []
if "map_image" not in st.session_state:
    st.session_state.map_image = criar_mapa_base()
if "city_pois" not in st.session_state:
    st.session_state.city_pois = gerar_pois()

st.set_page_config(page_title="Cidade Silenciosa – Megacidade Sul-Norte", layout="wide")
st.title("🏙️ Cidade Silenciosa – Exploração Urbana")

# Sidebar: regenerar mapa
with st.sidebar:
    if st.button("🔄 Gerar novo mapa (reseta POIs)"):
        st.session_state.map_image = criar_mapa_base()
        st.session_state.city_pois = gerar_pois()
        st.rerun()

# ---------- Tela de criação do grupo ----------
if len(st.session_state.players) == 0:
    st.subheader("Monte seu grupo de sobreviventes")
    col1, col2 = st.columns(2)
    with col1:
        new_name = st.text_input("Nome do novo personagem:", key="new_player_name")
        if st.button("Adicionar ao grupo"):
            if new_name:
                idx = len(st.session_state.players)
                st.session_state.players.append(Player(new_name))
                # Posição inicial no sul (área segura)
                st.session_state.player_positions[idx] = [0.1, 0.5]
                for i in range(idx):
                    st.session_state.player_relations.setdefault(i, {})[idx] = 'ally'
                    st.session_state.player_relations.setdefault(idx, {})[i] = 'ally'
                st.session_state.game_log.append(f"{new_name} surge nos arredores do sul.")
                st.rerun()
    with col2:
        if len(st.session_state.players) > 0:
            st.success(f"Grupo com {len(st.session_state.players)} personagem(ns).")
            if st.button("Iniciar jornada"):
                st.session_state.current_player_index = 0
                st.rerun()
else:
    # ---------- Jogo em andamento ----------
    total_players = len(st.session_state.players)
    current_idx = st.session_state.current_player_index
    current_player = st.session_state.players[current_idx]
    current_pos = st.session_state.player_positions[current_idx]

    # Reduzir duração de ruídos ao passar a vez
    with st.sidebar:
        st.subheader("👥 Grupo")
        for i, p in enumerate(st.session_state.players):
            rel = get_relation(current_idx, i)
            icon = "👉" if i == current_idx else ("🔵" if rel == 'ally' else "🔴")
            st.write(f"{icon} {p.name} (HP: {p.hp}/{p.max_hp})")
        if st.button("Passar vez ➡️"):
            to_remove = []
            for idx in st.session_state.action_noise:
                st.session_state.action_noise[idx]['turns_left'] -= 1
                if st.session_state.action_noise[idx]['turns_left'] <= 0:
                    to_remove.append(idx)
            for idx in to_remove:
                del st.session_state.action_noise[idx]
            next_idx = (current_idx + 1) % total_players
            st.session_state.current_player_index = next_idx
            st.rerun()
        st.markdown("---")
        st.subheader("🤝 Relações")
        for i, p in enumerate(st.session_state.players):
            if i != current_idx:
                rel = get_relation(current_idx, i)
                new_rel = st.radio(
                    f"Relação com {p.name}",
                    ['ally', 'enemy'],
                    index=0 if rel=='ally' else 1,
                    key=f"rel_{i}"
                )
                if new_rel != rel:
                    st.session_state.player_relations.setdefault(current_idx, {})[i] = new_rel
                    st.session_state.player_relations.setdefault(i, {})[current_idx] = new_rel
                    st.session_state.game_log.append(
                        f"{current_player.name} agora é {'aliado' if new_rel=='ally' else 'inimigo'} de {p.name}."
                    )
                    st.rerun()

    # ---------- Painel do personagem ativo ----------
    st.header(f"Vez de {current_player.name}")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("❤️ Saúde", f"{current_player.hp}/{current_player.max_hp}")
        st.metric("⚡ Estamina", f"{current_player.stamina}/{current_player.max_stamina}")
    with col2:
        st.metric("🍖 Fome", f"{current_player.hunger}/100")
        st.metric("💧 Sede", f"{current_player.thirst}/100")
    with col3:
        st.metric("🦠 Infecção", f"{current_player.infection}/100")
        st.metric("🌡️ Temp", f"{current_player.temperature}/100")
    with col4:
        st.write("**Habilidades**")
        for skill, lvl in current_player.skills.items():
            st.text(f"{skill}: {lvl}")

    # ---------- Ações de sobrevivência ----------
    st.subheader("Ações de Sobrevivência")
    cA, cB, cC, cD = st.columns(4)
    with cA:
        if st.button("⚔️ Atacar zumbi (10 ST)"):
            cost = current_player.use_stamina(10, 'direct')
            current_player.take_damage(8, reason="zumbi")
            current_player.gain_skill_xp("armas_brancas")
            make_noise(radius=0.008)
            st.session_state.game_log.append(f"{current_player.name} ataca um zumbi! (custo {cost} ST)")
            st.rerun()
        if st.button("🛡️ Defender (8 ST)"):
            cost = current_player.use_stamina(8, 'direct')
            current_player.take_damage(3)
            make_noise(radius=0.004)
            st.session_state.game_log.append(f"{current_player.name} se defende. (custo {cost} ST)")
            st.rerun()
    with cB:
        if st.button("💤 Descansar (avança dia)"):
            current_player.rest()
            st.session_state.game_log.append(f"{current_player.name} descansa por um ciclo.")
            if random.randint(1,3) == 1:
                current_player.degrade_skills()
            st.rerun()
    with cC:
        if st.button("💊 Medicar (-30 infecção)"):
            current_player.treat_infection(30)
            current_player.gain_skill_xp("medicina")
            st.session_state.game_log.append(f"{current_player.name} usa medicamentos.")
            st.rerun()
        if st.button("🍞 Comer ração"):
            current_player.eat(25, "bom")
            st.session_state.game_log.append(f"{current_player.name} come uma ração.")
            st.rerun()
    with cD:
        if st.button("💧 Beber água limpa"):
            current_player.drink(25, "limpa")
            st.session_state.game_log.append(f"{current_player.name} bebe água limpa.")
            st.rerun()
        if st.button("🧥 Vestir casaco (+5 isolamento)"):
            current_player.equip_clothing(5)
            st.session_state.game_log.append(f"{current_player.name} veste um casaco.")
            st.rerun()

    # ---------- Exploração urbana (POIs) ----------
    st.subheader("🔍 Explorar a Megacidade")
    if 0.4 <= current_pos[1] <= 0.85:   # centro (cidade)
        poi_proximo = None
        dist_min = 0.005
        for poi in st.session_state.city_pois:
            if not poi['looted']:
                d = distance(current_pos, poi['pos'])
                if d < dist_min:
                    dist_min = d
                    poi_proximo = poi
        if poi_proximo:
            if poi_proximo['tipo'] == 'avancado':
                st.warning("⚠️ Você está numa área extremamente perigosa (Zona Norte).")
            st.write(f"Ponto de interesse a {dist_min*100:.0f}m.")
            if st.button(f"🔎 Vasculhar (custa 5 ST)"):
                desc = vasculhar_ponto(current_player, poi_proximo)
                st.session_state.game_log.append(desc)
                poi_proximo['looted'] = True
                st.rerun()
        else:
            st.write("Nenhum ponto inexplorado por perto. Continue explorando.")
    else:
        st.write("Você está fora da área urbana. Aqui não há edifícios para vasculhar.")

    # ---------- Controle de zumbis ----------
    st.subheader("🧟 População de Zumbis")
    zombie_density = st.slider("Densidade", 10, 100, 30, 5)
    if st.button("🔄 Atualizar patrulhas"):
        st.session_state.zombie_positions = gerar_zumbis(zombie_density)
        st.rerun()
    if not st.session_state.zombie_positions:
        st.session_state.zombie_positions = gerar_zumbis(zombie_density)

    # ---------- Mapa tático ----------
    st.markdown("---")
    st.subheader("🗺️ Mapa Tático")
    img = st.session_state.map_image
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()

    m = folium.Map(location=[0.5, 0.5], zoom_start=12, crs='Simple')
    folium.raster_layers.ImageOverlay(
        image=img_base64,
        bounds=[[0,0],[1,1]],
        opacity=1,
    ).add_to(m)

    # Zonas de risco (polígonos)
    # Sul (baixo risco) - verde
    sul = [[0,0.4], [1,0.4], [1,1], [0,1]]
    folium.GeoJson(
        {"type":"Polygon","coordinates":[sul]},
        style_function=lambda x: {"fillColor":"green","color":"green","fillOpacity":0.1}
    ).add_to(m)
    # Centro (médio) - laranja
    centro = [[0,0.85], [1,0.85], [1,0.4], [0,0.4]]
    folium.GeoJson(
        {"type":"Polygon","coordinates":[centro]},
        style_function=lambda x: {"fillColor":"orange","color":"orange","fillOpacity":0.1}
    ).add_to(m)
    # Norte (alto) - vermelho escuro
    norte = [[0,0], [1,0], [1,0.85], [0,0.85]]
    folium.GeoJson(
        {"type":"Polygon","coordinates":[norte]},
        style_function=lambda x: {"fillColor":"darkred","color":"red","fillOpacity":0.2, "weight":2}
    ).add_to(m)
    # Zona de quarentena (roxo) - dentro do norte
    quarentena = [[0.2,0], [0.2,0.85], [0.8,0.85], [0.8,0]]
    folium.GeoJson(
        {"type":"Polygon","coordinates":[quarentena]},
        style_function=lambda x: {"fillColor":"purple","color":"purple","fillOpacity":0.15}
    ).add_to(m)

    # Zumbis (círculos pretos)
    for z in st.session_state.zombie_positions:
        folium.CircleMarker(
            location=z,
            radius=2,
            color='black',
            fill=True,
            fill_opacity=0.6
        ).add_to(m)

    # POIs (apenas não looted e próximos)
    raio_visao_pois = 0.03
    for poi in st.session_state.city_pois:
        if not poi['looted'] and distance(current_pos, poi['pos']) < raio_visao_pois:
            cor = 'lightblue' if poi['tipo'] == 'normal' else 'yellow'
            folium.CircleMarker(
                location=poi['pos'],
                radius=1.5,
                color=cor,
                fill=True,
                fill_opacity=0.9,
                popup=f"Chance: {poi['chance']*100:.0f}%"
            ).add_to(m)

    # Jogadores (visibilidade condicional)
    for i, p in enumerate(st.session_state.players):
        pos = st.session_state.player_positions[i]
        if i == current_idx:
            cor = 'green'
        else:
            rel = get_relation(current_idx, i)
            if rel == 'ally':
                cor = 'blue'
            else:
                dist = distance(current_pos, pos)
                if dist < 0.005 or (i in st.session_state.action_noise and dist <= st.session_state.action_noise[i]['radius']):
                    cor = 'red'
                else:
                    continue
        folium.Marker(
            location=pos,
            popup=f"{p.name} (HP:{p.hp})",
            icon=folium.Icon(color=cor)
        ).add_to(m)

    st_folium(m, width=800, height=800)

    # Movimentação
    st.subheader(f"Mover {current_player.name}")
    cols_move = st.columns(4)
    step = 0.02
    with cols_move[0]:
        if st.button("⬆️ Norte"):
            new_lat = current_pos[0] + step
            st.session_state.player_positions[current_idx][0] = min(1.0, new_lat)
            st.rerun()
    with cols_move[1]:
        if st.button("⬇️ Sul"):
            new_lat = current_pos[0] - step
            st.session_state.player_positions[current_idx][0] = max(0.0, new_lat)
            st.rerun()
    with cols_move[2]:
        if st.button("➡️ Leste"):
            new_lon = current_pos[1] + step
            st.session_state.player_positions[current_idx][1] = min(1.0, new_lon)
            st.rerun()
    with cols_move[3]:
        if st.button("⬅️ Oeste"):
            new_lon = current_pos[1] - step
            st.session_state.player_positions[current_idx][1] = max(0.0, new_lon)
            st.rerun()

    # Log de eventos
    st.markdown("---")
    st.subheader("📜 Registro")
    for msg in reversed(st.session_state.game_log[-10:]):
        st.write(f"- {msg}")

    # Verificar mortes
    for i, p in enumerate(st.session_state.players):
        if not p.is_alive():
            st.error(f"💀 {p.name} morreu!")
