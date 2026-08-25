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

    def has_powerup(self, name):
        return self.active_powerups.get(name, 0) > 0

    def add_powerup(self, name):
        self.active_powerups[name] = POWERUP_DURATION.get(
            name,
            0
        )

    def update_powerups(self, dt):

        for name in list(self.active_powerups.keys()):

            self.active_powerups[name] -= dt

            if self.active_powerups[name] <= 0:
                del self.active_powerups[name]

        if self.has_powerup("vision"):
            self.fov = MAX_FOV
        else:
            self.fov = BASE_FOV

    def handle_movement(self, dt, keys):

        move_x = 0.0
        move_y = 0.0

        forward_x = math.cos(self.angle)
        forward_y = math.sin(self.angle)

        right_x = math.cos(
            self.angle + math.pi / 2
        )
        right_y = math.sin(
            self.angle + math.pi / 2
        )

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

        if keys[pygame.K_RIGHT]:
            self.angle += PLAYER_TURN_SPEED * dt

        length = math.hypot(
            move_x,
            move_y
        )

        if length > 0:

            move_x /= length
            move_y /= length

            new_x = (
                self.x +
                move_x * PLAYER_SPEED * dt
            )

            new_y = (
                self.y +
                move_y * PLAYER_SPEED * dt
            )

            distance = math.hypot(
                new_x,
                new_y
            )

            max_distance = (
                ARENA_RADIUS -
                PLAYER_RADIUS
            )

            if distance > max_distance:

                scale = (
                    max_distance /
                    distance
                )

                new_x *= scale
                new_y *= scale

            self.x = new_x
            self.y = new_y

    def rotate_mouse(self, dx):

        self.angle += (
            dx *
            MOUSE_SENSITIVITY
        )