"""
sprites.py
==========
Carrega e prepara TODAS as imagens do jogo. Se algum arquivo estiver
faltando, o jogo não quebra: usa um substituto simples e avisa no console.

Arquivos lidos:
    assets/images/fundo2.png            -> parede/arquibancada da arena
    assets/images/arma_costas.png       -> arma (vista de costas)
    assets/images/enemies/<tipo>.png    -> sprite sheet de 6 quadros por inimigo
"""
import math
import os

import pygame

from config import (
    IMAGES_DIR,
    ENEMY_IMAGES_DIR,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    WALL_TEXTURE_BASE_ROW,
    SKY_COLOR,
    FLOOR_FAR,
    FLOOR_NEAR,
    ENEMY_UNITS_PER_PIXEL,
)
from enemy import ENEMY_TYPES
from powerups import POWERUP_COLORS, POWERUP_TYPES

SHEET_FRAMES = 6


def _load(path, alpha=True):
    try:
        img = pygame.image.load(path)
        return img.convert_alpha() if alpha else img.convert()
    except (pygame.error, FileNotFoundError, OSError) as err:
        print(f"[assets] aviso: não consegui carregar {path} ({err})")
        return None


class EnemySprites:
    """Quadros de um tipo de inimigo + variações (branco ao levar tiro, azul congelado)."""

    def __init__(self, frames):
        self.frames = frames
        self.flash = [self._silhouette(f, (255, 255, 255)) for f in frames]
        self.frozen = [self._tint(f, (50, 105, 170)) for f in frames]

        fw, fh = frames[0].get_size()
        self.px_w = fw
        self.px_h = fh
        self.world_h = fh * ENEMY_UNITS_PER_PIXEL
        self.world_w = fw * ENEMY_UNITS_PER_PIXEL

    @staticmethod
    def _silhouette(surf, color):
        mask = pygame.mask.from_surface(surf)
        return mask.to_surface(setcolor=color + (255,), unsetcolor=(0, 0, 0, 0))

    @staticmethod
    def _tint(surf, add):
        out = surf.copy()
        out.fill(add + (0,), special_flags=pygame.BLEND_RGB_ADD)
        return out


class Assets:

    def __init__(self):
        self._load_backdrop()
        self._load_weapon()
        self._load_enemies()
        self._build_icons()
        self._build_glows()
        self._build_overlays()
        self._build_shadow()
        self._build_floor()

    # ------------------------------------------------------------ cenário
    def _load_backdrop(self):
        img = _load(os.path.join(IMAGES_DIR, "fundo2.png"), alpha=False)

        if img is None:
            img = pygame.Surface((1536, WALL_TEXTURE_BASE_ROW))
            img.fill((150, 128, 96))
        else:
            rows = min(WALL_TEXTURE_BASE_ROW, img.get_height())
            img = img.subsurface((0, 0, img.get_width(), rows)).copy()

        # A arena é redonda: o fundo é repetido em 4 faixas (uma por portão).
        # As faixas vizinhas são ESPELHADAS, então as bordas se encaixam sem emenda.
        self.wall_tex = img
        self.wall_tex_flipped = pygame.transform.flip(img, True, False)
        self.wall_w, self.wall_h = img.get_size()

    def _build_floor(self):
        """Fundo base: céu em cima, areia em degradê embaixo."""
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert()
        half = SCREEN_HEIGHT // 2
        bg.fill(SKY_COLOR, (0, 0, SCREEN_WIDTH, half))

        for y in range(half, SCREEN_HEIGHT):
            t = (y - half) / max(1, SCREEN_HEIGHT - half)
            col = tuple(int(FLOOR_FAR[i] + (FLOOR_NEAR[i] - FLOOR_FAR[i]) * t) for i in range(3))
            pygame.draw.line(bg, col, (0, y), (SCREEN_WIDTH, y))

        self.background = bg

    # --------------------------------------------------------------- arma
    def _load_weapon(self):
        img = _load(os.path.join(IMAGES_DIR, "arma_costas.png"))

        if img is None:
            img = pygame.Surface((90, 300), pygame.SRCALPHA)
            pygame.draw.rect(img, (40, 40, 48), (25, 0, 40, 300), border_radius=6)
            pygame.draw.rect(img, (110, 66, 36), (10, 160, 70, 140), border_radius=6)

        self.weapon = img

    # ------------------------------------------------------------ inimigos
    def _load_enemies(self):
        self.enemy = {}

        for kind, spec in ENEMY_TYPES.items():
            sheet = _load(os.path.join(ENEMY_IMAGES_DIR, spec["sheet"] + ".png"))

            if sheet is None:
                fw, fh = 44, 64
                sheet = pygame.Surface((fw * SHEET_FRAMES, fh), pygame.SRCALPHA)
                for i in range(SHEET_FRAMES):
                    pygame.draw.rect(sheet, (190, 40, 40), (i * fw + 10, 6, fw - 20, fh - 8), border_radius=8)

            fw = sheet.get_width() // SHEET_FRAMES
            fh = sheet.get_height()
            frames = [sheet.subsurface((i * fw, 0, fw, fh)).copy() for i in range(SHEET_FRAMES)]

            self.enemy[kind] = EnemySprites(frames)

    # ------------------------------------------------------------- ícones
    def _build_icons(self):
        """Ícones dos power-ups, desenhados por código (32x32)."""
        self.icons = {}

        for kind in POWERUP_TYPES:
            s = pygame.Surface((32, 32), pygame.SRCALPHA)
            c = POWERUP_COLORS[kind]

            if kind == "vision":                 # olho
                pygame.draw.ellipse(s, (255, 255, 255), (2, 8, 28, 16))
                pygame.draw.ellipse(s, c, (2, 8, 28, 16), 3)
                pygame.draw.circle(s, c, (16, 16), 6)
                pygame.draw.circle(s, (10, 20, 50), (16, 16), 3)
                pygame.draw.circle(s, (255, 255, 255), (14, 14), 1)

            elif kind == "rapid_fire":           # raio
                pts = [(19, 1), (6, 18), (14, 18), (11, 31), (26, 12), (17, 12), (21, 1)]
                pygame.draw.polygon(s, (255, 255, 255), pts)
                pygame.draw.polygon(s, c, pts, 3)
                pygame.draw.polygon(s, c, pts)

            elif kind == "freeze":               # floco de neve
                for k in range(3):
                    a = k * math.pi / 3
                    dx, dy = math.cos(a) * 13, math.sin(a) * 13
                    pygame.draw.line(s, c, (16 - dx, 16 - dy), (16 + dx, 16 + dy), 3)
                    for sgn in (-1, 1):
                        ex, ey = 16 + dx * 0.62 * sgn, 16 + dy * 0.62 * sgn
                        for off in (-1, 1):
                            b = a + off * 0.9
                            pygame.draw.line(s, c, (ex, ey), (ex + math.cos(b) * 4 * sgn, ey + math.sin(b) * 4 * sgn), 2)
                pygame.draw.circle(s, (255, 255, 255), (16, 16), 3)

            else:                                # explosão (estrela)
                pts = []
                for k in range(16):
                    r = 15 if k % 2 == 0 else 7
                    a = k * math.pi / 8
                    pts.append((16 + math.cos(a) * r, 16 + math.sin(a) * r))
                pygame.draw.polygon(s, c, pts)
                pygame.draw.polygon(s, (255, 230, 120), [(16 + (x - 16) * 0.55, 16 + (y - 16) * 0.55) for x, y in pts])
                pygame.draw.circle(s, (255, 255, 255), (16, 16), 4)

            self.icons[kind] = s

    def _build_glows(self):
        """Halo radial de cada power-up (usado no item do chão)."""
        self.glows = {}
        size = 64

        for kind in POWERUP_TYPES:
            g = pygame.Surface((size, size), pygame.SRCALPHA)
            c = POWERUP_COLORS[kind]

            for y in range(size):
                for x in range(size):
                    d = math.hypot(x - size / 2 + 0.5, y - size / 2 + 0.5) / (size / 2)
                    if d < 1:
                        a = int(170 * (1 - d) ** 1.8)
                        g.set_at((x, y), c + (a,))

            self.glows[kind] = g

        # coluna de luz que sai do item (ajuda a achá-lo com a visão limitada)
        self.pillars = {}
        for kind in POWERUP_TYPES:
            p = pygame.Surface((8, 64), pygame.SRCALPHA)
            c = POWERUP_COLORS[kind]
            for y in range(64):
                a = int(120 * (y / 63.0) ** 1.4)
                pygame.draw.line(p, c + (a,), (0, y), (7, y))
            self.pillars[kind] = p

    def _build_overlays(self):
        """Vinhetas (escurecimento/vermelho nas bordas) em tela cheia."""

        def vignette(color, power, strength):
            w, h = 64, 40
            small = pygame.Surface((w, h), pygame.SRCALPHA)

            for y in range(h):
                for x in range(w):
                    nx = (x + 0.5) / w * 2 - 1
                    ny = (y + 0.5) / h * 2 - 1
                    d = min(1.0, math.hypot(nx, ny * 1.15) / 1.35)
                    a = int(255 * strength * (d ** power))
                    small.set_at((x, y), color + (min(255, a),))

            return pygame.transform.smoothscale(small, (SCREEN_WIDTH, SCREEN_HEIGHT))

        self.vignette_dark = vignette((0, 0, 0), 2.6, 0.75)
        self.vignette_red = vignette((190, 10, 10), 2.0, 1.0)
        self.vignette_fire = vignette((255, 120, 20), 1.6, 0.9)

        self.flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert()

    def _build_shadow(self):
        w, h = 64, 20
        s = pygame.Surface((w, h), pygame.SRCALPHA)

        for y in range(h):
            for x in range(w):
                d = math.hypot((x + 0.5 - w / 2) / (w / 2), (y + 0.5 - h / 2) / (h / 2))
                if d < 1:
                    s.set_at((x, y), (0, 0, 0, int(120 * (1 - d) ** 0.7)))

        self.shadow = s
