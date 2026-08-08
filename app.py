import streamlit as st
from player import Player
import random

# Inicialização do estado
if "player" not in st.session_state:
    st.session_state.player = None
if "game_log" not in st.session_state:
    st.session_state.game_log = []

st.set_page_config(page_title="Cidade Silenciosa", layout="wide")
st.title("🏚️ Cidade Silenciosa – Teste do Sistema Completo")

# Tela de criação
if st.session_state.player is None:
    st.subheader("Crie seu Sobrevivente")
    name = st.text_input("Nome:", "Sobrevivente")
    if st.button("Iniciar"):
        st.session_state.player = Player(name)
        st.session_state.game_log.append(f"{name} acorda em um abrigo subterrâneo.")
        st.rerun()
else:
    player = st.session_state.player

    # Painel de status principal
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("❤️ Saúde", f"{player.hp}/{player.max_hp}")
        st.metric("⚡ Estamina", f"{player.stamina}/{player.max_stamina}")
    with col2:
        st.metric("🍖 Fome", f"{player.hunger}/100")
        st.metric("💧 Sede", f"{player.thirst}/100")
    with col3:
        st.metric("🦠 Infecção", f"{player.infection}/100")
        st.metric("🌡️ Temp", f"{player.temperature}/100")
    with col4:
        st.write("**Habilidades**")
        for skill, lvl in player.skills.items():
            st.text(f"{skill}: {lvl}")

    st.markdown("---")
    st.subheader("Ações de Teste")

    # Organização em colunas
    cA, cB, cC, cD = st.columns(4)

    with cA:
        if st.button("⚔️ Atacar (direta, 10 ST)"):
            cost = player.use_stamina(10, 'direct')
            # Simula dano de zumbi
            player.take_damage(8, reason="zumbi")
            player.gain_skill_xp("armas_brancas")
            st.session_state.game_log.append(f"Ataque (custo {cost} ST). Zumbi revidou (-8 HP).")
            st.rerun()

        if st.button("🛡️ Defender (direta, 8 ST)"):
            cost = player.use_stamina(8, 'direct')
            player.take_damage(3)
            st.session_state.game_log.append(f"Defesa (custo {cost} ST). Dano reduzido (-3 HP).")
            st.rerun()

    with cB:
        if st.button("🔍 Vasculhar (outra, 15 ST)"):
            cost = player.use_stamina(15, 'other')
            # Encontra suprimentos aleatórios
            found = random.choice(["comida boa", "água limpa", "nada"])
            if found == "comida boa":
                player.eat(20, "bom")
                st.session_state.game_log.append("Encontrou comida boa (+20 fome).")
            elif found == "água limpa":
                player.drink(20, "limpa")
                st.session_state.game_log.append("Encontrou água limpa (+20 sede).")
            else:
                st.session_state.game_log.append("Não encontrou nada útil.")
            st.rerun()

        if st.button("💤 Descansar (avança dia)"):
            player.rest()
            st.session_state.game_log.append("Descansou. Novo ciclo: fome/sede/temp pioraram.")
            # Degrada habilidades a cada 3 dias (simulado simples)
            if random.randint(1, 3) == 1:
                player.degrade_skills()
                st.session_state.game_log.append("Algumas habilidades enferrujaram um pouco.")
            st.rerun()

    with cC:
        if st.button("💊 Medicar (-30 infecção)"):
            player.treat_infection(30)
            player.gain_skill_xp("medicina")
            st.session_state.game_log.append("Usou medicamento. Infecção reduzida. +XP Medicina.")
            st.rerun()

        if st.button("🍞 Comer ração (bom)"):
            player.eat(25, "bom")
            st.session_state.game_log.append("Comeu ração em bom estado.")
            st.rerun()

        if st.button("💧 Beber água limpa"):
            player.drink(25, "limpa")
            st.session_state.game_log.append("Bebeu água limpa.")
            st.rerun()

    with cD:
        if st.button("🔥 Acender fogueira (simula)"):
            # Simula aquecimento de fogueira pequena
            player.warm_up(20)
            st.session_state.game_log.append("Aqueceu-se com uma fogueira (+20 temp).")
            st.rerun()

        if st.button("🧥 Vestir casaco (+5 isolamento)"):
            player.equip_clothing(5)
            st.session_state.game_log.append("Vestiu um casaco. Isolamento térmico: +5.")
            st.rerun()

        if st.button("🤮 Comer comida estragada"):
            player.eat(15, "estragado")
            st.session_state.game_log.append("Comeu comida estragada! Infecção e possível vômito.")
            st.rerun()

    st.markdown("---")
    st.subheader("📜 Registro")
    for msg in reversed(st.session_state.game_log[-10:]):
        st.write(f"- {msg}")

    if not player.is_alive():
        st.error("💀 Você morreu!")
        if st.button("Recomeçar"):
            del st.session_state.player
            del st.session_state.game_log
            st.rerun()
