import math
import pygame

from config import (
    ARENA_RADIUS,
    PLAYER_RADIUS,
    PLAYER_SPEED,
    PLAYER_TURN_SPEED,
    MOUSE_SENSITIVITY,
    PLAYER_MAX_HP,
    BASE_FOV,
    MAX_FOV,
    FOV_SMOOTH,
    POWERUP_DURATION,
)


class Player:

    def __init__(self):
        self.x = 0.0
        self.y = 0.0

        self.angle = 0.0

        self.hp = PLAYER_MAX_HP

        self.fov = BASE_FOV

        self.shoot_timer = 0.0

        self.kills = 0
        self.round_num = 1

        self.active_powerups = {}

        # Feedback visual (usado só pelo renderer/ui)
        self.recoil = 0.0          # coice da arma (1 -> 0)
        self.muzzle_flash = 0.0    # clarão do tiro
        self.damage_flash = 0.0    # tela vermelha ao levar dano
        self.hit_marker = 0.0      # "X" na mira ao acertar
        self.hit_marker_kill = False
        self.bob_phase = 0.0       # balanço da arma ao andar
        self.bob_amount = 0.0
        self.turn_velocity = 0.0   # a arma "arrasta" ao girar a câmera

    # ------------------------------------------------------------------
    @property
    def dir_x(self):
        return math.cos(self.angle)

    @property
    def dir_y(self):
        return math.sin(self.angle)

    def has_powerup(self, name):
        return self.active_powerups.get(name, 0) > 0

    def add_powerup(self, name):
        # Pegar o mesmo power-up de novo apenas renova o tempo (não acumula)
        self.active_powerups[name] = POWERUP_DURATION.get(name, 0)

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)
        self.damage_flash = 1.0

    # ------------------------------------------------------------------
    def update(self, dt):
        """Timers e efeitos que não dependem de input."""

        for name in list(self.active_powerups.keys()):
            self.active_powerups[name] -= dt

            if self.active_powerups[name] <= 0:
                del self.active_powerups[name]

        # O FOV muda suavemente (e não "pula") ao pegar/perder a visão ampliada
        target_fov = MAX_FOV if self.has_powerup("vision") else BASE_FOV
        self.fov += (target_fov - self.fov) * min(1.0, FOV_SMOOTH * dt)

        self.shoot_timer = max(0.0, self.shoot_timer - dt)
        self.recoil = max(0.0, self.recoil - dt * 7.0)
        self.muzzle_flash = max(0.0, self.muzzle_flash - dt)
        self.damage_flash = max(0.0, self.damage_flash - dt * 1.6)
        self.hit_marker = max(0.0, self.hit_marker - dt)
        self.turn_velocity *= max(0.0, 1.0 - dt * 10.0)

    def handle_movement(self, dt, keys):

        move_x = 0.0
        move_y = 0.0

        forward_x = math.cos(self.angle)
        forward_y = math.sin(self.angle)

        right_x = math.cos(self.angle + math.pi / 2)
        right_y = math.sin(self.angle + math.pi / 2)

        if keys[pygame.K_w]:
            move_x += forward_x
            move_y += forward_y

        if keys[pygame.K_s]:
            move_x -= forward_x
            move_y -= forward_y

        if keys[pygame.K_a]:
            move_x -= right_x
            move_y -= right_y

        if keys[pygame.K_d]:
            move_x += right_x
            move_y += right_y

        if keys[pygame.K_LEFT]:
            self.angle -= PLAYER_TURN_SPEED * dt
            self.turn_velocity -= 40 * dt

        if keys[pygame.K_RIGHT]:
            self.angle += PLAYER_TURN_SPEED * dt
            self.turn_velocity += 40 * dt

        self.angle %= 2 * math.pi

        length = math.hypot(move_x, move_y)

        moving = length > 0

        if moving:

            move_x /= length
            move_y /= length

            new_x = self.x + move_x * PLAYER_SPEED * dt
            new_y = self.y + move_y * PLAYER_SPEED * dt

            distance = math.hypot(new_x, new_y)
            max_distance = ARENA_RADIUS - PLAYER_RADIUS

            if distance > max_distance:
                scale = max_distance / distance
                new_x *= scale
                new_y *= scale

            self.x = new_x
            self.y = new_y

        # balanço da arma
        if moving:
            self.bob_phase += dt * 9.5
            self.bob_amount = min(1.0, self.bob_amount + dt * 6.0)
        else:
            self.bob_amount = max(0.0, self.bob_amount - dt * 5.0)

    def rotate_mouse(self, dx):
        self.angle = (self.angle + dx * MOUSE_SENSITIVITY) % (2 * math.pi)
        self.turn_velocity += dx * 0.25
