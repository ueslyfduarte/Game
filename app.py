import streamlit as st
from player import Player
from mapa_gerador import gerar_mundo, gerar_zumbis, get_loot_table
import plotly.graph_objects as go
import numpy as np
from PIL import Image, ImageDraw
import random
import math

# ---------- Configurações ----------
LOCAL_RADIUS_KM = 0.6            # raio de renderização (km)
BUILDING_HEIGHT_SCALE = 0.008
MAP_FULL_SIZE = 200
KM_TO_PIX_FULL = 20
COR_FUNDO = (20, 20, 20)
ZOMBIE_DETECT_RADIUS = 0.2
ZOMBIE_SPEED = 0.03

TYPE_CONFIG = {
    'residencial': {'max_h': 0.025, 'base': 0.03,  'cor': (180, 180, 180)},
    'comercial':    {'max_h': 0.05,  'base': 0.025, 'cor': (220, 220, 120)},
    'industrial':   {'max_h': 0.06,  'base': 0.03,  'cor': (200, 160, 100)},
    'medico':       {'max_h': 0.07,  'base': 0.025, 'cor': (240, 100, 100)},
    'policial':     {'max_h': 0.08,  'base': 0.025, 'cor': (100, 100, 240)},
    'escola':       {'max_h': 0.04,  'base': 0.03,  'cor': (120, 220, 120)},
    'restaurante':  {'max_h': 0.03,  'base': 0.03,  'cor': (220, 170, 120)}
}

# ---------- Funções auxiliares ----------
def distance(x1, y1, x2, y2):
    return math.sqrt((x1-x2)**2 + (y1-y2)**2)

def get_relation(player_idx, other_idx):
    if player_idx == other_idx: return 'self'
    return st.session_state.player_relations.get(player_idx, {}).get(other_idx, 'ally')

def diario(entrada):
    st.session_state.diary.append(f"Dia {st.session_state.day}: {entrada}")

def mark_visited(x, y):
    cx = int(x * 10)
    cy = int(y * 10)
    st.session_state.visited.add((cx, cy))

def update_zombies(player_x, player_y):
    for z in st.session_state.zombies:
        if distance(z['x'], z['y'], player_x, player_y) < ZOMBIE_DETECT_RADIUS:
            dx = player_x - z['x']
            dy = player_y - z['y']
            dist = math.sqrt(dx*dx + dy*dy)
            if dist > 0:
                step = min(ZOMBIE_SPEED, dist)
                z['x'] += (dx / dist) * step
                z['y'] += (dy / dist) * step

def add_building_mesh(vertices, faces, x, y, largura, altura, z_base=0):
    w = largura / 2.0
    h = altura
    v0 = len(vertices)
    vertices.append([x - w, y - w, z_base])
    vertices.append([x + w, y - w, z_base])
    vertices.append([x + w, y + w, z_base])
    vertices.append([x - w, y + w, z_base])
    vertices.append([x - w, y - w, z_base + h])
    vertices.append([x + w, y - w, z_base + h])
    vertices.append([x + w, y + w, z_base + h])
    vertices.append([x - w, y + w, z_base + h])
    faces.extend([
        [v0, v0+1, v0+2], [v0, v0+2, v0+3],
        [v0+4, v0+7, v0+6], [v0+4, v0+6, v0+5],
        [v0, v0+4, v0+5], [v0, v0+5, v0+1],
        [v0+1, v0+5, v0+6], [v0+1, v0+6, v0+2],
        [v0+2, v0+6, v0+7], [v0+2, v0+7, v0+3],
        [v0+3, v0+7, v0+4], [v0+3, v0+4, v0]
    ])

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
if "last_pos" not in st.session_state:
    st.session_state.last_pos = None
if "last_direction" not in st.session_state:
    st.session_state.last_direction = (0, 1)  # olhando para norte
if "action_just_taken" not in st.session_state:
    st.session_state.action_just_taken = False

st.set_page_config(page_title="Cidade Silenciosa – 1ª Pessoa", layout="wide")
st.title("🏙️ Cidade Silenciosa – Visão Realista em Primeira Pessoa")

# ---------- Tela de criação de grupo ----------
if len(st.session_state.players) == 0:
    st.subheader("Forme seu grupo de sobreviventes")
    nome = st.text_input("Nome do sobrevivente:", key="new")
    if st.button("Adicionar ao grupo"):
        if nome:
            idx = len(st.session_state.players)
            p = Player(nome)
            st.session_state.players.append(p)
            st.session_state.player_positions[idx] = (5.0, 0.5)
            for i in range(idx):
                st.session_state.player_relations.setdefault(i, {})[idx] = 'ally'
                st.session_state.player_relations.setdefault(idx, {})[i] = 'ally'
            mark_visited(5.0, 0.5)
            st.session_state.last_pos = (5.0, 0.5)
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

    if st.session_state.action_just_taken:
        update_zombies(x, y)
        st.session_state.action_just_taken = False

    mark_visited(x, y)
    if st.session_state.last_pos is not None:
        old_x, old_y = st.session_state.last_pos
        dx = x - old_x
        dy = y - old_y
        if dx != 0 or dy != 0:
            length = math.sqrt(dx*dx + dy*dy)
            if length > 0:
                st.session_state.last_direction = (dx/length, dy/length)
    st.session_state.last_pos = (x, y)

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
                        st.session_state.action_just_taken = True
                        st.rerun()
        else:
            st.write("Nenhum item para usar.")
    with tab2:
        for msg in reversed(st.session_state.diary[-30:]):
            st.write(msg)
            # Ações
    st.subheader("Ações")
    cA, cB, cC = st.columns(3)
    with cA:
        if st.button("⚔️ Atacar (8 ST)"):
            if jogador.stamina < 8:
                st.warning("Sem estamina!")
            else:
                custo = jogador.use_stamina(8, 'direct')
                dano = jogador.get_attack_damage()
                zumbi_perto = any(distance(x, y, z['x'], z['y']) < 0.05 for z in st.session_state.zombies)
                if zumbi_perto:
                    jogador.take_damage(5, reason="zumbi")
                    diario(f"{jogador.name} ataca um zumbi causando {dano} de dano, mas sofre um arranhão.")
                else:
                    diario(f"{jogador.name} golpeia o ar. Nenhum zumbi por perto.")
                st.session_state.action_just_taken = True
                st.rerun()
        if st.button("🛡️ Defender (5 ST)"):
            if jogador.stamina < 5:
                st.warning("Sem estamina!")
            else:
                jogador.use_stamina(5, 'direct')
                diario(f"{jogador.name} fica em posição defensiva.")
                st.session_state.action_just_taken = True
                st.rerun()
    with cB:
        if st.button("💤 Descansar"):
            jogador.rest()
            st.session_state.day += 1
            diario(f"{jogador.name} descansa. Um novo dia amanhece.")
            if random.randint(1,3) == 1:
                jogador.degrade_skills()
            st.session_state.action_just_taken = True
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
                                    if 'arma' in item.lower(): peso = 2.0
                                    elif 'munição' in item.lower(): peso = 0.1
                                    elif 'garrafa' in item.lower() or 'lata' in item.lower(): peso = 0.3
                                    if jogador.add_item(item, 'diverso', 1, peso):
                                        diario(f"{jogador.name} encontra {item} em um(a) {poi['tipo']}.")
                                    else:
                                        diario(f"{jogador.name} encontra {item}, mas está sobrecarregado e não pode carregar.")
                                    break
                            else:
                                diario(f"{jogador.name} vasculha, mas não acha nada útil.")
                        poi['looted'] = True
                        st.session_state.action_just_taken = True
                        st.rerun()
                diario(f"{jogador.name} não há nada para vasculhar nas proximidades.")
                st.session_state.action_just_taken = True
                st.rerun()

    # Movimentação
    st.subheader(f"Mover {jogador.name} (custa 2 ST)")
    cols_m = st.columns(4)
    passo = 0.1
    sem_st = jogador.stamina < 2
    if cols_m[0].button("⬆️ Norte", disabled=sem_st):
        jogador.use_stamina(2, 'other')
        st.session_state.player_positions[atual] = (x, min(9.9, y + passo))
        st.session_state.action_just_taken = True
        st.rerun()
    if cols_m[1].button("⬇️ Sul", disabled=sem_st):
        jogador.use_stamina(2, 'other')
        st.session_state.player_positions[atual] = (x, max(0.1, y - passo))
        st.session_state.action_just_taken = True
        st.rerun()
    if cols_m[2].button("➡️ Leste", disabled=sem_st):
        jogador.use_stamina(2, 'other')
        st.session_state.player_positions[atual] = (min(9.9, x + passo), y)
        st.session_state.action_just_taken = True
        st.rerun()
    if cols_m[3].button("⬅️ Oeste", disabled=sem_st):
        jogador.use_stamina(2, 'other')
        st.session_state.player_positions[atual] = (max(0.1, x - passo), y)
        st.session_state.action_just_taken = True
        st.rerun()

    # ---------- MAPA EM PRIMEIRA PESSOA REALISTA ----------
    st.markdown("---")
    col_map1, col_map2 = st.columns([3, 1])

    with col_map1:
        st.subheader("👁️ Visão em Primeira Pessoa")
        predios, ruas, _ = st.session_state.world

        dir_x, dir_y = st.session_state.last_direction
        eye_height = 0.016          # ~1,6 metros
        look_distance = 0.35       # distância focal (metros)

        eye_x = x
        eye_y = y
        eye_z = eye_height

        down_angle = 0.03          # pequena inclinação para baixo
        center_x = x + dir_x * look_distance
        center_y = y + dir_y * look_distance
        center_z = eye_height - down_angle * look_distance

        fov = 120                  # graus
        half_fov_rad = math.radians(fov / 2)
        max_depth = 0.6            # km
        near = 0.01
        far = max_depth

        perp_x = -dir_y
        perp_y = dir_x

        near_center_x = x + dir_x * near
        near_center_y = y + dir_y * near
        far_center_x = x + dir_x * far
        far_center_y = y + dir_y * far

        near_half_width = near * math.tan(half_fov_rad)
        far_half_width = far * math.tan(half_fov_rad)

        p1 = (near_center_x - perp_x * near_half_width, near_center_y - perp_y * near_half_width)
        p2 = (near_center_x + perp_x * near_half_width, near_center_y + perp_y * near_half_width)
        p3 = (far_center_x + perp_x * far_half_width, far_center_y + perp_y * far_half_width)
        p4 = (far_center_x - perp_x * far_half_width, far_center_y - perp_y * far_half_width)

        xs = [p[0] for p in [p1, p2, p3, p4]]
        ys = [p[1] for p in [p1, p2, p3, p4]]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)

        # Chão
        vertices_floor = [
            [x_min, y_min, 0], [x_max, y_min, 0], [x_max, y_max, 0], [x_min, y_max, 0]
        ]
        faces_floor = [[0, 1, 2], [0, 2, 3]]
        mesh_floor = go.Mesh3d(
            x=[v[0] for v in vertices_floor],
            y=[v[1] for v in vertices_floor],
            z=[v[2] for v in vertices_floor],
            i=[f[0] for f in faces_floor],
            j=[f[1] for f in faces_floor],
            k=[f[2] for f in faces_floor],
            facecolor=['rgb(25,25,25)', 'rgb(25,25,25)'],
            opacity=1.0,
            name='Chão',
            lighting=dict(ambient=0.5, diffuse=0.5, specular=0.1, roughness=0.5)
        )

        # Prédios
        vertices = []
        faces = []
        cores_predios = []
        for b in predios:
            if x_min <= b['x'] <= x_max and y_min <= b['y'] <= y_max:
                cfg = TYPE_CONFIG.get(b['tipo'], TYPE_CONFIG['residencial'])
                h = min(cfg['max_h'], b['altura'] * BUILDING_HEIGHT_SCALE)
                h = max(h, 0.005)
                base = cfg['base']
                cor = cfg['cor']
                add_building_mesh(vertices, faces, b['x'], b['y'], base, h)
                cores_predios.extend([cor] * 12)
        mesh_predios = go.Mesh3d(
            x=[v[0] for v in vertices],
            y=[v[1] for v in vertices],
            z=[v[2] for v in vertices],
            i=[face[0] for face in faces],
            j=[face[1] for face in faces],
            k=[face[2] for face in faces],
            facecolor=[f'rgb({c[0]},{c[1]},{c[2]})' for c in cores_predios],
            opacity=1.0,
            flatshading=True,
            name='Prédios',
            lighting=dict(ambient=0.6, diffuse=0.8, specular=0.2, roughness=0.3)
        )

        # Ruas (faixas cinza)
        ruas_x, ruas_y, ruas_z = [], [], []
        for r in ruas:
            if (x_min <= r['x1'] <= x_max and y_min <= r['y1'] <= y_max) or \
               (x_min <= r['x2'] <= x_max and y_min <= r['y2'] <= y_max):
                ruas_x.extend([r['x1'], r['x2'], None])
                ruas_y.extend([r['y1'], r['y2'], None])
                ruas_z.extend([0.001, 0.001, None])
        trace_ruas = go.Scatter3d(
            x=ruas_x, y=ruas_y, z=ruas_z,
            mode='lines', line=dict(color='darkgray', width=6), name='Ruas'
        )

        # Faixa central amarela
        faixa_x, faixa_y, faixa_z = [], [], []
        for r in ruas:
            if r['x1'] == r['x2']:
                if x_min <= r['x1'] <= x_max:
                    faixa_x.extend([r['x1'], r['x1'], None])
                    faixa_y.extend([r['y1'], r['y2'], None])
                    faixa_z.extend([0.002, 0.002, None])
            else:
                if y_min <= r['y1'] <= y_max:
                    faixa_x.extend([r['x1'], r['x2'], None])
                    faixa_y.extend([r['y1'], r['y1'], None])
                    faixa_z.extend([0.002, 0.002, None])
        trace_faixa = go.Scatter3d(
            x=faixa_x, y=faixa_y, z=faixa_z,
            mode='lines', line=dict(color='gold', width=2, dash='dot'), name='Faixa'
        )

        # Calçadas
        calcadas_x, calcadas_y, calcadas_z = [], [], []
        offset = 0.015
        for r in ruas:
            if r['x1'] == r['x2']:
                if (x_min <= r['x1']-offset <= x_max) or (x_min <= r['x1']+offset <= x_max):
                    calcadas_x.extend([r['x1']-offset, r['x1']-offset, None, r['x1']+offset, r['x1']+offset, None])
                    calcadas_y.extend([r['y1'], r['y2'], None, r['y1'], r['y2'], None])
                    calcadas_z.extend([0.003, 0.003, None, 0.003, 0.003, None])
            else:
                if (y_min <= r['y1']-offset <= y_max) or (y_min <= r['y1']+offset <= y_max):
                    calcadas_y.extend([r['y1']-offset, r['y1']-offset, None, r['y1']+offset, r['y1']+offset, None])
                    calcadas_x.extend([r['x1'], r['x2'], None, r['x1'], r['x2'], None])
                    calcadas_z.extend([0.003, 0.003, None, 0.003, 0.003, None])
        trace_calcadas = go.Scatter3d(
            x=calcadas_x, y=calcadas_y, z=calcadas_z,
            mode='lines', line=dict(color='white', width=2), name='Calçadas'
        )

        # Zumbis
        zumbis_x, zumbis_y, zumbis_z = [], [], []
        for z in st.session_state.zombies:
            if x_min <= z['x'] <= x_max and y_min <= z['y'] <= y_max:
                zumbis_x.append(z['x'])
                zumbis_y.append(z['y'])
                zumbis_z.append(0.008)
        trace_zumbis = go.Scatter3d(
            x=zumbis_x, y=zumbis_y, z=zumbis_z,
            mode='markers', marker=dict(size=8, color='black'),
            name='Zumbis'
        )

        # Outros jogadores
        outros_x, outros_y, outros_z = [], [], []
        cores_outros = []
        for i, p in enumerate(st.session_state.players):
            if i != atual:
                px, py = st.session_state.player_positions[i]
                if x_min <= px <= x_max and y_min <= py <= y_max:
                    outros_x.append(px)
                    outros_y.append(py)
                    outros_z.append(0.01)
                    rel = get_relation(atual, i)
                    cores_outros.append('blue' if rel == 'ally' else 'red')
        trace_outros = go.Scatter3d(
            x=outros_x, y=outros_y, z=outros_z,
            mode='markers', marker=dict(size=10, color=cores_outros),
            name='Outros'
        )

        # Mira (ponto central)
        # Mira (ponto central)
        mira_dist = 0.05
        mira_x = [x + dir_x * mira_dist]
        mira_y = [y + dir_y * mira_dist]
        mira_z = [eye_height]
        trace_mira = go.Scatter3d(
            x=mira_x, y=mira_y, z=mira_z,
            mode='markers',
            marker=dict(size=6, color='white', symbol='cross'),
            name='Mira'
        )

        # Configuração da câmera
        camera = dict(
            eye=dict(x=eye_x, y=eye_y, z=eye_z),
            center=dict(x=center_x, y=center_y, z=center_z),
            projection=dict(type='perspective')
        )

        fig = go.Figure(data=[
            mesh_floor, mesh_predios, trace_ruas, trace_faixa, trace_calcadas,
            trace_zumbis, trace_outros, trace_mira
        ])
        fig.update_layout(
            scene=dict(
                xaxis=dict(range=[x_min, x_max], visible=False),
                yaxis=dict(range=[y_min, y_max], visible=False),
                zaxis=dict(range=[0, 0.15], visible=False),
                aspectmode='manual',
                aspectratio=dict(x=1, y=1, z=0.4),
                bgcolor='rgb(10,10,20)',
                camera=camera
            ),
            paper_bgcolor='rgb(10,10,20)',
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_map2:
        st.subheader("🧭 Minimapa")
        img_mini = Image.new('RGB', (MAP_FULL_SIZE, MAP_FULL_SIZE), COR_FUNDO)
        draw_mini = ImageDraw.Draw(img_mini)
        def world_to_mini(wx, wy):
            return int(wx * KM_TO_PIX_FULL), int(wy * KM_TO_PIX_FULL)
        for (cx, cy) in st.session_state.visited:
            x0, y0 = int(cx * 2), int(cy * 2)
            draw_mini.rectangle([(x0, y0), (x0+2, y0+2)], fill=(60,60,60))
        for r in ruas:
            p1 = world_to_mini(r['x1'], r['y1'])
            p2 = world_to_mini(r['x2'], r['y2'])
            draw_mini.line([p1, p2], fill=(80,80,80), width=1)
        for i, p in enumerate(st.session_state.players):
            px, py = world_to_mini(*st.session_state.player_positions[i])
            if i == atual:
                cor = (0,255,0)
            else:
                rel = get_relation(atual, i)
                cor = (0,0,255) if rel == 'ally' else (255,0,0)
            draw_mini.ellipse([(px-2, py-2), (px+2, py+2)], fill=cor)
        st.image(img_mini, use_container_width=True, caption="Cidade (10x10 km)")

    # Verificar mortes
    for i, p in enumerate(st.session_state.players):
        if not p.is_alive():
            st.error(f"💀 {p.name} morreu!")
