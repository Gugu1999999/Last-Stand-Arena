import random
import sys

import pygame

import math

from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    PLAYER_MAX_HP,
    SHOOT_RANGE,
    SHOOT_COOLDOWN,
    SHOOT_COOLDOWN_RAPID,
    SHOOT_ANGLE_TOLERANCE,
    POWERUP_DROP_CHANCE,
    MAX_FOV,
)

from player import Player
from waves import WaveManager
from renderer import Renderer
from ui import UI
from utils import norm_angle
from shoot import Bullet
from powerups import (
    POWERUP_TYPES,
    POWERUP_LABELS,
    POWERUP_WEIGHTS,
)


class Game:

    def __init__(self):

        pygame.init()

        pygame.display.set_caption(
            "Last Stand Arena"
        )

        self.screen = pygame.display.set_mode(
            (
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
            )
        )

        self.clock = pygame.time.Clock()

        self.mouse_locked = True

        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

        self.player = Player()

        self.zombies = []
        self.bullets = []
        self.powerups = []

        self.mouse_held = False

        self.wave_manager = WaveManager(
            self.zombies
        )

        self.renderer = Renderer(
            self.screen
        )

        self.ui = UI(
            self.screen
        )

        self.notification = ""
        self.notification_timer = 0

        self.state = "playing"

        self.reset()

    def reset(self):

        self.player = Player()

        self.zombies.clear()
        self.bullets.clear()
        self.powerups.clear()

        self.mouse_held = False

        self.wave_manager = WaveManager(
            self.zombies
        )

        self.state = "playing"

        self.notification = ""
        self.notification_timer = 0

        self.start_next_round()

    def start_next_round(self, explosion=False):

        self.wave_manager.start_next_round()

        self.player.round_num = (
            self.wave_manager.round_num
        )
        if explosion:
            self.notify(
                f"XXXXX {self.wave_manager.round_num} - EXPLOSÃO!"
            )
        self.notify(
            f"RODADA {self.wave_manager.round_num}"
        )

    def notify(
        self,
        text,
        duration=2.2,
    ):

        self.notification = text
        self.notification_timer = duration

    def update(self, dt):

        if self.state == "game_over":
            return

        self.player.update_powerups(dt)

        self.player.shoot_timer = max(
            0,
            self.player.shoot_timer - dt
        )

        if self.notification_timer > 0:

            self.notification_timer -= dt

        keys = pygame.key.get_pressed()

        self.player.handle_movement(
            dt,
            keys,

        self.collect_powerups()
        )

        # Tiro contínuo: enquanto o botão estiver pressionado e o
        # power-up "rapid_fire" estiver ativo, dispara automaticamente
        # a cada frame (o próprio try_shoot respeita o cooldown).
        if (
            self.mouse_held
            and self.player.has_powerup("rapid_fire")
        ):
            self.try_shoot()

        self.update_bullets(dt)

        frozen = self.player.has_powerup(
            "freeze"
        )

        alive_count = 0

        for zombie in self.zombies:

            zombie.update(
                dt,
                self.player,
                frozen,
            )

            if zombie.alive:
                alive_count += 1

        if self.player.hp <= 0:

            self.player.hp = 0

            self.state = "game_over"

            return

        if alive_count == 0:

            self.zombies.clear()

            self.start_next_round()

            

    def try_shoot(self):

        # Cooldown entre um tiro e outro: precisa SEMPRE ser respeitado,
        # com ou sem "tiro contínuo" ativo. O que muda com o power-up é
        # apenas o valor do cooldown (bem mais curto), nunca se ele existe.
        if self.player.shoot_timer > 0:
            return

        if self.player.has_powerup(
            "rapid_fire"
        ):
            self.player.shoot_timer = SHOOT_COOLDOWN_RAPID
        else:
            self.player.shoot_timer = SHOOT_COOLDOWN

        best_zombie = None

        best_distance = SHOOT_RANGE

        for zombie in self.zombies:

            if not zombie.alive:
                continue

            dx = zombie.x - self.player.x
            dy = zombie.y - self.player.y

            distance = (
                dx * dx +
                dy * dy
            ) ** 0.5

            angle = norm_angle(
                math.atan2(dy, dx)
                - self.player.angle
            )

            if (
                abs(angle)
                <= SHOOT_ANGLE_TOLERANCE
                and distance < best_distance
            ):

                best_distance = distance
                best_zombie = zombie

        if best_zombie:

            # A mira trava no alvo na hora do disparo, mas o impacto só
            # acontece quando a bala "viaja" até lá (ver update_bullets).
            self.bullets.append(
                Bullet(
                    self.player.x,
                    self.player.y,
                    best_zombie,
                )
            )

    def update_bullets(self, dt):

        remaining = []

        for bullet in self.bullets:

            arrived = bullet.update(dt)

            if not arrived:
                remaining.append(bullet)
                continue

            target = bullet.target

            # O alvo pode ter morrido enquanto a bala viajava
            # (ex.: power-up de explosão). Nesse caso não conta de novo.
            if target.alive:

                target.hit_flash = 0.15

                # Qualquer zumbi que tome um tiro morre — a bala que
                # chega ao alvo é sempre um abate garantido.
                self.kill_zombie(target)

        self.bullets = remaining

    def kill_zombie(self, zombie):

        zombie.alive = False

        self.player.kills += 1

        if random.random() < POWERUP_DROP_CHANCE:

            powerup = random.choices(
                POWERUP_TYPES,
                weights=[
                    POWERUP_WEIGHTS[name]
                    for name in POWERUP_TYPES
                ],
                k=1,
            )[0]

            self.apply_powerup(
                powerup
            )

    def apply_powerup(self, name):

        if name == "explosion":

            count = 0

            for zombie in self.zombies:

                if zombie.alive:

                    zombie.alive = False

                    count += 1

            self.player.kills += count

            self.notify(
                "EXPLOSÃO! Arena limpa"
            )

        else:

            self.player.add_powerup(
                name
            )

            if name == "vision":

                self.player.fov = MAX_FOV

            self.notify(
                f"Power-up: {POWERUP_LABELS[name]}"
            )

    def run(self):

        running = True

        while running:

            dt = (
                self.clock.tick(FPS)
                / 1000.0
            )

            dt = min(
                dt,
                0.05
            )

            for event in pygame.event.get():

                if event.type == pygame.QUIT:

                    running = False

                elif event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_ESCAPE:

                        self.mouse_locked = (
                            not self.mouse_locked
                        )

                        pygame.event.set_grab(
                            self.mouse_locked
                        )

                        pygame.mouse.set_visible(
                            not self.mouse_locked
                        )

                    elif (
                        event.key == pygame.K_r
                        and self.state == "game_over"
                    ):

                        self.reset()

                elif (
                    event.type == pygame.MOUSEMOTION
                    and self.mouse_locked
                ):

                    self.player.rotate_mouse(
                        event.rel[0]
                    )

                elif (
                    event.type
                    == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                ):

                    self.mouse_held = True

                    if self.state == "playing":

                        self.try_shoot()

                elif (
                    event.type
                    == pygame.MOUSEBUTTONUP
                    and event.button == 1
                ):

                    self.mouse_held = False

            self.update(dt)

            self.renderer.render(
                self.player,
                self.zombies,
                self.bullets,
            )

            self.ui.draw(
                self.player,
                self.wave_manager.round_num,
                self.zombies,
                self.state,
                self.notification,
                self.notification_timer,
            )

            pygame.display.flip()

        pygame.quit()

        sys.exit()