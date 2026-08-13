"""
Last Stand Arena
=================
Protótipo jogável em Python + pygame.

- Visão em primeira pessoa construída com RAY CASTING (estilo Doom).
- Arena circular (coliseu). O jogador fica preso dentro do círculo.
- Zumbis surgem dos 4 lados (Norte, Sul, Leste, Oeste) e avançam sobre o jogador.
- Ondas infinitas: a cada rodada os zumbis ficam mais rápidos e numerosos.
- Power-ups aleatórios ao eliminar zumbis: visão ampliada, tiro contínuo,
  paralisação dos inimigos e explosão que limpa a arena.

Controles:
  W / S       - andar para frente / para trás
  A / D       - deslocar lateralmente (strafe)
  Mouse       - olhar ao redor (câmera em primeira pessoa)
  Clique esq. - atirar
  ESC         - liberar/prender o mouse
  R           - reiniciar após Game Over
"""

import pygame
import math
import random
import sys

# ----------------------------------------------------------------------
# CONFIGURAÇÕES GERAIS
# ----------------------------------------------------------------------
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
FPS = 60

ARENA_RADIUS = 900.0          # raio da arena (mundo)
PLAYER_RADIUS = 20.0          # "colisão" do jogador com a parede
BASE_FOV = math.radians(70)   # campo de visão em cone (padrão)
MAX_FOV = math.radians(110)   # limite ao usar o power-up de visão
RENDER_COLS = 300             # nº de raios (colunas) - trocar p/ SCREEN_WIDTH deixa mais nítido e mais pesado
MAX_DEPTH = ARENA_RADIUS * 2

PLAYER_SPEED = 220.0          # px/seg
PLAYER_TURN_SPEED = 2.4       # rad/seg (teclado, fallback sem mouse)
MOUSE_SENSITIVITY = 0.0025

PLAYER_MAX_HP = 100
ZOMBIE_DAMAGE = 12
ZOMBIE_ATTACK_RANGE = 42
ZOMBIE_ATTACK_COOLDOWN = 0.8

SHOOT_RANGE = ARENA_RADIUS * 2
SHOOT_COOLDOWN = 0.32          # cadência da pistola
SHOOT_ANGLE_TOLERANCE = math.radians(4)  # "mira" - tolerância angular do tiro

POWERUP_DROP_CHANCE = 0.18
POWERUP_DURATION = {
    "vision": 8.0,
    "rapid_fire": 7.0,
    "freeze": 4.0,
}

WHITE = (240, 240, 240)
BLACK = (10, 10, 10)
RED = (200, 40, 40)
DARK_RED = (110, 15, 15)
GREEN = (60, 200, 90)
DARK_GREEN = (25, 110, 50)
YELLOW = (230, 200, 40)
BLUE = (60, 140, 230)
ORANGE = (230, 140, 30)
GREY = (70, 70, 75)
SAND = (150, 120, 80)


# ----------------------------------------------------------------------
# FUNÇÕES AUXILIARES
# ----------------------------------------------------------------------
def norm_angle(a):
    """Normaliza um ângulo para o intervalo [-pi, pi]."""
    while a > math.pi:
        a -= 2 * math.pi
    while a < -math.pi:
        a += 2 * math.pi
    return a


def ray_circle_distance(px, py, dx, dy, radius):
    """
    Retorna a distância entre (px,py) e a borda de um círculo de raio
    `radius` centrado na origem, seguindo a direção (dx,dy) (vetor unitário).
    Assume que o ponto de origem está SEMPRE dentro do círculo, então
    existe exatamente uma raiz positiva relevante.
    """
    # (px + t*dx)^2 + (py + t*dy)^2 = radius^2
    b = 2 * (px * dx + py * dy)
    c = px * px + py * py - radius * radius
    disc = b * b - 4 * c
    if disc < 0:
        return radius  # segurança (não deveria ocorrer)
    sqrt_disc = math.sqrt(disc)
    t = (-b + sqrt_disc) / 2
    return max(t, 0.0001)


# ----------------------------------------------------------------------
# JOGADOR
# ----------------------------------------------------------------------
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

        # power-ups ativos: nome -> tempo restante
        self.active_powerups = {}

    def has_powerup(self, name):
        return self.active_powerups.get(name, 0) > 0

    def add_powerup(self, name):
        self.active_powerups[name] = POWERUP_DURATION.get(name, 0)

    def update_powerups(self, dt):
        expired = []
        for name in list(self.active_powerups.keys()):
            self.active_powerups[name] -= dt
            if self.active_powerups[name] <= 0:
                expired.append(name)
                del self.active_powerups[name]
        # FOV volta ao normal quando "vision" expira
        if "vision" in expired or not self.has_powerup("vision"):
            self.fov = MAX_FOV if self.has_powerup("vision") else BASE_FOV

    def handle_movement(self, dt, keys):
        move_x = 0.0
        move_y = 0.0
        forward = (math.cos(self.angle), math.sin(self.angle))
        right = (math.cos(self.angle + math.pi / 2), math.sin(self.angle + math.pi / 2))

        if keys[pygame.K_w]:
            move_x += forward[0]
            move_y += forward[1]
        if keys[pygame.K_s]:
            move_x -= forward[0]
            move_y -= forward[1]
        if keys[pygame.K_d]:
            move_x += right[0]
            move_y += right[1]
        if keys[pygame.K_a]:
            move_x -= right[0]
            move_y -= right[1]

        # teclado alternativo p/ girar câmera, caso o mouse esteja livre
        if keys[pygame.K_LEFT]:
            self.angle -= PLAYER_TURN_SPEED * dt
        if keys[pygame.K_RIGHT]:
            self.angle += PLAYER_TURN_SPEED * dt

        length = math.hypot(move_x, move_y)
        if length > 0:
            move_x, move_y = move_x / length, move_y / length
            new_x = self.x + move_x * PLAYER_SPEED * dt
            new_y = self.y + move_y * PLAYER_SPEED * dt

            # colisão com a parede da arena (mantém o jogador dentro do círculo)
            dist_center = math.hypot(new_x, new_y)
            max_dist = ARENA_RADIUS - PLAYER_RADIUS
            if dist_center > max_dist:
                scale = max_dist / dist_center
                new_x *= scale
                new_y *= scale

            self.x, self.y = new_x, new_y

    def rotate_mouse(self, dx):
        self.angle += dx * MOUSE_SENSITIVITY


# ----------------------------------------------------------------------
# ZUMBI
# ----------------------------------------------------------------------
class Zombie:
    __slots__ = ("x", "y", "speed", "hp", "alive", "attack_timer", "hit_flash")

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
        self.hit_flash = max(0.0, self.hit_flash - dt)
        if frozen:
            return

        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)

        if dist > ZOMBIE_ATTACK_RANGE:
            if dist > 0:
                dx, dy = dx / dist, dy / dist
            self.x += dx * self.speed * dt
            self.y += dy * self.speed * dt
        else:
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                player.hp -= ZOMBIE_DAMAGE
                self.attack_timer = ZOMBIE_ATTACK_COOLDOWN


# ----------------------------------------------------------------------
# POWER-UP (efeito de "explosão" instantânea é tratado à parte)
# ----------------------------------------------------------------------
POWERUP_TYPES = ["vision", "rapid_fire", "freeze", "explosion"]
POWERUP_LABELS = {
    "vision": "VISÃO AMPLIADA",
    "rapid_fire": "TIRO CONTÍNUO",
    "freeze": "PARALISAÇÃO",
    "explosion": "EXPLOSÃO",
}


# ----------------------------------------------------------------------
# JOGO
# ----------------------------------------------------------------------
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Last Stand Arena")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 20)
        self.big_font = pygame.font.SysFont("arial", 48, bold=True)

        self.mouse_locked = True
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

        self.notification = ""
        self.notification_timer = 0.0

        self.reset()

    # ---------------- controle de partida ----------------
    def reset(self):
        self.player = Player()
        self.zombies = []
        self.round_num = 0
        self.state = "playing"  # playing | game_over
        self.round_delay_timer = 1.0
        self.spawning_new_round = True
        self.start_next_round()

    def start_next_round(self):
        self.round_num += 1
        self.player.round_num = self.round_num
        count = 4 + self.round_num * 2
        speed = 55 + self.round_num * 6
        speed = min(speed, 230)
        self.spawn_wave(count, speed)
        self.notify(f"RODADA {self.round_num}")

    def spawn_wave(self, count, speed):
        # 4 clusters de spawn: Norte, Sul, Leste, Oeste
        base_dirs = [0, math.pi / 2, math.pi, -math.pi / 2]
        for i in range(count):
            base = random.choice(base_dirs)
            angle = base + random.uniform(-0.35, 0.35)
            r = ARENA_RADIUS - 5
            x = math.cos(angle) * r
            y = math.sin(angle) * r
            hp = 1 + self.round_num // 5  # zumbis ficam mais resistentes com o tempo
            self.zombies.append(Zombie(x, y, speed * random.uniform(0.9, 1.1), hp))

    def notify(self, text, duration=2.2):
        self.notification = text
        self.notification_timer = duration

    # ---------------- update ----------------
    def update(self, dt):
        if self.state == "game_over":
            return

        self.player.update_powerups(dt)
        self.player.shoot_timer = max(0.0, self.player.shoot_timer - dt)
        if self.notification_timer > 0:
            self.notification_timer -= dt

        keys = pygame.key.get_pressed()
        self.player.handle_movement(dt, keys)

        frozen = self.player.has_powerup("freeze")
        alive_count = 0
        for z in self.zombies:
            z.update(dt, self.player, frozen)
            if z.alive:
                alive_count += 1

        if self.player.hp <= 0:
            self.player.hp = 0
            self.state = "game_over"
            return

        # remove zumbis mortos da lista periodicamente
        if alive_count == 0:
            self.zombies = []
            self.start_next_round()

    def try_shoot(self):
        if self.player.shoot_timer > 0 and not self.player.has_powerup("rapid_fire"):
            return
        self.player.shoot_timer = SHOOT_COOLDOWN if not self.player.has_powerup("rapid_fire") else 0.06

        best_z = None
        best_dist = SHOOT_RANGE
        for z in self.zombies:
            if not z.alive:
                continue
            dx = z.x - self.player.x
            dy = z.y - self.player.y
            dist = math.hypot(dx, dy)
            ang = norm_angle(math.atan2(dy, dx) - self.player.angle)
            if abs(ang) <= SHOOT_ANGLE_TOLERANCE and dist < best_dist:
                best_dist = dist
                best_z = z

        if best_z:
            best_z.hp -= 1
            best_z.hit_flash = 0.15
            if best_z.hp <= 0:
                self.kill_zombie(best_z)

    def kill_zombie(self, zombie):
        zombie.alive = False
        self.player.kills += 1
        if random.random() < POWERUP_DROP_CHANCE:
            self.apply_powerup(random.choice(POWERUP_TYPES))

    def apply_powerup(self, name):
        if name == "explosion":
            count = 0
            for z in self.zombies:
                if z.alive:
                    z.alive = False
                    count += 1
            self.player.kills += count
            self.notify("EXPLOSÃO! Arena limpa")
        else:
            self.player.add_powerup(name)
            if name == "vision":
                self.player.fov = MAX_FOV
            self.notify(f"Power-up: {POWERUP_LABELS[name]}")

    # ---------------- render (raycasting) ----------------
    def cast_and_draw(self):
        screen = self.screen
        half_h = SCREEN_HEIGHT // 2

        # céu / arquibancada (metade de cima) e chão de areia (metade de baixo)
        screen.fill(GREY, (0, 0, SCREEN_WIDTH, half_h))
        screen.fill(SAND, (0, half_h, SCREEN_WIDTH, half_h))

        fov = self.player.fov
        col_width = SCREEN_WIDTH / RENDER_COLS
        z_buffer = [MAX_DEPTH] * RENDER_COLS

        # 1) paredes da arena via ray casting
        for col in range(RENDER_COLS):
            cam_t = (col / RENDER_COLS) - 0.5  # -0.5 .. 0.5
            ray_angle = self.player.angle + cam_t * fov
            dx, dy = math.cos(ray_angle), math.sin(ray_angle)

            dist = ray_circle_distance(self.player.x, self.player.y, dx, dy, ARENA_RADIUS)
            # corrige efeito "olho de peixe"
            corrected = dist * math.cos(ray_angle - self.player.angle)
            corrected = max(corrected, 0.0001)
            z_buffer[col] = corrected

            wall_h = min(SCREEN_HEIGHT, (SCREEN_HEIGHT * 260) / corrected)
            shade = max(0.15, 1.0 - corrected / ARENA_RADIUS)
            color = (
                int(GREY[0] * shade + 40 * (1 - shade)),
                int(GREY[1] * shade + 20 * (1 - shade)),
                int(GREY[2] * shade + 20 * (1 - shade)),
            )
            x = int(col * col_width)
            pygame.draw.rect(
                screen, color,
                (x, int(half_h - wall_h / 2), math.ceil(col_width) + 1, int(wall_h))
            )

        # 2) zumbis como sprites (billboards), do mais longe para o mais perto
        visible = []
        for z in self.zombies:
            if not z.alive:
                continue
            ddx = z.x - self.player.x
            ddy = z.y - self.player.y
            dist = math.hypot(ddx, ddy)
            ang = norm_angle(math.atan2(ddy, ddx) - self.player.angle)
            if abs(ang) < fov / 2 + 0.15 and dist > 1:
                visible.append((dist, ang, z))

        visible.sort(key=lambda t: -t[0])

        for dist, ang, z in visible:
            screen_x = SCREEN_WIDTH / 2 + math.tan(ang) * (SCREEN_WIDTH / 2) / math.tan(fov / 2)
            col_check = int((screen_x / SCREEN_WIDTH) * RENDER_COLS)
            col_check = max(0, min(RENDER_COLS - 1, col_check))
            if dist > z_buffer[col_check] + 6:
                continue  # atrás da parede, não deveria ocorrer na arena, mas por segurança

            size = min(SCREEN_HEIGHT * 1.1, (SCREEN_HEIGHT * 130) / dist)
            top = half_h - size / 2
            color = WHITE if z.hit_flash > 0 else DARK_GREEN
            body_color = WHITE if z.hit_flash > 0 else GREEN

            # corpo
            pygame.draw.rect(screen, color, (screen_x - size * 0.16, top + size * 0.32, size * 0.32, size * 0.5))
            # cabeça
            pygame.draw.circle(screen, body_color, (int(screen_x), int(top + size * 0.22)), max(2, int(size * 0.16)))
            # braços
            pygame.draw.line(screen, color, (screen_x - size * 0.16, top + size * 0.4),
                              (screen_x - size * 0.32, top + size * 0.65), max(1, int(size * 0.04)))
            pygame.draw.line(screen, color, (screen_x + size * 0.16, top + size * 0.4),
                              (screen_x + size * 0.32, top + size * 0.65), max(1, int(size * 0.04)))

        # 3) arma na mão (simples)
        gun_w, gun_h = 140, 170
        gx = SCREEN_WIDTH / 2 - gun_w / 2
        gy = SCREEN_HEIGHT - gun_h + 40
        pygame.draw.rect(screen, (40, 40, 40), (gx + 30, gy, 40, 120), border_radius=6)
        pygame.draw.rect(screen, (25, 25, 25), (gx + 15, gy + 90, 70, 30), border_radius=4)

        # 4) mira
        pygame.draw.line(screen, WHITE, (SCREEN_WIDTH / 2 - 10, SCREEN_HEIGHT / 2),
                          (SCREEN_WIDTH / 2 + 10, SCREEN_HEIGHT / 2), 2)
        pygame.draw.line(screen, WHITE, (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 10),
                          (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 10), 2)

    # ---------------- HUD ----------------
    def draw_hud(self):
        screen = self.screen

        # barra de vida
        hp_ratio = max(0, self.player.hp) / PLAYER_MAX_HP
        pygame.draw.rect(screen, (60, 20, 20), (20, SCREEN_HEIGHT - 40, 220, 22))
        pygame.draw.rect(screen, RED, (20, SCREEN_HEIGHT - 40, int(220 * hp_ratio), 22))
        pygame.draw.rect(screen, WHITE, (20, SCREEN_HEIGHT - 40, 220, 22), 2)
        hp_text = self.font.render(f"HP {int(self.player.hp)}/{PLAYER_MAX_HP}", True, WHITE)
        screen.blit(hp_text, (26, SCREEN_HEIGHT - 38))

        round_text = self.font.render(f"Rodada: {self.round_num}", True, YELLOW)
        screen.blit(round_text, (20, 16))
        kills_text = self.font.render(f"Abates: {self.player.kills}", True, WHITE)
        screen.blit(kills_text, (20, 42))

        alive = sum(1 for z in self.zombies if z.alive)
        alive_text = self.font.render(f"Zumbis na arena: {alive}", True, WHITE)
        screen.blit(alive_text, (20, 68))

        # power-ups ativos
        py = 100
        for name, remaining in self.player.active_powerups.items():
            txt = self.font.render(f"{POWERUP_LABELS[name]}: {remaining:0.1f}s", True, ORANGE)
            screen.blit(txt, (20, py))
            py += 24

        if self.notification_timer > 0:
            alpha_text = self.big_font.render(self.notification, True, YELLOW)
            rect = alpha_text.get_rect(center=(SCREEN_WIDTH / 2, 70))
            screen.blit(alpha_text, rect)

        if self.state == "game_over":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(190)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))
            go_text = self.big_font.render("FIM DE JOGO", True, RED)
            screen.blit(go_text, go_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 60)))
            stat_text = self.font.render(
                f"Você sobreviveu até a rodada {self.round_num} com {self.player.kills} abates.",
                True, WHITE
            )
            screen.blit(stat_text, stat_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)))
            restart_text = self.font.render("Pressione R para reiniciar", True, YELLOW)
            screen.blit(restart_text, restart_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 40)))

    # ---------------- loop principal ----------------
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.mouse_locked = not self.mouse_locked
                        pygame.event.set_grab(self.mouse_locked)
                        pygame.mouse.set_visible(not self.mouse_locked)
                    elif event.key == pygame.K_r and self.state == "game_over":
                        self.reset()
                elif event.type == pygame.MOUSEMOTION and self.mouse_locked:
                    self.player.rotate_mouse(event.rel[0])
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == "playing":
                        self.try_shoot()

            self.update(dt)
            self.cast_and_draw()
            self.draw_hud()
            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
