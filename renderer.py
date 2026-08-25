import math
import pygame

from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    ARENA_RADIUS,
    RENDER_COLS,
    MAX_DEPTH,
    GREY,
    SAND,
    WHITE,
    GREEN,
    DARK_GREEN,
)

from utils import (
    norm_angle,
    ray_circle_distance,
)


class Renderer:

    def __init__(self, screen):

        self.screen = screen

    def render(self, player, zombies):

        screen = self.screen

        half_h = SCREEN_HEIGHT // 2

        screen.fill(
            GREY,
            (0, 0, SCREEN_WIDTH, half_h)
        )

        screen.fill(
            SAND,
            (0, half_h, SCREEN_WIDTH, half_h)
        )

        fov = player.fov

        col_width = SCREEN_WIDTH / RENDER_COLS

        z_buffer = [MAX_DEPTH] * RENDER_COLS

        # Paredes

        for col in range(RENDER_COLS):

            cam_t = (col / RENDER_COLS) - 0.5

            ray_angle = (
                player.angle +
                cam_t * fov
            )

            dx = math.cos(ray_angle)
            dy = math.sin(ray_angle)

            distance = ray_circle_distance(
                player.x,
                player.y,
                dx,
                dy,
                ARENA_RADIUS,
            )

            corrected = (
                distance *
                math.cos(ray_angle - player.angle)
            )

            corrected = max(
                corrected,
                0.0001
            )

            z_buffer[col] = corrected

            wall_h = min(
                SCREEN_HEIGHT,
                (SCREEN_HEIGHT * 260) / corrected
            )

            shade = max(
                0.15,
                1.0 - corrected / ARENA_RADIUS
            )

            color = (
                int(GREY[0] * shade + 40 * (1 - shade)),
                int(GREY[1] * shade + 20 * (1 - shade)),
                int(GREY[2] * shade + 20 * (1 - shade)),
            )

            x = int(col * col_width)

            pygame.draw.rect(
                screen,
                color,
                (
                    x,
                    int(half_h - wall_h / 2),
                    math.ceil(col_width) + 1,
                    int(wall_h),
                ),
            )

        # Zumbis

        visible = []

        for zombie in zombies:

            if not zombie.alive:
                continue

            dx = zombie.x - player.x
            dy = zombie.y - player.y

            distance = math.hypot(dx, dy)

            angle = norm_angle(
                math.atan2(dy, dx) -
                player.angle
            )

            if (
                abs(angle) < fov / 2 + 0.15
                and distance > 1
            ):
                visible.append(
                    (distance, angle, zombie)
                )

        visible.sort(
            key=lambda item: -item[0]
        )

        for distance, angle, zombie in visible:

            screen_x = (
                SCREEN_WIDTH / 2 +
                math.tan(angle) *
                (SCREEN_WIDTH / 2) /
                math.tan(fov / 2)
            )

            col = int(
                screen_x /
                SCREEN_WIDTH *
                RENDER_COLS
            )

            col = max(
                0,
                min(RENDER_COLS - 1, col)
            )

            if distance > z_buffer[col] + 6:
                continue

            size = min(
                SCREEN_HEIGHT * 1.1,
                (SCREEN_HEIGHT * 130) / distance
            )

            top = half_h - size / 2

            color = (
                WHITE
                if zombie.hit_flash > 0
                else DARK_GREEN
            )

            body_color = (
                WHITE
                if zombie.hit_flash > 0
                else GREEN
            )

            pygame.draw.rect(
                screen,
                color,
                (
                    screen_x - size * 0.16,
                    top + size * 0.32,
                    size * 0.32,
                    size * 0.5,
                ),
            )

            pygame.draw.circle(
                screen,
                body_color,
                (
                    int(screen_x),
                    int(top + size * 0.22),
                ),
                max(
                    2,
                    int(size * 0.16)
                ),
            )

            pygame.draw.line(
                screen,
                color,
                (
                    screen_x - size * 0.16,
                    top + size * 0.4,
                ),
                (
                    screen_x - size * 0.32,
                    top + size * 0.65,
                ),
                max(1, int(size * 0.04)),
            )

            pygame.draw.line(
                screen,
                color,
                (
                    screen_x + size * 0.16,
                    top + size * 0.4,
                ),
                (
                    screen_x + size * 0.32,
                    top + size * 0.65,
                ),
                max(1, int(size * 0.04)),
            )

        self.draw_weapon()
        self.draw_crosshair()

    def draw_weapon(self):

        gun_w = 140
        gun_h = 170

        gx = SCREEN_WIDTH / 2 - gun_w / 2
        gy = SCREEN_HEIGHT - gun_h + 40

        pygame.draw.rect(
            self.screen,
            (40, 40, 40),
            (
                gx + 30,
                gy,
                40,
                120,
            ),
            border_radius=6,
        )

        pygame.draw.rect(
            self.screen,
            (25, 25, 25),
            (
                gx + 15,
                gy + 90,
                70,
                30,
            ),
            border_radius=4,
        )

    def draw_crosshair(self):

        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2

        pygame.draw.line(
            self.screen,
            WHITE,
            (center_x - 10, center_y),
            (center_x + 10, center_y),
            2,
        )

        pygame.draw.line(
            self.screen,
            WHITE,
            (center_x, center_y - 10),
            (center_x, center_y + 10),
            2,
        )