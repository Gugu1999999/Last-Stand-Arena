import math
import random

from config import (
    PICKUP_LIFETIME,
    PICKUP_MAGNET_RADIUS,
    PICKUP_MAGNET_SPEED,
)

POWERUP_TYPES = [
    "vision",
    "rapid_fire",
    "freeze",
    "explosion",
]

POWERUP_LABELS = {
    "vision": "VISÃO AMPLIADA",
    "rapid_fire": "TIRO CONTÍNUO",
    "freeze": "PARALISAÇÃO",
    "explosion": "EXPLOSÃO",
}

# Peso relativo de cada power-up dentro do sorteio (quanto maior, mais chance).
POWERUP_WEIGHTS = {
    "vision": 1,
    "rapid_fire": 1,
    "freeze": 1,
    "explosion": 2,
}

# Cor de cada power-up (item no chão, brilho, HUD)
POWERUP_COLORS = {
    "vision": (80, 160, 255),
    "rapid_fire": (255, 220, 50),
    "freeze": (110, 225, 255),
    "explosion": (255, 110, 50),
}


def roll_powerup():
    return random.choices(
        POWERUP_TYPES,
        weights=[POWERUP_WEIGHTS[name] for name in POWERUP_TYPES],
        k=1,
    )[0]


class PowerUpDrop:
    """Item solto no chão por um inimigo morto. Precisa ser coletado."""

    def __init__(self, kind, x, y):
        self.kind = kind
        self.x = x
        self.y = y
        self.age = 0.0
        self.bob_phase = random.uniform(0.0, 6.28)

    @property
    def time_left(self):
        return PICKUP_LIFETIME - self.age

    @property
    def expired(self):
        return self.age >= PICKUP_LIFETIME

    @property
    def blinking(self):
        return self.time_left < 4.0 and int(self.age * 6) % 2 == 0

    def update(self, dt, player):
        self.age += dt
        self.bob_phase += dt * 3.2

        # "Ímã": perto do jogador, o item voa até ele (evita ter que pisar
        # exatamente em cima, o que era impossível antes).
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)

        if 0 < dist < PICKUP_MAGNET_RADIUS:
            pull = PICKUP_MAGNET_SPEED * (1.0 + (1.0 - dist / PICKUP_MAGNET_RADIUS) * 1.5)
            step = min(dist, pull * dt)
            self.x += dx / dist * step
            self.y += dy / dist * step
