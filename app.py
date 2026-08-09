import streamlit as st
from player import Player
from mapa_gerador import gerar_mundo, gerar_zumbis, get_loot_table
from PIL import Image, ImageDraw
import random
import math

# ---------- Configurações ----------
MAP_FULL_SIZE = 200        # minimapa (pixels)
LOCAL_MAP_SIZE = 400       # mapa local (pixels)
LOCAL_RADIUS_KM = 0.5      # raio visível ao redor (km)
KM_TO_PIX_FULL = 20        # 10 km -> 200 px (minimapa)
KM_TO_PIX_LOCAL = int(LOCAL_MAP_SIZE / (2 * LOCAL_RADIUS_KM))  # 400px para 1km

# Cores
COR_FUNDO = (20, 20, 20)
COR_RUA = (80, 80, 80)
COR_VISITADO = (60, 60, 60)
CORES_TIPO = {
    'residencial': (160, 160, 160),
    'comercial': (200, 200, 100),
    'industrial': (180, 140, 80),
    'medico': (220, 80, 80),
    'policial': (80, 80, 220),
    'escola': (100, 200, 100),
    'restaurante': (200, 150, 100)
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
    cx = int(x * 10)  # célula de 100m
    cy = int(y * 10)
    st.session_state.visited.add((cx, cy))

def cell_visited(x, y):
    cx = int(x * 10)
    cy = int(y * 10)
    return (cx, cy) in st.session_state.visited

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
if "last_direction" not in st.session_state:
    st.session_state.last_direction = None  # guarda (dx, dy) do último movimento

st.set_page_config(page_title="Cidade Silenciosa", layout="wide")
st.title("🏙️ Cidade Silenciosa – Exploração por Quarteirão")

# ---------- Tela de criação do grupo ----------
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

    # Marcar célula atual como visitada
    mark_visited(x, y)

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
    direcao = None
    with cols_m[0]:
        if st.button("⬆️ Norte", disabled=sem_st):
            jogador.use_stamina(2, 'other')
            st.session_state.player_positions[atual] = (x, min(9.9, y + passo))
            direcao = (0, 1)
            st.rerun()
    with cols_m[1]:
        if st.button("⬇️ Sul", disabled=sem_st):
            jogador.use_stamina(2, 'other')
            st.session_state.player_positions[atual] = (x, max(0.1, y - passo))
            direcao = (0, -1)
            st.rerun()
    with cols_m[2]:
        if st.button("➡️ Leste", disabled=sem_st):
            jogador.use_stamina(2, 'other')
            st.session_state.player_positions[atual] = (min(9.9, x + passo), y)
            direcao = (1, 0)
            st.rerun()
    with cols_m[3]:
        if st.button("⬅️ Oeste", disabled=sem_st):
            jogador.use_stamina(2, 'other')
            st.session_state.player_positions[atual] = (max(0.1, x - passo), y)
            direcao = (-1, 0)
            st.rerun()
    # Após qualquer movimento, atualiza direção (feito nos botões acima, mas precisa ser capturado antes do rerun)
    # A solução é guardar a direção no session_state ANTES do rerun. Vamos criar uma função auxiliar para movimento.
    # Reestruturando: não posso chamar st.rerun() dentro dos botões e depois atualizar direção. Melhor criar uma função move().

    # ---------- MAPAS ----------
    st.markdown("---")
    col_map1, col_map2 = st.columns([2, 1])
    with col_map1:
        st.subheader("🗺️ Visão Local")
        # Gera imagem local ao redor do jogador
        img_local = Image.new('RGB', (LOCAL_MAP_SIZE, LOCAL_MAP_SIZE), COR_FUNDO)
        draw = ImageDraw.Draw(img_local)

        # Limites do mundo visíveis na janela local
        x_min = x - LOCAL_RADIUS_KM
        x_max = x + LOCAL_RADIUS_KM
        y_min = y - LOCAL_RADIUS_KM
        y_max = y + LOCAL_RADIUS_KM

        # Converte coordenadas do mundo para pixel local
        def world_to_local(wx, wy):
            px = int((wx - x_min) * KM_TO_PIX_LOCAL)
            py = int((wy - y_min) * KM_TO_PIX_LOCAL)
            return px, py

        # Desenha ruas (apenas as visíveis dentro da janela)
        predios, ruas, _ = st.session_state.world
        for r in ruas:
            # clip simples: verifica se a linha cruza o retângulo visível
            # (para simplicidade, desenhamos se pelo menos um ponto está dentro)
            if (x_min <= r['x1'] <= x_max and y_min <= r['y1'] <= y_max) or \
               (x_min <= r['x2'] <= x_max and y_min <= r['y2'] <= y_max):
                p1 = world_to_local(r['x1'], r['y1'])
                p2 = world_to_local(r['x2'], r['y2'])
                draw.line([p1, p2], fill=COR_RUA, width=1)

        # Desenha prédios dentro da janela
        for b in predios:
            if x_min <= b['x'] <= x_max and y_min <= b['y'] <= y_max:
                px, py = world_to_local(b['x'], b['y'])
                cor = CORES_TIPO.get(b['tipo'], (150,150,150))
                # retângulo do prédio
                sz = 3
                draw.rectangle([(px-sz, py-sz), (px+sz, py+sz)], fill=cor, outline=(50,50,50))

        # Zumbis na área
        for z in st.session_state.zombies:
            if x_min <= z['x'] <= x_max and y_min <= z['y'] <= y_max:
                zx, zy = world_to_local(z['x'], z['y'])
                draw.ellipse([(zx-1, zy-1), (zx+1, zy+1)], fill=(0,0,0))

        # Outros jogadores
        for i, p in enumerate(st.session_state.players):
            if i != atual:
                px_, py_ = st.session_state.player_positions[i]
                if x_min <= px_ <= x_max and y_min <= py_ <= y_max:
                    px, py = world_to_local(px_, py_)
                    rel = get_relation(atual, i)
                    cor = (0,0,255) if rel == 'ally' else (255,0,0)
                    draw.ellipse([(px-4, py-4), (px+4, py+4)], fill=cor, outline=(255,255,255))

        # Jogador atual (seta de direção)
        px, py = world_to_local(x, y)
        # Desenha círculo verde
        draw.ellipse([(px-5, py-5), (px+5, py+5)], fill=(0,255,0), outline=(255,255,255))
        # Seta de direção se existir
        if st.session_state.last_direction is not None:
            dx, dy = st.session_state.last_direction
            # comprimento da seta
            comp = 10
            end_x = px + dx * comp
            end_y = py + dy * comp
            draw.line([(px, py), (end_x, end_y)], fill=(255,255,0), width=3)

        st.image(img_local, use_container_width=True, caption=f"Raio de {LOCAL_RADIUS_KM}km")

    with col_map2:
        st.subheader("🧭 Minimapa")
        # Minimapa geral (200x200 px, 10x10 km)
        img_mini = Image.new('RGB', (MAP_FULL_SIZE, MAP_FULL_SIZE), COR_FUNDO)
        draw_mini = ImageDraw.Draw(img_mini)

        # Converte mundo -> minimapa
        def world_to_mini(wx, wy):
            px = int(wx * KM_TO_PIX_FULL)
            py = int(wy * KM_TO_PIX_FULL)
            return px, py

        # Pinta células visitadas
        for (cx, cy) in st.session_state.visited:
            # cada célula tem 0.1 x 0.1 km, então no minimapa é 2x2 pixels
            x0 = int(cx * 2)
            y0 = int(cy * 2)
            draw_mini.rectangle([(x0, y0), (x0+2, y0+2)], fill=COR_VISITADO)

        # Ruas (finas, em toda a cidade)
        for r in ruas:
            p1 = world_to_mini(r['x1'], r['y1'])
            p2 = world_to_mini(r['x2'], r['y2'])
            draw_mini.line([p1, p2], fill=COR_RUA, width=1)

        # Jogadores (pontos coloridos)
        for i, p in enumerate(st.session_state.players):
            px, py = world_to_mini(*st.session_state.player_positions[i])
            if i == atual:
                cor = (0,255,0)
            else:
                rel = get_relation(atual, i)
                cor = (0,0,255) if rel == 'ally' else (255,0,0)
            draw_mini.ellipse([(px-2, py-2), (px+2, py+2)], fill=cor)

        st.image(img_mini, use_container_width=True, caption="Cidade (10x10 km)")

    # Atualiza última direção após movimento (precisa ser antes do rerun)
    # Como os botões já chamam rerun, a direção se perde. Vamos reestruturar o movimento para usar uma função.
    # Solução rápida: guardar direção no session_state logo antes do rerun.
    # Mas não é possível porque o código dos botões já é executado e depois rerun. 
    # Melhor: fazer os botões de movimento chamarem uma função que já atualiza a direção e dá rerun.
    # Vou modificar a parte de movimento acima, substituindo por esta lógica:

    # A forma mais simples é usar um callback via on_click, mas Streamlit não suporta bem em botões simples.
    # Alternativa: verificar a cada renderização qual foi a última direção percorrida, comparando posição anterior? 
    # Vamos armazenar a posição anterior e ao detectar mudança, inferir direção. É mais confiável.
    # Implementação: guardar last_pos no session_state e comparar.

    # Adicionar no início do jogo: if "last_pos" not in st.session_state: st.session_state.last_pos = ...
    # E após calcular x,y atuais, determinar direção e armazenar last_direction.
    # Faremos isso agora.

    # ---------- Atualização da direção (baseada na diferença de posição) ----------
    if "last_pos" not in st.session_state:
        st.session_state.last_pos = (x, y)
    else:
        old_x, old_y = st.session_state.last_pos
        dx = x - old_x
        dy = y - old_y
        if dx != 0 or dy != 0:
            # normaliza para direção unitária
            length = math.sqrt(dx*dx + dy*dy)
            if length > 0:
                st.session_state.last_direction = (dx/length, dy/length)
        st.session_state.last_pos = (x, y)

    # Verificar mortes
    for i, p in enumerate(st.session_state.players):
        if not p.is_alive():
            st.error(f"💀 {p.name} morreu!")
