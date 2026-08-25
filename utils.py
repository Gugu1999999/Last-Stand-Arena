import math


def norm_angle(angle):
    """Normaliza um ângulo para [-pi, pi]."""
    while angle > math.pi:
        angle -= 2 * math.pi

    while angle < -math.pi:
        angle += 2 * math.pi

    return angle


def ray_circle_distance(px, py, dx, dy, radius):
    """
    Calcula a distância até a borda da arena
    seguindo a direção do raio.
    """

    b = 2 * (px * dx + py * dy)
    c = px * px + py * py - radius * radius

    disc = b * b - 4 * c

    if disc < 0:
        return radius

    sqrt_disc = math.sqrt(disc)

    t = (-b + sqrt_disc) / 2

    return max(t, 0.0001)