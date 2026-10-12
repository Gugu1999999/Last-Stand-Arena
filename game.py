import math
import random

import pygame

from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    ARENA_RADIUS,
    EYE_HEIGHT,
    SHOOT_RANGE,
    SHOOT_COOLDOWN,
    SHOOT_COOLDOWN_RAPID,
    AIM_ASSIST_DEG,
    POWERUP_DROP_CHANCE,
    PICKUP_RADIUS,
    PICKUP_MAX_ON_GROUND,
    FIRST_WAVE_DELAY,
    INTERMISSION_TIME,
    ORANGE,
    RED,
)
from player import Player
from enemy import Enemy, separate_enemies
from waves import WaveManager
from shoot import Bullet
from powerups import PowerUpDrop, roll_powerup, POWERUP_LABELS, POWERUP_COLORS
from effects import ParticleSystem, Decals, ScreenFX, Shockwave
from sprites import Assets
from renderer import Renderer
from ui import UI
from audio import AudioManager
from utils import ray_circle_distance


class Game:
    """
    Estados:  "playing" | "paused" | "game_over"
    Dentro de "playing" a onda tem 2 fases (wave_state):
        "intermission" -> pausa entre rodadas (contagem regressiva)
        "active"       -> inimigos nascendo / lutando
    """

    def __init__(self):

        pygame.init()
        pygame.display.set_caption("Last Stand Arena")

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        self.audio = AudioManager()
        self.assets = Assets()                # precisa vir DEPOIS do display (convert_alpha)
        self.renderer = Renderer(self.screen, self.assets)
        self.ui = UI(self.screen, self.assets)
        self.decals = Decals()

        self.mouse_locked = False
        self.mouse_held = False
        self.fps_timer = 0.0

        self.reset()
        self.audio.play_music()

    # ==================================================================
    #  CONTROLE DE PARTIDA
    # ==================================================================
    def reset(self):

        self.player = Player()

        self.enemies = []
        self.bullets = []
        self.pickups = []

        self.particles = ParticleSystem()
        self.fx = ScreenFX()
        self.decals.clear_stains()
        self.shockwave = None

        self.wave_manager = WaveManager()
        self.round_num = 0
        self.spawn_queue = []
        self.wave_time = 0.0
        self.base_speed = 0.0
        self.champion_warned = False

        self.wave_state = "intermission"
        self.intermission_timer = FIRST_WAVE_DELAY

        self.time = 0.0
        self.game_over_time = 0.0
        self.state = "playing"

        self.ui.clear()
        self.ui.banner("PREPARE-SE", "Os portões da arena vão se abrir...", 2.0)

        self.mouse_held = False
        self.set_mouse_lock(True)

        if self.audio.enabled and getattr(self, "_music_started", False):
            self.audio.play_music()

        self._music_started = True

    def set_mouse_lock(self, locked):
        self.mouse_locked = locked
        pygame.event.set_grab(locked)
        pygame.mouse.set_visible(not locked)

    def toggle_pause(self):

        if self.state == "playing":
            self.state = "paused"
            self.mouse_held = False
            self.set_mouse_lock(False)
            self.audio.pause_music()

        elif self.state == "paused":
            self.state = "playing"
            self.set_mouse_lock(True)
            self.audio.resume_music()

    def game_over(self):
        self.state = "game_over"
        self.game_over_time = 0.0
        self.mouse_held = False
        self.set_mouse_lock(False)
        self.fx.shake(10, 0.5)
        self.audio.stop_music()
        self.audio.play("game_over")

    def enemies_remaining(self):
        return sum(1 for e in self.enemies if e.alive) + len(self.spawn_queue)

    # ==================================================================
    #  ONDAS
    # ==================================================================
    def start_next_round(self):

        self.spawn_queue, self.base_speed = self.wave_manager.start_next_round()
        self.round_num = self.wave_manager.round_num
        self.player.round_num = self.round_num

        self.wave_time = 0.0
        self.champion_warned = False
        self.wave_state = "active"

        self.ui.banner(f"RODADA {self.round_num}", f"{len(self.spawn_queue)} espartanos a caminho", 2.4)
        self.audio.play("round_start")

    def finish_wave(self):
        """Todos mortos: pausa antes da próxima rodada (nunca começa em cima da explosão)."""

        self.wave_state = "intermission"
        self.intermission_timer = INTERMISSION_TIME

        self.ui.banner("ARENA LIMPA", f"Rodada {self.round_num} concluída", 2.2, color=(140, 230, 150))

    def spawn_enemy(self, order):

        x, y = WaveManager.spawn_position(order.gate_angle)

        self.enemies.append(Enemy(order.kind, x, y, self.base_speed, self.round_num))
        self.particles.dust(x, y, n=10, spread=60.0, big=True)

        if order.kind == "campeao" and not self.champion_warned:
            self.champion_warned = True
            self.ui.toast("CAMPEÃO ESPARTANO!", RED, 2.4)

    def update_wave(self, dt):

        if self.wave_state == "intermission":

            self.intermission_timer -= dt

            if self.intermission_timer <= 0:
                self.start_next_round()

            return

        self.wave_time += dt

        while self.spawn_queue and self.spawn_queue[0].time <= self.wave_time:
            self.spawn_enemy(self.spawn_queue.pop(0))

        wave_over = (
            not self.spawn_queue
            and not any(e.alive for e in self.enemies)
            and self.shockwave is None            # espera a explosão terminar
        )

        if wave_over:
            self.finish_wave()

    # ==================================================================
    #  TIRO
    # ==================================================================
    def try_shoot(self):

        p = self.player

        if self.state != "playing" or p.shoot_timer > 0:
            return

        rapid = p.has_powerup("rapid_fire")

        p.shoot_timer = SHOOT_COOLDOWN_RAPID if rapid else SHOOT_COOLDOWN
        p.recoil = 1.0
        p.muzzle_flash = 0.07

        self.audio.play_shoot()

        fx, fy = p.dir_x, p.dir_y
        tolerance = math.tan(math.radians(AIM_ASSIST_DEG))

        target = None
        best = SHOOT_RANGE

        for e in self.enemies:

            if not e.alive:
                continue

            dx = e.x - p.x
            dy = e.y - p.y

            along = dx * fx + dy * fy                   # distância ao longo da mira

            if along <= 0 or along >= best:
                continue

            perp = abs(dx * fy - dy * fx)               # quão longe da linha de mira

            if perp <= e.hit_radius + along * tolerance:
                target = e
                best = along

        if target is not None:
            self.bullets.append(Bullet(p.x, p.y, target=target))
        else:
            d = ray_circle_distance(p.x, p.y, fx, fy, ARENA_RADIUS)
            self.bullets.append(Bullet(p.x, p.y, end=(p.x + fx * d, p.y + fy * d)))

    def update_bullets(self, dt):

        p = self.player
        remaining = []

        for b in self.bullets:

            if not b.update(dt):
                remaining.append(b)
                continue

            t = b.target

            if t is None:                                    # tiro perdido: poeira na parede
                ex, ey = b.end
                self.particles.dust(ex, ey, n=3, spread=30.0)
                self.particles.sparks(ex, ey, EYE_HEIGHT, 3)

            elif t.alive:
                killed = t.take_hit(1, p.x, p.y)

                p.hit_marker = 0.16
                p.hit_marker_kill = killed

                # o sangue espirra em direção ao jogador
                self.particles.sparks(t.x, t.y, EYE_HEIGHT * 0.7, 4)
                self.particles.blood(t.x, t.y, EYE_HEIGHT * 0.7, 2 * t.x - p.x, 2 * t.y - p.y,
                                     n=16 if killed else 7)

                if killed:
                    self.on_enemy_killed(t, "bullet")
                else:
                    self.audio.play("hit")

        self.bullets = remaining

    # ==================================================================
    #  MORTES E POWER-UPS
    # ==================================================================
    def on_enemy_killed(self, enemy, cause):

        self.player.kills += 1

        size = 52.0 if enemy.kind == "campeao" else 34.0
        self.decals.add_blood(enemy.x, enemy.y, size, burned=(cause == "explosion"))
        self.particles.dust(enemy.x, enemy.y, n=5, spread=40.0)
        self.audio.play("kill")

        # só quem morre a tiro solta item (a explosão não gera itens em cadeia)
        if (
            cause == "bullet"
            and len(self.pickups) < PICKUP_MAX_ON_GROUND
            and random.random() < POWERUP_DROP_CHANCE
        ):
            kind = roll_powerup()
            self.pickups.append(PowerUpDrop(kind, enemy.x, enemy.y))
            self.particles.sparkle(enemy.x, enemy.y, 40.0, POWERUP_COLORS[kind], n=12)

    def update_pickups(self, dt):

        p = self.player
        keep = []

        for d in self.pickups:

            d.update(dt, p)

            if d.expired:
                continue

            if math.hypot(d.x - p.x, d.y - p.y) <= PICKUP_RADIUS:
                self.collect_pickup(d)
                continue

            keep.append(d)

        self.pickups = keep

    def collect_pickup(self, drop):

        color = POWERUP_COLORS[drop.kind]

        self.particles.sparkle(drop.x, drop.y, 40.0, color, n=22)
        self.fx.flash(color, 0.30, 3.2)
        self.audio.play("powerup")

        self.apply_powerup(drop.kind)

    def apply_powerup(self, kind):

        if kind == "explosion":
            self.trigger_explosion()
            return

        self.player.add_powerup(kind)
        self.ui.toast(f"{POWERUP_LABELS[kind]}!", POWERUP_COLORS[kind], 2.0)

    def trigger_explosion(self):
        """
        Cria uma onda de choque que sai do jogador. Os inimigos morrem quando a
        onda passa por eles (ver update_shockwave). A fila de inimigos que
        ainda não nasceram também é cancelada: a explosão encerra a rodada.
        """

        p = self.player

        self.shockwave = Shockwave(p.x, p.y)
        self.spawn_queue.clear()

        self.fx.flash((255, 205, 120), 0.9, 1.5)
        self.fx.shake(15, 1.0)
        self.fx.heat = 1.0

        self.ui.toast("EXPLOSÃO!", ORANGE, 1.8, big=True)
        self.audio.play_explosion()

    def update_shockwave(self, dt):

        sw = self.shockwave

        if sw is None:
            return

        sw.advance(dt)

        for e in self.enemies:
            if e.alive and math.hypot(e.x - sw.x, e.y - sw.y) <= sw.radius:
                e.die(burned=True)
                self.particles.fire(e.x, e.y, 0.0, n=16)
                self.particles.blood(e.x, e.y, 60.0, e.x, e.y, n=6)
                self.on_enemy_killed(e, "explosion")

        if sw.done:
            self.shockwave = None

    # ==================================================================
    #  UPDATE
    # ==================================================================
    def update(self, dt):

        if self.state == "paused":
            return

        self.time += dt

        p = self.player

        if self.state == "game_over":
            self.game_over_time += dt
            p.update(dt)
            self.fx.update(dt)
            self.particles.update(dt)
            self.ui.update(dt)
            return

        p.update(dt)
        self.fx.update(dt)
        self.particles.update(dt)
        self.ui.update(dt)

        p.handle_movement(dt, pygame.key.get_pressed())

        if self.mouse_held and p.has_powerup("rapid_fire"):
            self.try_shoot()

        self.update_pickups(dt)
        self.update_bullets(dt)
        self.update_shockwave(dt)
        self.update_wave(dt)

        frozen = p.has_powerup("freeze")

        for e in self.enemies:
            if e.update(dt, p, frozen):
                self.fx.shake(7, 0.3)
                self.audio.play_zombie_attack()
                self.audio.play("hurt")

        separate_enemies(self.enemies)
        self.enemies = [e for e in self.enemies if not e.removed]

        if p.hp <= 0:
            self.game_over()

    # ==================================================================
    #  LOOP PRINCIPAL
    # ==================================================================
    def handle_event(self, event):

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                self.toggle_pause()

            elif event.key == pygame.K_r and self.state == "game_over":
                self.reset()

        elif event.type == pygame.MOUSEMOTION:

            if self.state == "playing" and self.mouse_locked:
                self.player.rotate_mouse(event.rel[0])

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            if self.state == "paused":
                self.toggle_pause()                  # o clique que "volta" ao jogo não atira

            elif self.state == "playing":
                self.mouse_held = True
                self.try_shoot()

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.mouse_held = False

        elif event.type == getattr(pygame, "WINDOWFOCUSLOST", -1):
            if self.state == "playing":
                self.toggle_pause()                  # perdeu o foco: pausa sozinho

    def run(self):

        running = True

        while running:

            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.handle_event(event)

            self.update(dt)

            self.renderer.render(self)
            self.ui.draw(self)

            if self.state == "paused":
                self.ui.draw_pause()
            elif self.state == "game_over":
                self.ui.draw_game_over(self)

            pygame.display.flip()

            self.fps_timer += dt
            if self.fps_timer >= 0.5:
                self.fps_timer = 0.0
                pygame.display.set_caption(f"Last Stand Arena  -  {self.clock.get_fps():.0f} FPS")

        pygame.quit()
