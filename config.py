import math
import os

# ---------------------------------------------------------------------
# Caminhos (relativos a este arquivo: o jogo roda de qualquer pasta)
# ---------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
ENEMY_IMAGES_DIR = os.path.join(IMAGES_DIR, "enemies")
SFX_DIR = os.path.join(ASSETS_DIR, "sfx")
MUSIC_DIR = os.path.join(ASSETS_DIR, "music")

# Tela
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
FPS = 60

# Arena
ARENA_RADIUS = 900.0
PLAYER_RADIUS = 90.0          # distância mínima entre o jogador e a parede

# Câmera
BASE_FOV = math.radians(70)
MAX_FOV = math.radians(110)
FOV_SMOOTH = 7.0              # velocidade da transição do FOV (power-up de visão)
EYE_HEIGHT = 95.0             # altura dos olhos (unidades do mundo)
RENDER_COLS = 250             # nº de raios/colunas da parede (mais = mais nítido, mais pesado)
NEAR_PLANE = 10.0
MAX_DEPTH = ARENA_RADIUS * 2

# Arena: o fundo (fundo2.png) é repetido em 4 faixas de 90 graus, uma por
# portão. Os portões ficam nos ângulos 0, 90, 180 e 270 graus -- exatamente
# de onde os inimigos saem.
GATE_ANGLES = [0.0, math.pi / 2, math.pi, -math.pi / 2]
WALL_TEXTURE_BASE_ROW = 643   # linha do fundo2.png onde a parede encontra a areia

# Jogador
PLAYER_SPEED = 220.0
PLAYER_TURN_SPEED = 2.4
MOUSE_SENSITIVITY = 0.0025
PLAYER_MAX_HP = 100

# Inimigos (os tipos ficam em enemy.py)
ENEMY_UNITS_PER_PIXEL = 2.3   # tamanho de 1 pixel do sprite no mundo

# Tiro
SHOOT_RANGE = ARENA_RADIUS * 2
SHOOT_COOLDOWN = 0.32
SHOOT_COOLDOWN_RAPID = 0.09
AIM_ASSIST_DEG = 1.2          # tolerância extra de mira (além do tamanho do inimigo)

# Velocidade da bala (unidades/seg) -> define o tempo até o impacto
BULLET_SPEED = 1900.0
BULLET_MIN_TRAVEL_TIME = 0.05

# Power-ups
POWERUP_DROP_CHANCE = 0.30
POWERUP_DURATION = {
    "vision": 8.0,
    "rapid_fire": 7.0,
    "freeze": 4.0,
}
PICKUP_RADIUS = 75.0          # distância para coletar
PICKUP_MAGNET_RADIUS = 220.0  # perto assim, o item é "puxado" até o jogador
PICKUP_MAGNET_SPEED = 360.0
PICKUP_LIFETIME = 15.0        # some depois desse tempo (pisca nos últimos 4s)
PICKUP_MAX_ON_GROUND = 5

# Ondas
FIRST_WAVE_DELAY = 2.2        # pausa antes da rodada 1
INTERMISSION_TIME = 3.2       # pausa entre rodadas (impede a onda de "atropelar" a explosão)

# Explosão (power-up): onda de choque que se espalha a partir do jogador
EXPLOSION_SPEED = 1500.0
EXPLOSION_MAX_RADIUS = ARENA_RADIUS * 2 + 150

# Cores
WHITE = (240, 240, 240)
BLACK = (10, 10, 10)

RED = (200, 40, 40)
DARK_RED = (110, 15, 15)

GREEN = (60, 200, 90)
DARK_GREEN = (25, 110, 50)

YELLOW = (230, 200, 40)
BLUE = (60, 140, 230)
ORANGE = (230, 140, 30)

GREY = (70, 70, 75)
SAND = (150, 120, 80)

SKY_COLOR = (1, 128, 252)         # cor do céu do fundo2.png
FLOOR_FAR = (226, 158, 54)        # areia perto do horizonte
FLOOR_NEAR = (244, 188, 72)       # areia perto do jogador
