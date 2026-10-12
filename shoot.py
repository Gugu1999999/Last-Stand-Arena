import math

from config import BULLET_SPEED, BULLET_MIN_TRAVEL_TIME, EYE_HEIGHT


class Bullet:
    """
    Projétil em voo.

    O alvo é travado no instante do disparo (mira instantânea), mas o dano só
    é aplicado quando a bala "chega", respeitando o tempo de trajeto
    calculado a partir da distância e de BULLET_SPEED.

    Se `target` for None, é um tiro perdido: a bala voa até `end` (a parede).
    """

    START_Z = EYE_HEIGHT - 32.0

    def __init__(self, x, y, target=None, end=None):

        self.start_x = x
        self.start_y = y

        self.target = target
        self.end = end if end is not None else (x, y)

        ex, ey, ez = self._end_point()

        distance = math.hypot(ex - x, ey - y)

        self.travel_time = max(distance / BULLET_SPEED, BULLET_MIN_TRAVEL_TIME)
        self.timer = self.travel_time

    def _end_point(self):
        if self.target is not None:
            # a bala acompanha o alvo, então nunca "erra" quem foi mirado
            return self.target.x, self.target.y, EYE_HEIGHT * 0.7
        return self.end[0], self.end[1], EYE_HEIGHT

    @property
    def progress(self):
        if self.travel_time <= 0:
            return 1.0
        return 1.0 - max(0.0, self.timer) / self.travel_time

    def position_at(self, progress):
        """Posição (x, y, z) da bala numa fração do trajeto."""
        ex, ey, ez = self._end_point()
        p = max(0.0, min(1.0, progress))

        return (
            self.start_x + (ex - self.start_x) * p,
            self.start_y + (ey - self.start_y) * p,
            self.START_Z + (ez - self.START_Z) * p,
        )

    @property
    def x(self):
        return self.position_at(self.progress)[0]

    @property
    def y(self):
        return self.position_at(self.progress)[1]

    def update(self, dt):
        """Retorna True quando a bala chega ao destino."""

        self.timer -= dt

        return self.timer <= 0
