import math

from config import (
    ZOMBIE_DAMAGE,
    ZOMBIE_ATTACK_RANGE,
    ZOMBIE_ATTACK_COOLDOWN,
)


class Zombie:

    def __init__(self, x, y, speed, hp=1):

        self.x = x
        self.y = y

        self.speed = speed
        self.hp = hp

        self.alive = True

        self.attack_timer = 0.0
        self.hit_flash = 0.0

    def update(self, dt, player, frozen):

        if not self.alive:
            return

        self.hit_flash = max(
            0.0,
            self.hit_flash - dt
        )

        if frozen:
            return

        dx = player.x - self.x
        dy = player.y - self.y

        distance = math.hypot(dx, dy)

        if distance > ZOMBIE_ATTACK_RANGE:

            if distance > 0:

                dx /= distance
                dy /= distance

            self.x += dx * self.speed * dt
            self.y += dy * self.speed * dt

        else:

            self.attack_timer -= dt

            if self.attack_timer <= 0:

                player.hp -= ZOMBIE_DAMAGE

                self.attack_timer = ZOMBIE_ATTACK_COOLDOWN