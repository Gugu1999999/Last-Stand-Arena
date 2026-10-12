"""
ui.py
=====
HUD e telas por cima do jogo: vida, rodada, abates, power-ups ativos,
avisos grandes (banner), avisos pequenos (toast), setas para itens fora da
visão, tela de pausa e de fim de jogo.

BANNER e TOAST ficam em posições diferentes da tela de propósito: assim
"EXPLOSÃO!" e "RODADA 5" nunca se sobrepõem.
"""
import math

import pygame

from config import (
    SCREEN_WIDTH as W,
    SCREEN_HEIGHT as H,
    PLAYER_MAX_HP,
    WHITE,
    YELLOW,
    RED,
    ORANGE,
    PICKUP_LIFETIME,
    POWERUP_DURATION,
    EYE_HEIGHT,
)
from powerups import POWERUP_LABELS, POWERUP_COLORS
from enemy import ENEMY_TYPES

SHADOW = (14, 10, 12)


class UI:

    def __init__(self, screen, assets):

        self.screen = screen
        self.assets = assets

        self.font = pygame.font.SysFont("arial", 20, bold=True)
        self.font_small = pygame.font.SysFont("arial", 15, bold=True)
        self.font_big = pygame.font.SysFont("arial", 50, bold=True)
        self.font_huge = pygame.font.SysFont("arial", 68, bold=True)

        self.banner_text = ""
        self.banner_sub = ""
        self.banner_color = YELLOW
        self.banner_t = 0.0
        self.banner_total = 1.0

        self.toasts = []          # [texto, cor, tempo_restante]

        self._text_cache = {}
        self._panel = pygame.Surface((236, 96), pygame.SRCALPHA)
        pygame.draw.rect(self._panel, (10, 8, 14, 150), self._panel.get_rect(), border_radius=10)

        self._dim = pygame.Surface((W, H), pygame.SRCALPHA)

    # ------------------------------------------------------------------
    def banner(self, text, sub="", duration=2.4, color=YELLOW):
        self.banner_text = text
        self.banner_sub = sub
        self.banner_color = color
        self.banner_t = duration
        self.banner_total = duration

    def toast(self, text, color=WHITE, duration=2.2, big=False):
        self.toasts.append([text, color, duration, big])
        self.toasts = self.toasts[-3:]

    def clear(self):
        self.banner_t = 0.0
        self.toasts.clear()

    def update(self, dt):
        self.banner_t = max(0.0, self.banner_t - dt)

        for t in self.toasts:
            t[2] -= dt

        self.toasts = [t for t in self.toasts if t[2] > 0]

    # ------------------------------------------------------------------
    def _render(self, font, text, color):
        key = (id(font), text, color)
        surf = self._text_cache.get(key)

        if surf is None:
            if len(self._text_cache) > 400:
                self._text_cache.clear()
            surf = font.render(text, True, color)
            self._text_cache[key] = surf

        return surf

    def text(self, font, text, color, pos, anchor="topleft", alpha=255, outline=2):
        main = self._render(font, text, color)
        dark = self._render(font, text, SHADOW)
        rect = main.get_rect(**{anchor: pos})

        if alpha < 255:
            main = main.copy()
            main.set_alpha(alpha)
            dark = dark.copy()
            dark.set_alpha(alpha)

        for ox, oy in ((-outline, 0), (outline, 0), (0, -outline), (0, outline), (outline, outline)):
            self.screen.blit(dark, rect.move(ox, oy))

        self.screen.blit(main, rect)
        return rect

    # ==================================================================
    def draw(self, game):

        p = game.player

        self._draw_info_panel(game)
        self._draw_hp(p, game.time)
        self._draw_powerups(p)
        self._draw_pickup_arrows(game)
        self._draw_banner_and_toasts(game)

    def _draw_info_panel(self, game):

        p = game.player
        alive = game.enemies_remaining()

        self.screen.blit(self._panel, (12, 12))
        self.text(self.font, f"RODADA  {max(1, game.round_num)}", YELLOW, (26, 20))
        self.text(self.font, f"Abates: {p.kills}", WHITE, (26, 46))
        self.text(self.font, f"Espartanos: {alive}", (255, 170, 150) if alive else WHITE, (26, 70))

    def _draw_hp(self, p, time):

        x, y, w, h = 20, H - 46, 270, 26
        ratio = max(0.0, p.hp / PLAYER_MAX_HP)

        pygame.draw.rect(self.screen, (24, 8, 10), (x - 3, y - 3, w + 6, h + 6), border_radius=8)
        pygame.draw.rect(self.screen, (80, 18, 20), (x, y, w, h), border_radius=6)

        if ratio > 0:
            color = (214, 52, 48) if ratio > 0.3 else (255, 90, 40)
            if ratio <= 0.3 and int(time * 6) % 2 == 0:
                color = (255, 150, 120)
            pygame.draw.rect(self.screen, color, (x, y, max(6, int(w * ratio)), h), border_radius=6)
            pygame.draw.rect(self.screen, (255, 140, 130), (x + 3, y + 3, max(0, int(w * ratio) - 6), 5), border_radius=3)

        pygame.draw.rect(self.screen, (240, 220, 210), (x, y, w, h), 2, border_radius=6)
        self.text(self.font, f"VIDA  {int(p.hp)}/{PLAYER_MAX_HP}", WHITE, (x + w // 2, y + h // 2), anchor="center")

    def _draw_powerups(self, p):

        x = W - 232
        y = 16

        for name, remaining in p.active_powerups.items():
            color = POWERUP_COLORS[name]
            total = POWERUP_DURATION.get(name, 1.0)
            ratio = max(0.0, min(1.0, remaining / total))

            pygame.draw.rect(self.screen, (10, 8, 14), (x, y, 216, 46), border_radius=9)
            pygame.draw.rect(self.screen, color, (x, y, 216, 46), 2, border_radius=9)
            self.screen.blit(self.assets.icons[name], (x + 8, y + 7))

            self.text(self.font_small, POWERUP_LABELS[name], color, (x + 48, y + 6))
            pygame.draw.rect(self.screen, (50, 44, 52), (x + 48, y + 28, 150, 8), border_radius=4)
            pygame.draw.rect(self.screen, color, (x + 48, y + 28, int(150 * ratio), 8), border_radius=4)

            if remaining < 2.0 and int(remaining * 6) % 2 == 0:      # pisca quando está acabando
                pygame.draw.rect(self.screen, (255, 255, 255), (x, y, 216, 46), 2, border_radius=9)

            y += 54

    def _draw_pickup_arrows(self, game):
        """Setas nas bordas apontando para power-ups que estão fora do campo de visão."""

        p = game.player
        half_fov = p.fov / 2

        for d in game.pickups:
            ang = math.atan2(d.y - p.y, d.x - p.x) - p.angle
            ang = (ang + math.pi) % (2 * math.pi) - math.pi

            if abs(ang) < half_fov * 0.92:
                continue                                  # já está na tela

            if d.blinking:
                continue

            color = POWERUP_COLORS[d.kind]
            dist = math.hypot(d.x - p.x, d.y - p.y)
            side = 1 if ang > 0 else -1                   # direita / esquerda
            ax = W - 34 if side > 0 else 34
            ay = H // 2 + int(math.sin(game.time * 4 + d.bob_phase) * 6)

            pts = [(ax + side * 16, ay), (ax - side * 10, ay - 16), (ax - side * 10, ay + 16)]
            pygame.draw.polygon(self.screen, color, pts, 0)
            pygame.draw.polygon(self.screen, (255, 255, 255), pts, 2)
            self.screen.blit(pygame.transform.scale(self.assets.icons[d.kind], (22, 22)), (ax - 11, ay - 42))
            self.text(self.font_small, f"{int(dist / 10)}m", WHITE, (ax, ay + 28), anchor="center")

    def _draw_banner_and_toasts(self, game):

        # --- banner grande (centro-alto) --------------------------------
        if self.banner_t > 0:
            elapsed = self.banner_total - self.banner_t
            fade_in = min(1.0, elapsed / 0.18)
            fade_out = min(1.0, self.banner_t / 0.45)
            alpha = int(255 * min(fade_in, fade_out))
            slide = int((1.0 - fade_in) * -26)

            self.text(self.font_huge, self.banner_text, self.banner_color, (W // 2, 120 + slide),
                      anchor="center", alpha=alpha, outline=3)

            if self.banner_sub:
                self.text(self.font, self.banner_sub, WHITE, (W // 2, 168 + slide), anchor="center", alpha=alpha)

        # contagem regressiva entre rodadas (abaixo do banner, posição própria)
        if game.wave_state == "intermission" and game.round_num > 0 and game.intermission_timer > 0:
            self.text(self.font, f"Próxima rodada em {game.intermission_timer:0.1f}s", (255, 235, 190),
                      (W // 2, 205), anchor="center")

        # --- avisos pequenos (acima da arma, empilhados) -----------------
        y = H - 150
        for text, color, remaining, big in reversed(self.toasts):
            alpha = int(255 * min(1.0, remaining / 0.5))
            self.text(self.font_big if big else self.font, text, color, (W // 2, y),
                      anchor="center", alpha=alpha, outline=3 if big else 2)
            y -= 54 if big else 30

    # ==================================================================
    def draw_pause(self):
        self._dim.fill((0, 0, 0, 150))
        self.screen.blit(self._dim, (0, 0))
        self.text(self.font_huge, "PAUSADO", WHITE, (W // 2, H // 2 - 50), anchor="center", outline=3)
        self.text(self.font, "Clique (ou ESC) para continuar", (230, 220, 200), (W // 2, H // 2 + 10), anchor="center")
        self.text(self.font_small, "WASD move  |  Mouse mira  |  Clique atira", (200, 190, 180), (W // 2, H // 2 + 46), anchor="center")

    def draw_game_over(self, game):

        t = min(1.0, game.game_over_time / 0.9)

        self._dim.fill((40, 0, 0, int(190 * t)))
        self.screen.blit(self._dim, (0, 0))

        a = int(255 * t)
        self.text(self.font_huge, "FIM DE JOGO", RED, (W // 2, H // 2 - 80), anchor="center", alpha=a, outline=3)
        self.text(self.font, f"Você sobreviveu até a rodada {game.round_num}", WHITE, (W // 2, H // 2 - 22), anchor="center", alpha=a)
        self.text(self.font, f"Espartanos abatidos: {game.player.kills}", WHITE, (W // 2, H // 2 + 10), anchor="center", alpha=a)

        if game.game_over_time > 0.9:
            blink = 255 if int(game.game_over_time * 2) % 2 == 0 else 150
            self.text(self.font, "Pressione R para reiniciar", YELLOW, (W // 2, H // 2 + 62), anchor="center", alpha=blink)
