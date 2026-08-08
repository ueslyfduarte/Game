import streamlit as st
from player import Player
import folium
from streamlit_folium import st_folium
import random
import math

# ---------- Funções auxiliares ----------
def distance(pos1, pos2):
    return math.sqrt((pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2)

def get_relation(player_idx, other_idx):
    if player_idx == other_idx:
        return 'self'
    relations = st.session_state.player_relations.get(player_idx, {})
    return relations.get(other_idx, 'ally')

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
# Novo: controle de ruídos de ações
if "action_noise" not in st.session_state:
    st.session_state.action_noise = {}  # idx -> {'radius': float, 'turns_left': int}

st.set_page_config(page_title="Cidade Silenciosa - Multijogador", layout="wide")
st.title("🏚️ Cidade Silenciosa – Visibilidade Tática")

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
                base_lat, base_lon = -23.5505, -46.6333
                st.session_state.player_positions[idx] = [
                    base_lat + random.uniform(-0.01, 0.01),
                    base_lon + random.uniform(-0.01, 0.01)
                ]
                for i in range(idx):
                    st.session_state.player_relations.setdefault(i, {})[idx] = 'ally'
                    st.session_state.player_relations.setdefault(idx, {})[i] = 'ally'
                st.session_state.game_log.append(f"{new_name} juntou-se ao grupo.")
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

    # Reduzir contagem de turnos dos ruídos ativos (expira ao passar a vez)
    # (faremos isso quando passar a vez, mas também podemos reduzir aqui se quisermos)

    # ---------- Barra lateral ----------
    with st.sidebar:
        st.subheader("👥 Grupo")
        for i, p in enumerate(st.session_state.players):
            rel = get_relation(current_idx, i)
            icon = "👉" if i == current_idx else ("🔵" if rel == 'ally' else "🔴")
            st.write(f"{icon} {p.name} (HP: {p.hp}/{p.max_hp})")
        if st.button("Passar vez ➡️"):
            # Reduzir duração dos ruídos em 1 turno
            to_remove = []
            for idx in st.session_state.action_noise:
                st.session_state.action_noise[idx]['turns_left'] -= 1
                if st.session_state.action_noise[idx]['turns_left'] <= 0:
                    to_remove.append(idx)
            for idx in to_remove:
                del st.session_state.action_noise[idx]
            # Próximo jogador
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

    # ---------- Função para registrar ruído ----------
    def make_noise(radius, turns=1):
        """Registra um ruído para o jogador atual com raio e duração em turnos."""
        st.session_state.action_noise[current_idx] = {
            'radius': radius,
            'turns_left': turns
        }

    # ---------- Ações (com níveis de ruído) ----------
    st.subheader("Ações de Sobrevivência")
    cA, cB, cC, cD = st.columns(4)
    with cA:
        if st.button("⚔️ Atacar zumbi (10 ST, ruído médio)"):
            cost = current_player.use_stamina(10, 'direct')
            current_player.take_damage(8, reason="zumbi")
            current_player.gain_skill_xp("armas_brancas")
            make_noise(radius=0.008)  # ~800m
            st.session_state.game_log.append(f"{current_player.name} atacou zumbi (custo {cost} ST). Ruído médio.")
            st.rerun()
        if st.button("🛡️ Defender (8 ST, ruído baixo)"):
            cost = current_player.use_stamina(8, 'direct')
            current_player.take_damage(3)
            make_noise(radius=0.004)  # ~400m
            st.session_state.game_log.append(f"{current_player.name} defendeu (custo {cost} ST). Ruído baixo.")
            st.rerun()
    with cB:
        if st.button("🔍 Vasculhar (15 ST, ruído baixo)"):
            cost = current_player.use_stamina(15, 'other')
            found = random.choice(["comida boa", "água limpa", "nada"])
            if found == "comida boa":
                current_player.eat(20, "bom")
                st.session_state.game_log.append(f"{current_player.name} encontrou comida.")
            elif found == "água limpa":
                current_player.drink(20, "limpa")
                st.session_state.game_log.append(f"{current_player.name} encontrou água.")
            else:
                st.session_state.game_log.append(f"{current_player.name} não achou nada.")
            make_noise(radius=0.003)  # vasculhar é silencioso, mas não totalmente
            st.rerun()
        if st.button("💤 Descansar (silencioso, avança dia)"):
            current_player.rest()
            # descansar não gera ruído (ou muito pouco)
            st.session_state.game_log.append(f"{current_player.name} descansou. Ciclo avança.")
            if random.randint(1,3) == 1:
                current_player.degrade_skills()
            st.rerun()
    with cC:
        if st.button("💊 Medicar (silencioso)"):
            current_player.treat_infection(30)
            current_player.gain_skill_xp("medicina")
            st.session_state.game_log.append(f"{current_player.name} medicou-se (silencioso).")
            st.rerun()
        if st.button("🍞 Comer ração (silencioso)"):
            current_player.eat(25, "bom")
            st.session_state.game_log.append(f"{current_player.name} comeu (silencioso).")
            st.rerun()
        if st.button("💧 Beber água limpa (silencioso)"):
            current_player.drink(25, "limpa")
            st.session_state.game_log.append(f"{current_player.name} bebeu (silencioso).")
            st.rerun()
    with cD:
        if st.button("🔥 Acender fogueira (ruído extremo, luz visível)"):
            current_player.warm_up(20)
            # Fogueira gera ruído e também um "evento de luz" visível a longa distância
            make_noise(radius=0.05, turns=2)  # ~5km, dura 2 turnos
            st.session_state.game_log.append(f"{current_player.name} acendeu uma fogueira. Muito visível!")
            st.rerun()
        if st.button("🧥 Vestir casaco (silencioso)"):
            current_player.equip_clothing(5)
            st.session_state.game_log.append(f"{current_player.name} vestiu casaco (silencioso).")
            st.rerun()

    # ---------- Ataque PvP (apenas inimigos detectáveis) ----------
    st.subheader("⚔️ Conflito entre jogadores")
    # Lista alvos válidos: inimigos que estão no raio de detecção (proximidade ou ruído)
    detectable_enemies = []
    for i, p in enumerate(st.session_state.players):
        if i != current_idx and get_relation(current_idx, i) == 'enemy':
            dist = distance(current_pos, st.session_state.player_positions[i])
            # Detecção por proximidade direta (200m)
            if dist < 0.002:
                detectable_enemies.append((i, p, dist, "proximidade"))
            # Detecção por ruído do inimigo
            elif i in st.session_state.action_noise:
                noise_radius = st.session_state.action_noise[i]['radius']
                if dist <= noise_radius:
                    detectable_enemies.append((i, p, dist, "ruído"))
    if detectable_enemies:
        options = [f"{p.name} ({dist*100:.0f}m, {reason})" for i,p,dist,reason in detectable_enemies]
        target = st.selectbox("Alvo detectado:", options)
        if st.button("🗡️ Atacar jogador (15 ST)"):
            selected_idx = detectable_enemies[options.index(target)][0]
            target_player = st.session_state.players[selected_idx]
            cost = current_player.use_stamina(15, 'direct')
            damage = 10 + current_player.skills["armas_brancas"] * 2
            target_player.take_damage(damage, reason="pvp")
            st.session_state.game_log.append(
                f"{current_player.name} atacou {target_player.name} causando {damage} de dano!"
            )
            # O ataque também gera ruído
            make_noise(radius=0.01)  # som de combate alto
            st.rerun()
    else:
        st.write("Nenhum inimigo detectado nas proximidades.")

    # ---------- Mapa com visibilidade condicional ----------
    st.markdown("---")
    st.subheader("🗺️ Mapa – Visão por Proximidade e Ruído")
    m = folium.Map(location=current_pos, zoom_start=15)
    # Adiciona jogador atual
    folium.Marker(
        current_pos,
        popup="Você está aqui",
        icon=folium.Icon(color='green', icon='home')
    ).add_to(m)

    # Para cada outro jogador, decide se aparece
    for i, p in enumerate(st.session_state.players):
        if i == current_idx:
            continue
        pos = st.session_state.player_positions[i]
        rel = get_relation(current_idx, i)
        show_marker = False
        reason = ""

        if rel == 'ally':
            show_marker = True
            reason = "aliado"
        else:
            dist = distance(current_pos, pos)
            # Proximidade direta (<200m)
            if dist < 0.002:
                show_marker = True
                reason = f"perto ({dist*100:.0f}m)"
            # Ruído do outro jogador
            elif i in st.session_state.action_noise:
                noise_radius = st.session_state.action_noise[i]['radius']
                if dist <= noise_radius:
                    show_marker = True
                    reason = f"ruído (dist {dist*100:.0f}m)"

        if show_marker:
            cor = 'blue' if rel == 'ally' else 'red'
            folium.Marker(
                pos,
                popup=f"{p.name} ({reason})",
                icon=folium.Icon(color=cor)
            ).add_to(m)

    st_folium(m, width=700, height=400, key="main_map")

    # Movimentação individual
    st.subheader(f"Mover {current_player.name}")
    cols_move = st.columns(4)
    move_step = 0.005  # ~500m por passo
    with cols_move[0]:
        if st.button("⬆️ Norte"):
            st.session_state.player_positions[current_idx][0] += move_step
            # Movimento normalmente não gera ruído (a menos que corra, etc)
            st.rerun()
    with cols_move[1]:
        if st.button("⬇️ Sul"):
            st.session_state.player_positions[current_idx][0] -= move_step
            st.rerun()
    with cols_move[2]:
        if st.button("➡️ Leste"):
            st.session_state.player_positions[current_idx][1] += move_step
            st.rerun()
    with cols_move[3]:
        if st.button("⬅️ Oeste"):
            st.session_state.player_positions[current_idx][1] -= move_step
            st.rerun()

    # Log de eventos
    st.markdown("---")
    st.subheader("📜 Registro")
    for msg in reversed(st.session_state.game_log[-8:]):
        st.write(f"- {msg}")

    # Verificar mortes
    for i, p in enumerate(st.session_state.players):
        if not p.is_alive():
            st.error(f"💀 {p.name} morreu!")
