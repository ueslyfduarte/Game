import random

class Player:
    def __init__(self, name):
        self.name = name
        self.max_hp = 100
        self.hp = 100
        self.max_stamina = 100
        self.stamina = 100
        self.hunger = 100          # 0 = faminto
        self.thirst = 100          # 0 = sedento
        self.infection = 0         # 0 = saudável, 100 = séptico
        self.temperature = 100     # 0 = hipotermia
        self.clothing_bonus = 0
        self.skills = {
            "armas_brancas": 0,
            "armas_fogo": 0,
            "furtividade": 0,
            "medicina": 0,
            "mecanica": 0,
            "sobrevivencia": 0
        }
        self.last_action_type = None
        self.last_stamina_cost = 0
        self.temp_defense = 0.0
        self.inventory = []          # lista de dicts: {'nome','tipo','quantidade','peso','atributos'}
        self.max_weight = 30.0       # kg
        self.equipped_weapon = None  # referência ao item do inventário ou None (desarmado)

    @property
    def current_weight(self):
        return sum(item['peso'] * item.get('quantidade', 1) for item in self.inventory)

    def add_item(self, nome, tipo, quantidade=1, peso=0.5, atributos=None):
        if self.current_weight + peso * quantidade > self.max_weight:
            return False
        for item in self.inventory:
            if item['nome'] == nome and item['tipo'] == tipo and item.get('atributos') == atributos:
                item['quantidade'] += quantidade
                return True
        self.inventory.append({
            'nome': nome,
            'tipo': tipo,
            'quantidade': quantidade,
            'peso': peso,
            'atributos': atributos or {}
        })
        return True

    def remove_item(self, nome, quantidade=1):
        for item in self.inventory:
            if item['nome'] == nome:
                if item['quantidade'] <= quantidade:
                    self.inventory.remove(item)
                else:
                    item['quantidade'] -= quantidade
                return True
        return False

    def has_item(self, nome):
        return any(item['nome'] == nome for item in self.inventory)

    def get_item_quantity(self, nome):
        for item in self.inventory:
            if item['nome'] == nome:
                return item['quantidade']
        return 0

    def apply_daily_needs(self):
        self.hunger = max(0, self.hunger - 10)
        self.thirst = max(0, self.thirst - 15)
        base_temp_loss = 8
        effective_loss = max(1, base_temp_loss - self.clothing_bonus)
        self.temperature = max(0, self.temperature - effective_loss)
        self._update_status_effects()

    def _update_status_effects(self):
        self._recalculate_max_hp()
        self._recalculate_max_stamina()
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
        if self.hunger <= 20: reduction = min(reduction, 0.8)
        if self.thirst <= 20: reduction = min(reduction, 0.8)
        if self.infection >= 80: reduction = min(reduction, 0.7)
        self.max_hp = int(base * reduction)
        self.hp = min(self.hp, self.max_hp)

    def _recalculate_max_stamina(self):
        base = 100
        reduction = 1.0
        if self.hunger <= 20: reduction = min(reduction, 0.8)
        if self.thirst <= 20: reduction = min(reduction, 0.8)
        if self.temperature <= 20: reduction = min(reduction, 0.8)
        self.max_stamina = int(base * reduction)
        self.stamina = min(self.stamina, self.max_stamina)

    def take_damage(self, amount, reason=""):
        if self.temp_defense > 0:
            amount = max(1, int(amount * (1 - self.temp_defense)))
        self.hp = max(0, self.hp - amount)
        if reason == "zumbi":
            dice = random.randint(1, 30)
            if 16 <= dice <= 25:
                self.infection = min(100, self.infection + 5)
            elif dice >= 26:
                self.infection = min(100, self.infection + 15)
        if self.hp == 0:
            self._on_death()

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def eat(self, amount, food_state="bom"):
        self.hunger = min(100, self.hunger + amount)
        if food_state == "vencido":
            if random.randint(1, 20) >= 11:
                self.infection = min(100, self.infection + 10)
        elif food_state == "estragado":
            self.infection = min(100, self.infection + 20)
            if random.random() < 0.5:
                self.thirst = max(0, self.thirst - 15)
        self._update_status_effects()

    def drink(self, amount, water_type="limpa"):
        self.thirst = min(100, self.thirst + amount)
        if water_type == "contaminada":
            self.infection = min(100, self.infection + 15)
        self._update_status_effects()

    def treat_infection(self, amount):
        self.infection = max(0, self.infection - amount)
        self._update_status_effects()

    def warm_up(self, amount):
        self.temperature = min(100, self.temperature + amount)

    def equip_clothing(self, bonus):
        self.clothing_bonus = bonus

    def use_stamina(self, cost, action_type='other'):
        if action_type == 'direct' and self.last_action_type == 'direct':
            actual_cost = max(1, int(cost * 0.5))
        else:
            actual_cost = cost
        self.stamina = max(0, self.stamina - actual_cost)
        self.last_action_type = action_type
        self.last_stamina_cost = actual_cost
        return actual_cost

    def recover_stamina(self, amount):
        self.stamina = min(self.max_stamina, self.stamina + amount)

    def gain_skill_xp(self, skill_name, amount=1):
        if skill_name in self.skills:
            self.skills[skill_name] += amount

    def degrade_skills(self):
        for skill in self.skills:
            if self.skills[skill] > 0:
                self.skills[skill] = max(0, self.skills[skill] - 1)

    def is_alive(self):
        return self.hp > 0

    def _on_death(self):
        pass

    def rest(self):
        self.heal(20)
        self.recover_stamina(50)
        self.apply_daily_needs()

    # Combate
    def get_attack_damage(self):
        if self.equipped_weapon is None:
            return random.randint(1, 3)  # desarmado
        atrib = self.equipped_weapon['atributos']
        if atrib.get('tipo') == 'arma_branca':
            return random.randint(*atrib['dano'])
        elif atrib.get('tipo') == 'arma_fogo':
            return random.randint(*atrib['dano'])
        return random.randint(1, 3)
