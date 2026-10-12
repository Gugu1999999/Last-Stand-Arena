"""
teste_automatico.py
===================
Roda o jogo SEM janela (modo "dummy" do SDL) e confere as regras principais.
Serve para o time rodar antes de cada merge:

    python tests/teste_automatico.py            # testes rápidos (~20 s)
    python tests/teste_automatico.py --longo    # + 10 min de jogo simulado por um "robô"
    python tests/teste_automatico.py --capturas # salva imagens em tests/capturas/

Se algo falhar, o script mostra qual regra quebrou e sai com código 1.
"""
import math
import os
import random
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

import pygame                                   # noqa: E402

from config import (                            # noqa: E402
    ARENA_RADIUS, PLAYER_RADIUS, PLAYER_MAX_HP, BASE_FOV, MAX_FOV, PICKUP_RADIUS,
)
from enemy import Enemy                         # noqa: E402
from game import Game                           # noqa: E402
from powerups import PowerUpDrop, POWERUP_TYPES  # noqa: E402

DT = 1 / 60
CAPTURAS = "--capturas" in sys.argv
falhas = []


class Teclas:
    """Teclado falso (no modo dummy não existe teclado de verdade)."""

    def __init__(self):
        self.down = set()

    def __getitem__(self, k):
        return k in self.down


teclas = Teclas()
pygame.key.get_pressed = lambda: teclas


def confere(condicao, mensagem):
    print(("  OK     " if condicao else "  FALHOU ") + mensagem)
    if not condicao:
        falhas.append(mensagem)


def avancar(g, segundos):
    for _ in range(int(round(segundos / DT))):
        g.update(DT)


def capturar(g, nome):
    if not CAPTURAS:
        return
    os.makedirs(os.path.join(RAIZ, "tests", "capturas"), exist_ok=True)
    g.renderer.render(g)
    g.ui.draw(g)
    pygame.image.save(g.screen, os.path.join(RAIZ, "tests", "capturas", nome + ".png"))


def novo_jogo():
    g = Game()
    avancar(g, 2.4)                      # sai do "PREPARE-SE" e começa a rodada 1
    g.spawn_queue.clear()
    g.enemies.clear()
    g.pickups.clear()
    g.player.x = g.player.y = 0.0
    g.player.angle = 0.0
    return g


# ----------------------------------------------------------------------
def teste_coleta_de_itens():
    print("\n[1] Power-ups dropados podem ser coletados")
    import game as modulo_game

    g = novo_jogo()
    p = g.player
    original = modulo_game.random.random
    modulo_game.random.random = lambda: 0.0            # força o drop
    e = Enemy("batedor", 500, 0, 0, 1)
    g.enemies.append(e)
    g.try_shoot()
    avancar(g, 0.5)
    modulo_game.random.random = original

    confere(not e.alive, "inimigo morre com 1 tiro (batedor tem 1 de vida)")
    confere(len(g.pickups) == 1, "o inimigo soltou um item")
    if g.pickups:
        d = g.pickups[0]
        p.angle = math.atan2(d.y, d.x)
        teclas.down = {pygame.K_w}
        for _ in range(300):
            g.update(DT)
            if not g.pickups:
                break
        teclas.down.clear()
        confere(not g.pickups, f"o item é coletado ao se aproximar (raio {PICKUP_RADIUS:.0f})")

    g.pickups.clear()
    g.shockwave = None
    p.active_powerups.clear()
    p.x = p.y = 0.0
    g.pickups.append(PowerUpDrop("rapid_fire", 200, 0))
    avancar(g, 1.0)
    confere(p.has_powerup("rapid_fire"), "o 'ímã' puxa o item que está perto")


def teste_explosao_e_ondas():
    print("\n[2] Explosão não é atropelada pela próxima rodada")
    g = novo_jogo()
    p = g.player
    for x, y in [(400, -150), (500, 60), (600, -40), (350, 200), (-300, 0)]:
        g.enemies.append(Enemy("hoplita", x, y, 40, 1))
    g.spawn_queue.clear()
    rodada_antes = g.round_num
    g.apply_powerup("explosion")

    confere(g.shockwave is not None, "a explosão cria uma onda de choque")
    vivos0 = sum(e.alive for e in g.enemies)
    avancar(g, 0.1)
    confere(vivos0 == 5, "os inimigos NÃO morrem todos no mesmo frame")
    t_ini = g.time
    avancar(g, 1.5)
    confere(not any(e.alive for e in g.enemies), "a onda elimina todos os inimigos")
    confere(g.round_num == rodada_antes, "a próxima rodada NÃO começou durante a explosão")
    confere(g.wave_state == "intermission", "há uma pausa entre rodadas")
    avancar(g, 4.0)
    confere(g.round_num == rodada_antes + 1, "depois da pausa a nova rodada começa")
    capturar(g, "explosao_depois")


def teste_power_ups():
    print("\n[3] Efeitos dos power-ups")
    g = novo_jogo()
    p = g.player

    g.apply_powerup("vision")
    avancar(g, 1.2)
    confere(abs(p.fov - MAX_FOV) < math.radians(2), "visão ampliada abre o FOV (suavemente)")
    p.active_powerups.clear()
    avancar(g, 1.5)
    confere(abs(p.fov - BASE_FOV) < math.radians(2), "o FOV volta ao normal quando acaba")

    g.enemies.append(Enemy("hoplita", 500, 0, 100, 1))
    g.apply_powerup("freeze")
    x0 = g.enemies[0].x
    avancar(g, 1.0)
    confere(abs(g.enemies[0].x - x0) < 0.01, "paralisação segura os inimigos")
    p.active_powerups.clear()
    avancar(g, 0.5)
    confere(abs(g.enemies[0].x - x0) > 5, "e eles voltam a andar depois")


def teste_combate_e_game_over():
    print("\n[4] Combate, vida e game over")
    g = novo_jogo()
    p = g.player

    g.enemies.append(Enemy("campeao", 600, 0, 0, 1))
    hp0 = g.enemies[0].hp
    g.try_shoot()
    avancar(g, 0.6)
    confere(g.enemies[0].hp == hp0 - 1 and g.enemies[0].alive, "o campeão aguenta vários tiros (tem vida)")

    g.enemies.clear()
    g.enemies.append(Enemy("hoplita", 3000, 3000, 0, 1))        # fora de alcance: não deve acertar
    g.player.angle = 0
    g.enemies.clear()
    g.enemies.append(Enemy("hoplita", 500, 400, 0, 1))
    g.try_shoot()
    avancar(g, 0.5)
    confere(g.enemies[0].alive, "tiro fora da mira não acerta ninguém")

    g.enemies.clear()
    g.enemies.append(Enemy("campeao", 150, 0, 0, 1))
    avancar(g, 60)
    confere(g.state == "game_over", "vida zerada leva ao game over")
    avancar(g, 1.5)
    g.reset()
    confere(g.state == "playing" and g.player.hp == PLAYER_MAX_HP, "reiniciar restaura a partida")


def teste_arena_e_pausa():
    print("\n[5] Arena, pausa e mouse")
    g = novo_jogo()
    p = g.player
    teclas.down = {pygame.K_w}
    avancar(g, 8.0)
    teclas.down.clear()
    r = math.hypot(p.x, p.y)
    confere(r <= ARENA_RADIUS - PLAYER_RADIUS + 0.01, f"o jogador não atravessa a parede (parou a {r:.0f})")

    g.toggle_pause()
    t = g.time
    avancar(g, 1.0)
    confere(g.state == "paused" and g.time == t, "pausa congela o jogo")
    confere(not g.mouse_locked, "pausa libera o mouse")
    g.toggle_pause()
    confere(g.state == "playing" and g.mouse_locked, "retomar prende o mouse de novo")


def teste_longo(minutos=10):
    print(f"\n[6] Estresse: robô jogando {minutos} min simulados")
    random.seed(7)
    g = Game()
    frames = int(minutos * 60 * 60)
    maior = mortes = 0
    t0 = time.time()
    for f in range(frames):
        p = g.player
        if g.state == "playing":
            teclas.down.clear()
            if f % 90 < 60:
                teclas.down.add(pygame.K_w)
            if (f // 45) % 3 == 0:
                teclas.down.add(pygame.K_a)
            vivos = [e for e in g.enemies if e.alive]
            if vivos:
                e = min(vivos, key=lambda e: (e.x - p.x) ** 2 + (e.y - p.y) ** 2)
                diff = (math.atan2(e.y - p.y, e.x - p.x) - p.angle + math.pi) % (2 * math.pi) - math.pi
                p.angle = (p.angle + max(-0.06, min(0.06, diff))) % (2 * math.pi)
                if f % 7 == 0:
                    g.try_shoot()
            if random.random() < 0.001 and len(g.pickups) < 5:
                g.pickups.append(PowerUpDrop(random.choice(POWERUP_TYPES), p.x + random.uniform(-300, 300),
                                             p.y + random.uniform(-300, 300)))
        elif g.state == "game_over" and g.game_over_time > 1.0:
            mortes += 1
            g.reset()
        g.update(DT)
        if f % 30 == 0:
            g.renderer.render(g)
            g.ui.draw(g)
        maior = max(maior, g.round_num)
        if any(v != v for v in (p.x, p.y, p.angle, p.fov)):
            confere(False, "valores inválidos (NaN) no jogador")
            return
    confere(len(g.particles.items) <= 500 and len(g.pickups) <= 5, "listas de efeitos continuam limitadas")
    print(f"      (rodada máxima {maior}, {mortes} reinícios, {time.time() - t0:.0f}s de relógio)")


# ----------------------------------------------------------------------
if __name__ == "__main__":
    random.seed(1)
    for teste in (teste_coleta_de_itens, teste_explosao_e_ondas, teste_power_ups,
                  teste_combate_e_game_over, teste_arena_e_pausa):
        teste()
    if "--longo" in sys.argv:
        teste_longo()
    print()
    if falhas:
        print(f"{len(falhas)} verificação(ões) FALHARAM:")
        for m in falhas:
            print("  -", m)
        sys.exit(1)
    print("Tudo certo!")
