import streamlit as st
from player import Player
from mapa_gerador import gerar_mundo, gerar_zumbis, get_loot_table
import plotly.graph_objects as go
import numpy as np
from PIL import Image, ImageDraw
import random
import math

# ---------- Configurações ----------
LOCAL_RADIUS_KM = 0.5            # raio visível 3D (km)
BUILDING_BASE = 0.01             # tamanho horizontal do prédio (km)
BUILDING_HEIGHT_SCALE = 0.005    # fator para altura visual (km por unidade de altura)
MAP_FULL_SIZE = 200              # minimapa (pixels)
KM_TO_PIX_FULL = 20              # 10 km -> 200 px
COR_FUNDO = (20, 20, 20)

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

# ---------- Geração de mesh para prédios ----------
def add_building_mesh(vertices, faces, x, y, largura, altura, z_base=0):
    """Adiciona um cuboide centrado em (x, y) ao mesh."""
    w = largura / 2.0
    h = altura
    # 8 vértices
    v0 = len(vertices)
    vertices.append([x - w, y - w, z_base])
    vertices.append([x + w, y - w, z_base])
    vertices.append([x + w, y + w, z_base])
    vertices.append([x - w, y + w, z_base])
    vertices.append([x - w, y - w, z_base + h])
    vertices.append([x + w, y - w, z_base + h])
    vertices.append([x + w, y + w, z_base + h])
    vertices.append([x - w, y + w, z_base + h])
    # 12 triângulos (faces)
    faces.extend([
        [v0, v0+1, v0+2], [v0, v0+2, v0+3],  # base
        [v0+4, v0+7, v0+6], [v0+4, v0+6, v0+5],  # topo
        [v0, v0+4, v0+5], [v0, v0+5, v0+1],  # lateral
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
    st.session_state.last_direction = None

st.set_page_config(page_title="Cidade Silenciosa 3D", layout="wide")
st.title("🏙️ Cidade Silenciosa – Exploração 3D")

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

    # Marcar visita
    mark_visited(x, y)

    # Atualizar direção (baseado na diferença de posição)
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

    # Abas inventário/diário (mantidas iguais, omitidas aqui para brevidade – cole as abas do código anterior)
    # ... (use as mesmas abas de inventário e diário que já funcionavam)

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
                        st.rerun()
                diario(f"{jogador.name} não há nada para vasculhar nas proximidades.")
                st.rerun()

    # Movimentação
    st.subheader(f"Mover {jogador.name} (custa 2 ST)")
    cols_m = st.columns(4)
    passo = 0.1
    sem_st = jogador.stamina < 2
    if cols_m[0].button("⬆️ Norte", disabled=sem_st):
        jogador.use_stamina(2, 'other')
        st.session_state.player_positions[atual] = (x, min(9.9, y + passo))
        st.rerun()
    if cols_m[1].button("⬇️ Sul", disabled=sem_st):
        jogador.use_stamina(2, 'other')
        st.session_state.player_positions[atual] = (x, max(0.1, y - passo))
        st.rerun()
    if cols_m[2].button("➡️ Leste", disabled=sem_st):
        jogador.use_stamina(2, 'other')
        st.session_state.player_positions[atual] = (min(9.9, x + passo), y)
        st.rerun()
    if cols_m[3].button("⬅️ Oeste", disabled=sem_st):
        jogador.use_stamina(2, 'other')
        st.session_state.player_positions[atual] = (max(0.1, x - passo), y)
        st.rerun()

    # ---------- MAPA 3D LOCAL ----------
    st.markdown("---")
    col_map1, col_map2 = st.columns([3, 1])

    with col_map1:
        st.subheader("🏢 Visão 3D (raio de 0.5 km)")

        # Dados do mundo
        predios, ruas, _ = st.session_state.world
        x_min, x_max = x - LOCAL_RADIUS_KM, x + LOCAL_RADIUS_KM
        y_min, y_max = y - LOCAL_RADIUS_KM, y + LOCAL_RADIUS_KM

        # Construir mesh dos prédios visíveis
        vertices = []
        faces = []
        cores_predios = []
        for b in predios:
            if x_min <= b['x'] <= x_max and y_min <= b['y'] <= y_max:
                # altura visual: limitar entre 0.01 e 0.06 km (10 a 60 metros)
                altura_km = min(0.06, max(0.01, b['altura'] * BUILDING_HEIGHT_SCALE))
                cor_rgb = {
                    'residencial': (160, 160, 160),
                    'comercial': (200, 200, 100),
                    'industrial': (180, 140, 80),
                    'medico': (220, 80, 80),
                    'policial': (80, 80, 220),
                    'escola': (100, 200, 100),
                    'restaurante': (200, 150, 100)
                }.get(b['tipo'], (150,150,150))
                add_building_mesh(vertices, faces, b['x'], b['y'], BUILDING_BASE, altura_km)
                cores_predios.extend([cor_rgb] * 12)  # 12 triângulos por prédio

        # Criar mesh 3D dos prédios
        mesh_predios = go.Mesh3d(
            x=[v[0] for v in vertices],
            y=[v[1] for v in vertices],
            z=[v[2] for v in vertices],
            i=[face[0] for face in faces],
            j=[face[1] for face in faces],
            k=[face[2] for face in faces],
            facecolor=[f'rgb({c[0]},{c[1]},{c[2]})' for c in cores_predios],
            opacity=0.9,
            name='Prédios'
        )

        # Ruas (linhas)
        ruas_x = []
        ruas_y = []
        ruas_z = []
        for r in ruas:
            if (x_min <= r['x1'] <= x_max and y_min <= r['y1'] <= y_max) or \
               (x_min <= r['x2'] <= x_max and y_min <= r['y2'] <= y_max):
                ruas_x.extend([r['x1'], r['x2'], None])
                ruas_y.extend([r['y1'], r['y2'], None])
                ruas_z.extend([0, 0, None])
        trace_ruas = go.Scatter3d(
            x=ruas_x, y=ruas_y, z=ruas_z,
            mode='lines',
            line=dict(color='gray', width=2),
            name='Ruas'
        )

        # Zumbis
        zumbis_x, zumbis_y, zumbis_z = [], [], []
        for z in st.session_state.zombies:
            if x_min <= z['x'] <= x_max and y_min <= z['y'] <= y_max:
                zumbis_x.append(z['x'])
                zumbis_y.append(z['y'])
                zumbis_z.append(0.005)  # levemente acima do chão
        trace_zumbis = go.Scatter3d(
            x=zumbis_x, y=zumbis_y, z=zumbis_z,
            mode='markers',
            marker=dict(size=3, color='black'),
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
            mode='markers',
            marker=dict(size=6, color=cores_outros),
            name='Outros'
        )

        # Jogador atual (esfera verde)
        trace_jogador = go.Scatter3d(
            x=[x], y=[y], z=[0.015],
            mode='markers',
            marker=dict(size=10, color='lime', symbol='circle'),
            name=jogador.name
        )

        # Seta de direção
        direcao_trace = None
        if st.session_state.last_direction is not None:
            dx, dy = st.session_state.last_direction
            comp = 0.04  # 40 metros
            end_x = x + dx * comp
            end_y = y + dy * comp
            direcao_trace = go.Scatter3d(
                x=[x, end_x], y=[y, end_y], z=[0.015, 0.015],
                mode='lines',
                line=dict(color='yellow', width=6),
                name='Direção'
            )

        # Configuração do layout 3D
        fig = go.Figure(data=[mesh_predios, trace_ruas, trace_zumbis, trace_outros, trace_jogador] +
                             ([direcao_trace] if direcao_trace else []))
        fig.update_layout(
            scene=dict(
                xaxis=dict(range=[x_min, x_max], visible=False),
                yaxis=dict(range=[y_min, y_max], visible=False),
                zaxis=dict(range=[0, 0.1], visible=False),
                aspectmode='manual',
                aspectratio=dict(x=1, y=1, z=0.3),
                bgcolor='rgb(20,20,20)'
            ),
            paper_bgcolor='rgb(20,20,20)',
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=False
        )
        fig.update_scenes(camera=dict(eye=dict(x=1.5, y=1.5, z=0.8)))
        st.plotly_chart(fig, use_container_width=True)

    with col_map2:
        st.subheader("🧭 Minimapa")
        # Minimapa com Pillow (igual ao código anterior)
        img_mini = Image.new('RGB', (MAP_FULL_SIZE, MAP_FULL_SIZE), COR_FUNDO)
        draw_mini = ImageDraw.Draw(img_mini)
        def world_to_mini(wx, wy):
            return int(wx * KM_TO_PIX_FULL), int(wy * KM_TO_PIX_FULL)
        # Células visitadas
        for (cx, cy) in st.session_state.visited:
            x0, y0 = int(cx * 2), int(cy * 2)
            draw_mini.rectangle([(x0, y0), (x0+2, y0+2)], fill=(60,60,60))
        # Ruas
        for r in ruas:
            p1 = world_to_mini(r['x1'], r['y1'])
            p2 = world_to_mini(r['x2'], r['y2'])
            draw_mini.line([p1, p2], fill=(80,80,80), width=1)
        # Jogadores
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
