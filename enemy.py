"""
enemy.py  (substitui o antigo zombie.py)
========================================
Os inimigos agora são ESPARTANOS, com 3 tipos. Para criar/ajustar um tipo,
mexa só no dicionário ENEMY_TYPES (e no sprite sheet correspondente em
assets/images/enemies/<sheet>.png).

Ciclo de vida:  walk -> windup -> recover -> (volta a walk)
                qualquer estado -> dying -> corpse -> removed
"""
import math
import random

from config import ARENA_RADIUS

ENEMY_TYPES = {
    # Soldado básico: equilibrado.
    "hoplita": dict(
        label="Hoplita",
        sheet="hoplita",
        hp=2, hp_per_rounds=6,          # +1 de vida a cada 6 rodadas
        speed_mult=1.0,
        damage=12,
        attack_range=175.0, windup=0.45, recover=0.30, cooldown=0.55,
        hit_radius=30.0, body_radius=32.0,
        weave=0.0,
    ),
    # Rápido e frágil: corre em zigue-zague, difícil de acertar de longe.
    "batedor": dict(
        label="Batedor",
        sheet="batedor",
        hp=1, hp_per_rounds=10,
        speed_mult=1.75,
        damage=8,
        attack_range=140.0, windup=0.28, recover=0.22, cooldown=0.35,
        hit_radius=26.0, body_radius=28.0,
        weave=0.55,
    ),
    # Tanque: lento, muita vida, bate forte.
    "campeao": dict(
        label="Campeão",
        sheet="campeao",
        hp=5, hp_per_rounds=4,
        speed_mult=0.62,
        damage=24,
        attack_range=215.0, windup=0.65, recover=0.40, cooldown=0.80,
        hit_radius=42.0, body_radius=44.0,
        weave=0.0,
    ),
}

CORPSE_FALL_TIME = 0.45     # tempo da animação de queda
CORPSE_LINGER = 1.3         # tempo que o corpo fica no chão
CORPSE_FADE = 0.8           # tempo do sumiço (fade)


class Enemy:

    def __init__(self, kind, x, y, base_speed, round_num=1):

        spec = ENEMY_TYPES[kind]

        self.kind = kind
        self.spec = spec

        self.x = x
        self.y = y

        self.speed = base_speed * spec["speed_mult"]
        self.max_hp = spec["hp"] + round_num // spec["hp_per_rounds"]
        self.hp = self.max_hp

        self.alive = True            # False assim que a vida zera
        self.removed = False         # True quando o corpo sumiu de vez

        self.state = "walk"
        self.state_t = 0.0
        self.attack_cd = random.uniform(0.0, 0.35)

        self.anim_t = random.uniform(0.0, 4.0)
        self.hit_flash = 0.0
        self.weave_phase = random.uniform(0.0, 6.28)

        self.death_t = 0.0
        self.burned = False

    # ------------------------------------------------------------------
    @property
    def radius(self):
        return self.spec["body_radius"]

    @property
    def hit_radius(self):
        return self.spec["hit_radius"]

    def frame_index(self):
        """Quadro do sprite sheet (0-3 andando, 4 preparando, 5 golpe)."""
        if self.state == "windup":
            return 4
        if self.state == "recover":
            return 5
        return int(self.anim_t) % 4

    # ------------------------------------------------------------------
    def take_hit(self, damage, from_x, from_y):
        """Retorna True se este tiro matou o inimigo."""
        if not self.alive:
            return False

        self.hp -= damage
        self.hit_flash = 0.12

        # pequeno empurrão para trás (peso diferente por tipo)
        dx = self.x - from_x
        dy = self.y - from_y
        dist = math.hypot(dx, dy) or 1.0
        push = 16.0 if self.kind != "campeao" else 6.0
        self.x += dx / dist * push
        self.y += dy / dist * push

        if self.hp <= 0:
            self.die()
            return True

        # levar um tiro interrompe o golpe que estava sendo preparado
        if self.state == "windup":
            self.state = "walk"
            self.state_t = 0.0
            self.attack_cd = max(self.attack_cd, 0.25)

        return False

    def die(self, burned=False):
        if not self.alive:
            return
        self.alive = False
        self.hp = 0
        self.state = "dying"
        self.death_t = 0.0
        self.burned = burned

    # ------------------------------------------------------------------
    def update(self, dt, player, frozen):
        """Retorna True no frame em que o golpe acerta o jogador."""

        self.hit_flash = max(0.0, self.hit_flash - dt)

        if not self.alive:
            self.death_t += dt
            if self.death_t >= CORPSE_FALL_TIME + CORPSE_LINGER + CORPSE_FADE:
                self.removed = True
            return False

        if frozen:
            return False

        spec = self.spec

        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy) or 0.0001
        nx, ny = dx / dist, dy / dist

        self.attack_cd = max(0.0, self.attack_cd - dt)
        self.state_t += dt
        hit_player = False

        if self.state == "walk":

            if dist > spec["attack_range"]:
                vx, vy = nx, ny

                if spec["weave"] > 0:       # zigue-zague (batedor)
                    self.weave_phase += dt * 5.0
                    side = math.sin(self.weave_phase) * spec["weave"]
                    vx += -ny * side
                    vy += nx * side
                    norm = math.hypot(vx, vy) or 1.0
                    vx, vy = vx / norm, vy / norm

                self.x += vx * self.speed * dt
                self.y += vy * self.speed * dt
                self.anim_t += dt * (5.0 + self.speed * 0.035)

            elif self.attack_cd <= 0:
                self.state = "windup"
                self.state_t = 0.0

        elif self.state == "windup":
            # O inimigo "avisa" antes de bater: dá tempo de atirar ou recuar
            if self.state_t >= spec["windup"]:
                if dist <= spec["attack_range"] * 1.25:
                    player.take_damage(spec["damage"])
                    hit_player = True
                self.state = "recover"
                self.state_t = 0.0

        elif self.state == "recover":
            if self.state_t >= spec["recover"]:
                self.state = "walk"
                self.state_t = 0.0
                self.attack_cd = spec["cooldown"]

        # nunca sai da arena
        r = math.hypot(self.x, self.y)
        limit = ARENA_RADIUS - 25.0
        if r > limit:
            self.x *= limit / r
            self.y *= limit / r

        return hit_player


def separate_enemies(enemies):
    """Empurra inimigos que ficaram um em cima do outro (evita 'pilha')."""

    living = [e for e in enemies if e.alive]

    for i in range(len(living)):
        a = living[i]

        for j in range(i + 1, len(living)):
            b = living[j]

            dx = b.x - a.x
            dy = b.y - a.y
            min_dist = a.radius + b.radius
            d2 = dx * dx + dy * dy

            if d2 >= min_dist * min_dist:
                continue

            if d2 < 1e-6:
                dx, dy, d2 = random.uniform(-1, 1), random.uniform(-1, 1), 1.0

            d = math.sqrt(d2)
            push = (min_dist - d) * 0.5
            ux, uy = dx / d, dy / d

            a.x -= ux * push
            a.y -= uy * push
            b.x += ux * push
            b.y += uy * push
