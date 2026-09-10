import math

from config import BULLET_SPEED, BULLET_MIN_TRAVEL_TIME


class Bullet:
    """
    Representa um projetil em voo entre o jogador e o zumbi alvo.

    O alvo eh travado no instante do disparo (mira instantanea), mas o dano
    so eh aplicado quando a bala "chega" no alvo, respeitando o tempo de
    trajeto calculado a partir da distancia e de BULLET_SPEED.
    """

    def __init__(self, x, y, target):

        self.start_x = x
        self.start_y = y

        self.target = target

        self.target_x = target.x
        self.target_y = target.y

        distance = math.hypot(
            self.target_x - x,
            self.target_y - y,
        )

        self.travel_time = max(
            distance / BULLET_SPEED,
            BULLET_MIN_TRAVEL_TIME,
        )

        self.timer = self.travel_time

    @property
    def progress(self):

        if self.travel_time <= 0:
            return 1.0

        return 1.0 - max(0.0, self.timer) / self.travel_time

    @property
    def x(self):
        return self.start_x + (
            self.target_x - self.start_x
        ) * self.progress

    @property
    def y(self):
        return self.start_y + (
            self.target_y - self.start_y
        ) * self.progress

    def update(self, dt):
        """Retorna True quando a bala chega ao destino."""

        self.timer -= dt

        return self.timer <= 0
