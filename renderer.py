"""
renderer.py
===========
Desenha um frame completo do jogo em primeira pessoa.

Como funciona o ray casting aqui:
  1. Para cada coluna da tela lançamos um raio a partir do jogador.
  2. A distância até a parede circular da arena é calculada com a interseção
     raio-círculo (utils.ray_circle_distance).
  3. Essa distância define a altura da faixa da parede (perto = alta) e
     QUAL pedaço do fundo2.png aparece naquela coluna (a imagem é "colada"
     na parede da arena, então os portões ficam sempre nos mesmos lugares).
  4. Inimigos, itens, partículas e balas são "billboards" projetados com a
     mesma câmera, ordenados do mais longe para o mais perto.
"""
import math
import random

import pygame

from config import (
    SCREEN_WIDTH as W,
    SCREEN_HEIGHT as H,
    ARENA_RADIUS,
    RENDER_COLS,
    EYE_HEIGHT,
    NEAR_PLANE,
    WHITE,
)
from enemy import CORPSE_FALL_TIME, CORPSE_LINGER, CORPSE_FADE
from powerups import POWERUP_COLORS
from utils import norm_angle

TWO_PI = 2 * math.pi
HALF_PI = math.pi / 2
QUARTER_PI = math.pi / 4
WALL_MIN_DEPTH = 60.0          # evita ampliar demais a parede colada no jogador
HALF_H = H // 2


class Renderer:

    def __init__(self, screen, assets):

        self.screen = screen
        self.assets = assets

        self.world = pygame.Surface((W, H)).convert()

        n = RENDER_COLS
        self.col_x = [int(i * W / n) for i in range(n + 1)]

        # quantas unidades do mundo cabem em 1 pixel do fundo2.png
        self.wall_units = ARENA_RADIUS * HALF_PI / assets.wall_w

        self.time = 0.0
        self._cached_fov = None
        self._col_phi = []
        self._col_cos = []
        self._set_camera(0, 0, 0, 70)

    # ------------------------------------------------------------------
    def _set_camera(self, x, y, angle, fov):
        self.cam_x = x
        self.cam_y = y
        self.fx = math.cos(angle)
        self.fy = math.sin(angle)
        self.rx = -self.fy
        self.ry = self.fx
        self.f = (W / 2) / math.tan(fov / 2)        # distância focal em pixels

    def project(self, wx, wy, wz):
        """Mundo -> tela. Retorna (x, y, profundidade) ou None se estiver atrás."""
        dx = wx - self.cam_x
        dy = wy - self.cam_y
        depth = dx * self.fx + dy * self.fy

        if depth < NEAR_PLANE:
            return None

        side = dx * self.rx + dy * self.ry

        return (
            W / 2 + side / depth * self.f,
            HALF_H + (EYE_HEIGHT - wz) / depth * self.f,
            depth,
        )

    # ------------------------------------------------------------------
    def render(self, game):

        player = game.player
        surf = self.world

        self.time = game.time
        self._set_camera(player.x, player.y, player.angle, player.fov)

        surf.blit(self.assets.background, (0, 0))

        self._walls(surf, player)
        self._decals(surf, game)

        if game.shockwave:
            self._shockwave(surf, game.shockwave)

        self._billboards(surf, game)
        self._particles(surf, game)
        self._bullets(surf, game)
        self._weapon(surf, player)
        self._crosshair(surf, player)
        self._overlays(surf, game)

        ox, oy = game.fx.shake_offset()

        if ox or oy:
            self.screen.fill((0, 0, 0))

        self.screen.blit(surf, (ox, oy))

    # ==================================================================
    #  PAREDES (ray casting)
    # ==================================================================
    def _walls(self, surf, player):

        assets = self.assets
        n = RENDER_COLS
        tex_w = assets.wall_w
        tex_h = assets.wall_h
        tan_half = math.tan(player.fov / 2)
        f = self.f

        px, py, pa = player.x, player.y, player.angle

        # ângulo de cada coluna em relação ao centro da tela (só muda se o FOV mudar)
        if self._cached_fov is None or abs(self._cached_fov - player.fov) > 1e-5:
            self._cached_fov = player.fov
            self._col_phi = []
            self._col_cos = []
            for i in range(n):
                xc = (self.col_x[i] + self.col_x[i + 1]) * 0.5
                phi = math.atan((xc / (W / 2) - 1.0) * tan_half)
                self._col_phi.append(phi)
                self._col_cos.append(math.cos(phi))

        # 1) um raio por coluna
        rays = []
        cos, sin, atan2, sqrt = math.cos, math.sin, math.atan2, math.sqrt
        c0 = px * px + py * py - ARENA_RADIUS * ARENA_RADIUS

        for i in range(n):
            ray = pa + self._col_phi[i]

            dx = cos(ray)
            dy = sin(ray)

            # interseção raio-círculo (mesma conta de utils.ray_circle_distance, inline p/ ganhar velocidade)
            b = 2 * (px * dx + py * dy)
            disc = b * b - 4 * c0
            dist = (-b + sqrt(disc)) / 2 if disc > 0 else ARENA_RADIUS
            if dist < 0.0001:
                dist = 0.0001

            depth = max(dist * self._col_cos[i], WALL_MIN_DEPTH)     # corrige "olho de peixe"
            wall_angle = atan2(py + dy * dist, px + dx * dist)       # onde a parede foi atingida

            rays.append((depth, wall_angle))

        # 2) uma faixa de textura por coluna
        for i in range(n):

            depth, wall_angle = rays[i]

            s = (wall_angle + QUARTER_PI) % TWO_PI
            seg = int(s // HALF_PI)
            local = (s - seg * HALF_PI) / HALF_PI

            tex = assets.wall_tex if seg % 2 == 0 else assets.wall_tex_flipped

            other = rays[i + 1][1] if i + 1 < n else rays[i - 1][1]
            strip = max(1, min(48, int(round(abs(norm_angle(other - wall_angle)) * tex_w / HALF_PI))))

            sx0 = int(local * tex_w - strip / 2)
            sx0 = max(0, min(tex_w - strip, sx0))

            kv = f * self.wall_units / depth                    # pixels de tela por pixel de textura
            base_y = HALF_H + f * EYE_HEIGHT / depth            # onde a parede toca o chão
            top_y = base_y - tex_h * kv

            sy0 = max(0, int(-top_y / kv))
            sy1 = min(tex_h, int(math.ceil((H - top_y) / kv)))

            if sy1 <= sy0:
                continue

            x0 = self.col_x[i]
            w = self.col_x[i + 1] - x0
            dest_h = max(1, int(round((sy1 - sy0) * kv)))

            piece = tex.subsurface((sx0, sy0, strip, sy1 - sy0))
            surf.blit(pygame.transform.scale(piece, (w, dest_h)), (x0, int(round(top_y + sy0 * kv))))

    # ==================================================================
    #  MARCAS NO CHÃO
    # ==================================================================
    def _flat_ellipse(self, surf, wx, wy, width, color):
        pr = self.project(wx, wy, 0)

        if pr is None:
            return

        sx, sy, depth = pr
        w = self.f * width / depth

        if w < 1.5 or sx < -w or sx > W + w or depth > 1700:
            return

        h = max(1.0, w * min(0.6, EYE_HEIGHT / depth))

        pygame.draw.ellipse(surf, color, (sx - w / 2, sy - h / 2, w, h))

    def _decals(self, surf, game):

        cols = ((255, 218, 122), (198, 134, 42), (150, 110, 68))

        for (x, y, width, kind) in game.decals.static:
            self._flat_ellipse(surf, x, y, width, cols[kind])

            if kind == 2:                                       # pedra: pequeno brilho no topo
                self._flat_ellipse(surf, x - width * 0.12, y, width * 0.55, (196, 156, 108))

        for (x, y, width, color) in game.decals.stains:
            self._flat_ellipse(surf, x, y, width, color)

    # ==================================================================
    #  ONDA DE CHOQUE DA EXPLOSÃO
    # ==================================================================
    def _shockwave(self, surf, sw):

        r = sw.radius

        if r < 40:
            return

        steps = 140
        pts = []

        for k in range(steps + 1):
            a = k / steps * TWO_PI
            pts.append(self.project(sw.x + math.cos(a) * r, sw.y + math.sin(a) * r, 0))

        fade = 1.0 - sw.progress * 0.6

        for layer, (color, mult) in enumerate((((255, 110, 30), 1.0), ((255, 190, 70), 0.55), ((255, 250, 220), 0.22))):
            for k in range(steps):
                a, b = pts[k], pts[k + 1]

                if a is None or b is None:
                    continue

                if max(abs(a[0] - W / 2), abs(b[0] - W / 2)) > W * 2:
                    continue

                width = max(2, int(self.f * 46 * mult * fade / a[2]))
                pygame.draw.line(surf, color, (a[0], a[1]), (b[0], b[1]), width)

    # ==================================================================
    #  BILLBOARDS: inimigos e itens
    # ==================================================================
    def _billboards(self, surf, game):

        items = []

        for e in game.enemies:
            if e.removed:
                continue
            pr = self.project(e.x, e.y, 0)
            if pr:
                items.append((pr[2], 0, e, pr))

        for d in game.pickups:
            pr = self.project(d.x, d.y, 0)
            if pr:
                items.append((pr[2], 1, d, pr))

        items.sort(key=lambda t: -t[0])

        frozen = game.player.has_powerup("freeze")

        for depth, kind, obj, pr in items:
            if kind == 0:
                self._enemy(surf, obj, pr, frozen)
            else:
                self._pickup(surf, obj, pr)

    def _blit_scaled(self, surf, src, left, top, w, h, alpha=255):
        """Desenha `src` esticado em (left, top, w, h) recortando só o que aparece na tela."""

        w = int(round(w))
        h = int(round(h))

        if w < 1 or h < 1:
            return

        cl = max(0, int(left))
        ct = max(0, int(top))
        cr = min(W, int(left) + w)
        cb = min(H, int(top) + h)

        if cr <= cl or cb <= ct:
            return

        sw, sh = src.get_size()

        sx0 = max(0, int((cl - left) * sw / w))
        sx1 = min(sw, max(sx0 + 1, int(math.ceil((cr - left) * sw / w))))
        sy0 = max(0, int((ct - top) * sh / h))
        sy1 = min(sh, max(sy0 + 1, int(math.ceil((cb - top) * sh / h))))

        dl = left + sx0 * w / sw
        dt = top + sy0 * h / sh
        dw = max(1, int(round((sx1 - sx0) * w / sw)))
        dh = max(1, int(round((sy1 - sy0) * h / sh)))

        piece = pygame.transform.scale(src.subsurface((sx0, sy0, sx1 - sx0, sy1 - sy0)), (dw, dh))

        if alpha < 255:
            piece.set_alpha(alpha)

        surf.blit(piece, (int(round(dl)), int(round(dt))))

    def _enemy(self, surf, e, pr, frozen):

        sx, feet_y, depth = pr
        spr = self.assets.enemy[e.kind]

        scale = self.f / depth
        w = spr.world_w * scale
        h = spr.world_h * scale

        if sx + w / 2 < 0 or sx - w / 2 > W:
            return

        squash = 1.0
        widen = 1.0
        alpha = 255
        frame = e.frame_index()

        if not e.alive:                              # queda e desaparecimento do corpo
            ft = min(1.0, e.death_t / CORPSE_FALL_TIME)
            ease = 1 - (1 - ft) ** 2
            squash = 1 - 0.88 * ease
            widen = 1 + 0.28 * ease
            frame = 0

            fade_t = e.death_t - CORPSE_FALL_TIME - CORPSE_LINGER
            if fade_t > 0:
                alpha = int(255 * max(0.0, 1 - fade_t / CORPSE_FADE))

        # sombra no chão
        sh_w = max(4, int(spr.world_w * 0.62 * scale * widen))
        sh_h = max(2, int(sh_w * min(0.5, EYE_HEIGHT / depth * 0.9)))
        shadow = pygame.transform.scale(self.assets.shadow, (sh_w, sh_h))
        if alpha < 255:
            shadow.set_alpha(alpha)
        surf.blit(shadow, (int(sx - sh_w / 2), int(feet_y - sh_h / 2)))

        if e.alive and e.hit_flash > 0:
            src = spr.flash[frame]
        elif e.alive and frozen:
            src = spr.frozen[frame]
        else:
            src = spr.frames[frame]

        ww = w * widen
        hh = h * squash

        self._blit_scaled(surf, src, sx - ww / 2, feet_y - hh, ww, hh, alpha)

    def _pickup(self, surf, d, pr):

        if d.blinking:
            return

        sx, ground_y, depth = pr
        scale = self.f / depth

        if sx < -200 or sx > W + 200:
            return

        color = POWERUP_COLORS[d.kind]
        hover = 46 + math.sin(d.bob_phase) * 10
        cy = ground_y - hover * scale
        pulse = 1.0 + 0.08 * math.sin(self.time * 6.0)
        r = max(7, 27 * scale * pulse)

        # coluna de luz
        ph = min(H * 1.5, 340 * scale)
        pw = max(4, 26 * scale)
        pillar = pygame.transform.scale(self.assets.pillars[d.kind], (int(pw), int(max(2, ph))))
        surf.blit(pillar, (int(sx - pw / 2), int(ground_y - ph)))

        # sombra e anel no chão
        ring_w = max(6, 70 * scale)
        ring_h = max(3, ring_w * min(0.5, EYE_HEIGHT / depth * 0.9))
        pygame.draw.ellipse(surf, color, (sx - ring_w / 2, ground_y - ring_h / 2, ring_w, ring_h), max(1, int(ring_w * 0.06)))

        # halo
        glow_s = int(r * 4.2)
        if glow_s > 2:
            surf.blit(pygame.transform.smoothscale(self.assets.glows[d.kind], (glow_s, glow_s)),
                      (int(sx - glow_s / 2), int(cy - glow_s / 2)))

        # orbe com ícone
        pygame.draw.circle(surf, (22, 24, 36), (int(sx), int(cy)), int(r))
        pygame.draw.circle(surf, color, (int(sx), int(cy)), int(r), max(2, int(r * 0.16)))

        icon_s = int(r * 1.35)
        if icon_s > 3:
            surf.blit(pygame.transform.scale(self.assets.icons[d.kind], (icon_s, icon_s)),
                      (int(sx - icon_s / 2), int(cy - icon_s / 2)))

    # ==================================================================
    #  PARTÍCULAS E BALAS
    # ==================================================================
    def _particles(self, surf, game):

        for q in game.particles.items:
            pr = self.project(q.x, q.y, q.z)

            if pr is None or pr[2] > 2200:
                continue

            sx, sy, depth = pr
            life = q.life / q.max_life if q.shrink else 1.0
            size = max(1, int(self.f * q.size * (0.35 + 0.65 * life) / depth))

            if -size < sx < W + size and -size < sy < H + size:
                surf.fill(q.color, (int(sx - size / 2), int(sy - size / 2), size, size))

    def _bullets(self, surf, game):

        mx, my = W / 2, H - 262          # ponta do cano na tela

        for b in game.bullets:

            head = self.project(*b.position_at(b.progress))

            if head is None or head[2] < 70:
                continue

            tail = self.project(*b.position_at(b.progress - 0.035 / b.travel_time))

            if tail is None or tail[2] < 70:
                tail = (mx, my, 0)

            width = max(2, int(self.f * 3.2 / head[2]))

            pygame.draw.line(surf, (255, 190, 70), (tail[0], tail[1]), (head[0], head[1]), width + 2)
            pygame.draw.line(surf, (255, 250, 200), (tail[0], tail[1]), (head[0], head[1]), width)
            pygame.draw.circle(surf, (255, 255, 255), (int(head[0]), int(head[1])), max(2, width))

    # ==================================================================
    #  ARMA, MIRA E OVERLAYS
    # ==================================================================
    def _weapon(self, surf, p):

        img = self.assets.weapon
        ow, oh = img.get_size()

        rec = p.recoil
        scale = 300.0 / oh * (1.0 + 0.06 * rec)

        ww = int(ow * scale)
        hh = int(oh * scale)

        bob = p.bob_amount
        bx = math.sin(p.bob_phase) * 15 * bob
        by = abs(math.cos(p.bob_phase)) * 11 * bob
        sway = max(-70.0, min(70.0, -p.turn_velocity * 3.0))

        left = W / 2 - ww / 2 + bx + sway
        top = H - hh + 70 + by + rec * 34

        surf.blit(pygame.transform.scale(img, (ww, hh)), (int(left), int(top)))

        if p.muzzle_flash > 0:
            self._muzzle_flash(surf, left + ww / 2, top + 4, p.muzzle_flash / 0.07)

    def _muzzle_flash(self, surf, cx, cy, t):

        t = max(0.0, min(1.0, t))
        r = 54 * (0.55 + 0.45 * t)
        spikes = 10
        rnd = random.Random(int(self.time * 60))

        for scale, color in ((1.0, (255, 140, 30)), (0.68, (255, 222, 110)), (0.36, (255, 255, 255))):
            pts = []
            for k in range(spikes * 2):
                ang = k * math.pi / spikes + rnd.uniform(-0.08, 0.08)
                rad = r * scale * (rnd.uniform(0.85, 1.2) if k % 2 == 0 else 0.42)
                pts.append((cx + math.cos(ang) * rad, cy + math.sin(ang) * rad))
            pygame.draw.polygon(surf, color, pts)

    def _crosshair(self, surf, p):

        cx, cy = W // 2, H // 2

        for color, width, gap, ln in (((10, 10, 10), 4, 5, 13), (WHITE, 2, 5, 12)):
            pygame.draw.line(surf, color, (cx - gap - ln, cy), (cx - gap, cy), width)
            pygame.draw.line(surf, color, (cx + gap, cy), (cx + gap + ln, cy), width)
            pygame.draw.line(surf, color, (cx, cy - gap - ln), (cx, cy - gap), width)
            pygame.draw.line(surf, color, (cx, cy + gap), (cx, cy + gap + ln), width)

        if p.hit_marker > 0:                         # "X" ao acertar (vermelho se matou)
            color = (255, 70, 60) if p.hit_marker_kill else (255, 255, 255)
            d1, d2 = 9, 20
            for sx in (-1, 1):
                for sy in (-1, 1):
                    pygame.draw.line(surf, color, (cx + sx * d1, cy + sy * d1), (cx + sx * d2, cy + sy * d2), 3)

    def _overlays(self, surf, game):

        a = self.assets
        p = game.player
        fx = game.fx

        # campo de visão limitado: bordas escuras (mais tensão)
        surf.blit(a.vignette_dark, (0, 0))

        if p.has_powerup("freeze"):
            a.flash_surface.fill((90, 170, 255))
            a.flash_surface.set_alpha(34)
            surf.blit(a.flash_surface, (0, 0))

        if fx.heat > 0:
            a.vignette_fire.set_alpha(int(255 * min(1.0, fx.heat)))
            surf.blit(a.vignette_fire, (0, 0))

        red = p.damage_flash * 0.95
        if p.hp <= 30 and p.hp > 0:                       # vida baixa: borda pulsando
            red = max(red, 0.30 + 0.20 * math.sin(self.time * 5.0))

        if red > 0:
            a.vignette_red.set_alpha(int(255 * min(1.0, red)))
            surf.blit(a.vignette_red, (0, 0))

        if fx.flash_alpha > 0:
            a.flash_surface.fill(fx.flash_color)
            a.flash_surface.set_alpha(int(255 * min(1.0, fx.flash_alpha)))
            surf.blit(a.flash_surface, (0, 0))
