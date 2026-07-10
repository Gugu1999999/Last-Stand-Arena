import pygame
import math

pygame.init()

LARGURA = 2000
ALTURA = 1000
TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("RayCasting - Etapa 1")

clock = pygame.time.Clock()

TAMANHO = 64

MAPA = [
"1111111111111111111111111111111",
"1000000000000000000000000000001",
"1000111000000000000000000000001",
"1000000000000000000000000000001",
"1000000000001110000000000000001",
"1000000000000000000000000000001",
"1000000000000000000000000000001",
"1000000000000001110000000000001",
"1000000000000000000000000000001",
"1000000000000000000000000000001",
"1000000000000000000000000000001",
"1000000000000000000000000000001",
"1000000111111111111111100000001",
"1000000000000000000000000000001",
"1000000000000000000000000000001",
"1111111111111111111111111111111"
]

player_x = 150
player_y = 150
angulo = 0

velocidade = 3
rotacao = 0.05

def parede(x, y):
    coluna = int(x // TAMANHO)
    linha = int(y // TAMANHO)

    if linha < 0 or linha >= len(MAPA):
        return True

    if coluna < 0 or coluna >= len(MAPA[0]):
        return True

    return MAPA[linha][coluna] == "1"


rodando = True

while rodando:

    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            rodando = False

    teclas = pygame.key.get_pressed()

    if teclas[pygame.K_a]:
        angulo -= rotacao

    if teclas[pygame.K_d]:
        angulo += rotacao

    novo_x = player_x
    novo_y = player_y

    if teclas[pygame.K_w]:
        novo_x += math.cos(angulo) * velocidade
        novo_y += math.sin(angulo) * velocidade

    if teclas[pygame.K_s]:
        novo_x -= math.cos(angulo) * velocidade
        novo_y -= math.sin(angulo) * velocidade

    if not parede(novo_x, novo_y):
        player_x = novo_x
        player_y = novo_y

    TELA.fill((25,25,25))

    # mapa
    for linha in range(len(MAPA)):
        for coluna in range(len(MAPA[0])):

            cor = (180,180,180) if MAPA[linha][coluna] == "1" else (60,60,60)

            pygame.draw.rect(
                TELA,
                cor,
                (
                    coluna*TAMANHO,
                    linha*TAMANHO,
                    TAMANHO,
                    TAMANHO
                )
            )

    # jogador
    pygame.draw.circle(
        TELA,
        (255,0,0),
        (int(player_x), int(player_y)),
        8
    )

    # direção
    fim_x = player_x + math.cos(angulo) *40
    fim_y = player_y + math.sin(angulo) * 40

    pygame.draw.line(
        TELA,
        (255,255,0),
        (player_x, player_y),
        (fim_x, fim_y),
        3
    )

    pygame.display.flip()

pygame.quit()