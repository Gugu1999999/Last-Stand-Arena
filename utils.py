import math


def norm_angle(angle):
    """Normaliza um ângulo para [-pi, pi]."""
    angle = (angle + math.pi) % (2 * math.pi) - math.pi
    return angle


def clamp(value, low, high):
    return max(low, min(high, value))


def lerp(a, b, t):
    return a + (b - a) * t


def ray_circle_distance(px, py, dx, dy, radius):
    """
    Distância da posição (px, py) até a borda da arena (círculo de raio
    `radius` centrado na origem) seguindo a direção unitária (dx, dy).
    Assume que o ponto de origem está dentro do círculo.
    """
    b = 2 * (px * dx + py * dy)
    c = px * px + py * py - radius * radius

    disc = b * b - 4 * c

    if disc < 0:
        return radius

    t = (-b + math.sqrt(disc)) / 2

    return max(t, 0.0001)
