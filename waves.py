import math
import random

from config import ARENA_RADIUS
from zombie import Zombie


class WaveManager:

    def __init__(self, zombies):

        self.zombies = zombies
        self.round_num = 0

    def start_next_round(self):

        self.round_num += 1

        count = 4 + self.round_num * 2

        speed = 55 + self.round_num * 6

        speed = min(speed, 230)

        self.spawn_wave(count, speed)

    def spawn_wave(self, count, speed):

        base_dirs = [
            0,
            math.pi / 2,
            math.pi,
            -math.pi / 2,
        ]

        for _ in range(count):

            base = random.choice(base_dirs)

            angle = base + random.uniform(
                -0.35,
                0.35
            )

            radius = ARENA_RADIUS - 5

            x = math.cos(angle) * radius
            y = math.sin(angle) * radius

            hp = 1 + self.round_num // 5

            zombie = Zombie(
                x,
                y,
                speed * random.uniform(0.9, 1.1),
                hp,
            )

            self.zombies.append(zombie)