import random

class Player:
    def __init__(self, name):
        self.name = name
        # Vitalidade
        self.max_hp = 100
        self.hp = 100
        self.max_stamina = 100
        self.stamina = 100

        # Necessidades (0 = péssimo, 100 = saciado/hidratado)
        self.hunger = 100
        self.thirst = 100

        # Infecção (0 = saudável, 100 = séptico)
        self.infection = 0

        # Temperatura corporal (0 = hipotermia, 100 = confortável)
        self.temperature = 100

        # Habilidades (começam em 0, melhoram com uso)
        self.skills = {
            "armas_brancas": 0,
            "armas_fogo": 0,
            "arremesso": 0,
            "furtividade": 0,
            "medicina": 0,
            "mecanica": 0,
            "sobrevivencia": 0
        }

        # Roupas (isolamento térmico passivo, 0 = sem bônus)
        self.clothing_bonus = 0

        # Controle de ações consecutivas
        self.last_action_type = None
        self.last_stamina_cost = 0

        # Inventário (lista de dicionários com 'nome', 'tipo', 'estado')
        self.inventory = []

    # ---------- Métodos de atualização diária ----------
    def apply_daily_needs(self):
        """Passagem de um ciclo (dia/noite): piora fome, sede, temperatura."""
        # Fome e sede caem
        self.hunger = max(0, self.hunger - 15)
        self.thirst = max(0, self.thirst - 20)

        # Temperatura diminui com o frio ambiente (valor base de perda)
        base_temp_loss = 10
        # Roupas reduzem a perda
        effective_loss = max(1, base_temp_loss - self.clothing_bonus)
        self.temperature = max(0, self.temperature - effective_loss)

        self._update_status_effects()

    def _update_status_effects(self):
        """Recalcula máximos e aplica danos progressivos."""
        self._recalculate_max_hp()
        self._recalculate_max_stamina()

        # Danos progressivos
        if self.hunger <= 20:
            self.take_damage(5, reason="fome")
        if self.thirst <= 20:
            self.take_damage(5, reason="sede")
        if self.infection >= 80:
            self.take_damage(3, reason="infecção")
        if self.temperature <= 20:
            self.take_damage(2, reason="frio")

    def _recalculate_max_hp(self):
        base = 100
        reduction = 1.0
        if self.hunger <= 20:
            reduction = min(reduction, 0.8)
        if self.thirst <= 20:
            reduction = min(reduction, 0.8)
        if self.infection >= 80:
            reduction = min(reduction, 0.7)
        # Frio não reduz HP máximo, apenas causa dano (definido nos efeitos)
        self.max_hp = int(base * reduction)
        if self.hp > self.max_hp:
            self.hp = self.max_hp

    def _recalculate_max_stamina(self):
        base = 100
        reduction = 1.0
        if self.hunger <= 20:
            reduction = min(reduction, 0.8)
        if self.thirst <= 20:
            reduction = min(reduction, 0.8)
        # Temperatura baixa também reduz estamina máxima
        if self.temperature <= 20:
            reduction = min(reduction, 0.8)
        self.max_stamina = int(base * reduction)
        if self.stamina > self.max_stamina:
            self.stamina = self.max_stamina

    # ---------- Dano e cura ----------
    def take_damage(self, amount, reason=""):
        self.hp = max(0, self.hp - amount)
        if reason == "zumbi":
            # Rolagem automática de infecção (d30)
            dice = random.randint(1, 30)
            if dice <= 15:
                pass  # sem infecção
            elif dice <= 25:
                self.infection = min(100, self.infection + 5)
            else:
                self.infection = min(100, self.infection + 15)
        if self.hp == 0:
            self._on_death()

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    # Necessidades
    def eat(self, amount, food_state="bom"):
        """food_state: 'bom', 'vencido', 'estragado'."""
        self.hunger = min(100, self.hunger + amount)
        if food_state == "vencido":
            if random.randint(1, 20) >= 11:
                self.infection = min(100, self.infection + 10)
        elif food_state == "estragado":
            self.infection = min(100, self.infection + 20)
            # chance de vômito (perde hidratação)
            if random.random() < 0.5:
                self.thirst = max(0, self.thirst - 15)
        self._update_status_effects()

    def drink(self, amount, water_type="limpa"):
        """water_type: 'limpa', 'contaminada'."""
        self.thirst = min(100, self.thirst + amount)
        if water_type == "contaminada":
            self.infection = min(100, self.infection + 15)
        self._update_status_effects()

    def treat_infection(self, amount):
        """Reduz a infecção (usa medicamento ou habilidade)."""
        self.infection = max(0, self.infection - amount)
        self._update_status_effects()

    # Temperatura
    def warm_up(self, amount):
        """Aumenta a temperatura corporal (ex: fogueira)."""
        self.temperature = min(100, self.temperature + amount)

    def equip_clothing(self, bonus):
        """Define o bônus de isolamento das roupas atuais."""
        self.clothing_bonus = bonus

    # ---------- Estamina e ações ----------
    def use_stamina(self, cost, action_type='other'):
        actual_cost = cost
        if action_type == 'direct' and self.last_action_type == 'direct':
            actual_cost = max(1, int(cost * 0.5))
        self.stamina = max(0, self.stamina - actual_cost)
        self.last_action_type = action_type
        self.last_stamina_cost = actual_cost
        return actual_cost

    def recover_stamina(self, amount):
        self.stamina = min(self.max_stamina, self.stamina + amount)

    # ---------- Habilidades ----------
    def gain_skill_xp(self, skill_name, amount=1):
        if skill_name in self.skills:
            self.skills[skill_name] += amount

    def degrade_skills(self, days=3):
        """A cada período sem usar, perde um pouco de XP."""
        for skill in self.skills:
            if self.skills[skill] > 0:
                self.skills[skill] = max(0, self.skills[skill] - 1)

    # ---------- Estado ----------
    def is_alive(self):
        return self.hp > 0

    def _on_death(self):
        # Placeholder, tratado no Streamlit
        pass

    def rest(self):
        """Descanso: recupera HP e ST, mas avança necessidades."""
        self.heal(20)
        self.recover_stamina(50)
        self.apply_daily_needs()
