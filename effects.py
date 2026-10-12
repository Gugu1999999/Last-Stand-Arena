"""
effects.py
==========
Efeitos visuais do jogo (nada aqui altera regras de jogo, só "suco"):

  - ParticleSystem : sangue, faíscas, poeira, fogo, brilhos (partículas no mundo 3D)
  - Decals         : marcas no chão (grãos de areia/pedras para dar noção de
                     movimento + manchas de sangue onde os inimigos caem)
  - ScreenFX       : flash de tela e tremor de câmera
  - Shockwave      : onda de choque da explosão (anel que se expande pelo chão)
"""
import math
import random

from config import ARENA_RADIUS, EXPLOSION_SPEED, EXPLOSION_MAX_RADIUS


# ======================================================================
#  PARTÍCULAS
# ======================================================================
class Particle:
    __slots__ = ("x", "y", "z", "vx", "vy", "vz", "life", "max_life",
                 "size", "color", "gravity", "drag", "shrink")

    def __init__(self, x, y, z, vx, vy, vz, life, size, color, gravity, drag=0.0, shrink=True):
        self.x, self.y, self.z = x, y, z
        self.vx, self.vy, self.vz = vx, vy, vz
        self.life = self.max_life = life
        self.size = size
        self.color = color
        self.gravity = gravity
        self.drag = drag
        self.shrink = shrink


class ParticleSystem:

    LIMIT = 500

    def __init__(self):
        self.items = []

    def clear(self):
        self.items.clear()

    def add(self, *args, **kwargs):
        if len(self.items) < self.LIMIT:
            self.items.append(Particle(*args, **kwargs))

    def update(self, dt):
        alive = []

        for p in self.items:
            p.life -= dt

            if p.life <= 0:
                continue

            if p.drag:
                k = max(0.0, 1.0 - p.drag * dt)
                p.vx *= k
                p.vy *= k

            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vz -= p.gravity * dt
            p.z += p.vz * dt

            if p.z < 0:                       # quicou no chão
                p.z = 0.0
                p.vz *= -0.25
                p.vx *= 0.6
                p.vy *= 0.6

            alive.append(p)

        self.items = alive

    # ---------------------------------------------------------- presets
    def blood(self, x, y, z, from_x, from_y, n=10):
        """Sangue espirrando para longe de (from_x, from_y)."""
        base = math.atan2(y - from_y, x - from_x)

        for _ in range(n):
            a = base + random.uniform(-0.9, 0.9)
            s = random.uniform(70, 260)
            shade = random.randint(0, 50)
            self.add(x, y, z, math.cos(a) * s, math.sin(a) * s, random.uniform(40, 230),
                     random.uniform(0.45, 0.9), random.uniform(3, 6.5),
                     (150 + shade, 14 + shade // 3, 18), 650, 0.5)

    def sparks(self, x, y, z, n=6):
        for _ in range(n):
            a = random.uniform(0, 6.283)
            s = random.uniform(90, 300)
            self.add(x, y, z, math.cos(a) * s, math.sin(a) * s, random.uniform(40, 200),
                     random.uniform(0.15, 0.35), random.uniform(2, 3.5),
                     random.choice([(255, 240, 150), (255, 190, 60), (255, 255, 255)]), 520)

    def dust(self, x, y, n=8, spread=45.0, big=False):
        for _ in range(n):
            a = random.uniform(0, 6.283)
            s = random.uniform(10, spread)
            self.add(x + random.uniform(-14, 14), y + random.uniform(-14, 14), random.uniform(2, 14),
                     math.cos(a) * s, math.sin(a) * s, random.uniform(20, 70),
                     random.uniform(0.5, 1.0), random.uniform(10, 22) * (1.5 if big else 1.0),
                     random.choice([(236, 196, 120), (214, 168, 92), (250, 218, 150)]), -40, 1.2)

    def fire(self, x, y, z, n=14):
        """Bola de fogo + fumaça (inimigo atingido pela explosão)."""
        for _ in range(n):
            a = random.uniform(0, 6.283)
            s = random.uniform(30, 190)
            hot = random.random() < 0.7
            color = random.choice([(255, 230, 110), (255, 160, 40), (255, 100, 30)]) if hot \
                else random.choice([(70, 60, 56), (110, 98, 90)])
            self.add(x, y, z + random.uniform(0, 70), math.cos(a) * s, math.sin(a) * s,
                     random.uniform(60, 260), random.uniform(0.5, 1.1),
                     random.uniform(9, 20), color, -60 if not hot else 120, 1.0)

    def sparkle(self, x, y, z, color, n=18):
        """Brilho ao coletar um power-up."""
        for _ in range(n):
            a = random.uniform(0, 6.283)
            s = random.uniform(60, 230)
            self.add(x, y, z, math.cos(a) * s, math.sin(a) * s, random.uniform(80, 260),
                     random.uniform(0.4, 0.8), random.uniform(3, 6), color, 420, 0.8)


# ======================================================================
#  MARCAS NO CHÃO
# ======================================================================
class Decals:
    """Manchas no chão. As de areia são fixas (dão noção de movimento ao andar)."""

    MAX_STAINS = 70

    def __init__(self):
        rng = random.Random(1234)
        self.static = []          # (x, y, largura, tipo)   tipo: 0 claro, 1 escuro, 2 pedra

        for _ in range(300):
            a = rng.uniform(0, 6.283)
            r = math.sqrt(rng.random()) * (ARENA_RADIUS - 30)
            kind = rng.choice([0, 0, 1, 1, 1, 2]) if rng.random() < 0.97 else 2
            width = rng.uniform(7, 20) if kind != 2 else rng.uniform(16, 30)
            self.static.append((math.cos(a) * r, math.sin(a) * r, width, kind))

        self.stains = []          # (x, y, largura, cor)

    def clear_stains(self):
        self.stains.clear()

    def add_blood(self, x, y, size=34.0, burned=False):
        color = (60, 44, 36) if burned else (140, 26, 28)
        self.stains.append((x, y, size * random.uniform(0.8, 1.3), color))
        self.stains.append((x + random.uniform(-26, 26), y + random.uniform(-26, 26),
                            size * random.uniform(0.3, 0.6), color))

        if len(self.stains) > self.MAX_STAINS:
            del self.stains[: len(self.stains) - self.MAX_STAINS]


# ======================================================================
#  EFEITOS DE TELA
# ======================================================================
class ScreenFX:

    def __init__(self):
        self.flash_color = (255, 255, 255)
        self.flash_alpha = 0.0
        self.flash_decay = 2.5

        self.shake_amp = 0.0
        self.shake_time = 0.0
        self.shake_total = 0.001

        self.heat = 0.0            # tom alaranjado após a explosão (1 -> 0)

    def flash(self, color, alpha=0.6, decay=2.5):
        self.flash_color = color
        self.flash_alpha = max(self.flash_alpha, alpha)
        self.flash_decay = decay

    def shake(self, amplitude, duration):
        if amplitude >= self.shake_amp * (self.shake_time / self.shake_total if self.shake_total else 0):
            self.shake_amp = amplitude
            self.shake_time = duration
            self.shake_total = duration

    def update(self, dt):
        self.flash_alpha = max(0.0, self.flash_alpha - self.flash_decay * dt)
        self.shake_time = max(0.0, self.shake_time - dt)
        self.heat = max(0.0, self.heat - dt * 0.7)

    def shake_offset(self):
        if self.shake_time <= 0:
            return 0, 0

        k = self.shake_time / self.shake_total
        amp = self.shake_amp * k

        return int(random.uniform(-amp, amp)), int(random.uniform(-amp, amp))

    def reset(self):
        self.flash_alpha = 0.0
        self.shake_time = 0.0
        self.heat = 0.0


# ======================================================================
#  ONDA DE CHOQUE (power-up de explosão)
# ======================================================================
class Shockwave:
    """
    A explosão NÃO mata todo mundo no mesmo frame: a onda sai do jogador e
    vai varrendo a arena; cada inimigo morre no instante em que a onda passa
    por ele. Isso dá tempo de o efeito aparecer e evita que a próxima rodada
    "atropele" a explosão.
    """

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 0.0
        self.done = False

    def advance(self, dt):
        self.radius += EXPLOSION_SPEED * dt

        if self.radius >= EXPLOSION_MAX_RADIUS:
            self.done = True

    @property
    def progress(self):
        return min(1.0, self.radius / EXPLOSION_MAX_RADIUS)
