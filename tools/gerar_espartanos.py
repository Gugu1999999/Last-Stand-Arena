"""
gerar_espartanos.py
===================
Gera os sprite sheets dos 3 tipos de espartanos (pixel-art feito por código).

Uso (na raiz do projeto):
    python tools/gerar_espartanos.py

Saída: assets/images/enemies/<tipo>.png  (6 quadros lado a lado, mesma ordem):
    0..3 = caminhada | 4 = preparando o golpe | 5 = golpe

IMPORTANTE PARA O TIME DE ARTES: o jogo só lê os PNGs. Pode redesenhar à mão
qualquer sheet, desde que mantenha 6 quadros do mesmo tamanho na mesma ordem
(o tamanho de cada quadro é a largura total / 6). Rode este script de novo
só se quiser voltar aos sprites originais.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from pixelkit import (Canvas, m_rect, m_ellipse, m_poly, m_line, m_mirror)

FRAMES = 6
WALK_POSES = [
    dict(bob=0, lift_l=0, lift_r=0, sway=0),
    dict(bob=1, lift_l=3, lift_r=0, sway=1),
    dict(bob=0, lift_l=0, lift_r=0, sway=0),
    dict(bob=1, lift_l=0, lift_r=3, sway=-1),
]
ATTACK_POSES = [
    dict(bob=0, lift_l=0, lift_r=0, sway=0, attack=1),   # preparando
    dict(bob=-1, lift_l=0, lift_r=0, sway=0, attack=2),  # golpe
]



def lanca_diagonal(c, x0, y0, x1, y1, mat_cabo, mat_ponta, comp_ponta, larg_ponta, cabo_grosso=2):
    """cabo de (x0,y0) até a base da ponta; a ponta aponta na mesma direção"""
    import math
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy)
    ux, uy = dx / n, dy / n
    px, py = -uy, ux                       # perpendicular
    c.paint(m_line(x0, y0, x1, y1, cabo_grosso), mat_cabo)
    bx, by = x1, y1
    tx, ty = x1 + ux * comp_ponta, y1 + uy * comp_ponta
    h = larg_ponta / 2
    c.paint(m_poly([(bx + px * h, by + py * h), (bx + ux * comp_ponta * 0.35 + px * h * 0.9, by + uy * comp_ponta * 0.35 + py * h * 0.9),
                    (tx, ty), (bx + ux * comp_ponta * 0.35 - px * h * 0.9, by + uy * comp_ponta * 0.35 - py * h * 0.9),
                    (bx - px * h, by - py * h)]), mat_ponta)
    mx, my = bx + ux * comp_ponta * 0.5, by + uy * comp_ponta * 0.5
    c.dots([(int(mx), int(my))], (255, 255, 255))

# =====================================================================
#  HOPLITA  (soldado básico: elmo com crista vermelha, escudo, lança)
# =====================================================================
def hoplita(pose):
    W, H = 44, 64
    c = Canvas(W, H)
    bob = pose["bob"]
    att = pose.get("attack", 0)
    oy = -bob                       # corpo sobe 1px no passo
    sway = pose["sway"]
    lean = 1 if att == 1 else 0     # preparando: puxa o corpo para trás
    GROUND = 62

    # ---- lança (atrás do braço) ------------------------------------
    sx = 8
    if att == 0:
        c.paint(m_rect(sx, 5 + oy, sx + 2, GROUND), "wood")
        c.paint(m_poly([(sx - 1.5, 10 + oy), (sx + 1, 2 + oy), (sx + 3.5, 10 + oy), (sx + 1, 12 + oy)]), "steel")
    elif att == 1:                  # lança erguida, ponta mais alta
        c.paint(m_rect(sx, 3, sx + 2, GROUND - 4), "wood")
        c.paint(m_poly([(sx - 1.5, 8), (sx + 1, 1), (sx + 3.5, 8), (sx + 1, 10)]), "steel")
    # (att == 2: a lança é desenhada no final, por cima do corpo)

    # ---- capa (atrás do corpo) -------------------------------------
    top, bot = 21 + oy, 53 + oy
    cape = m_poly([(10, top), (34, top), (38 + sway, bot), (6 + sway, bot)])
    c.paint(cape, "cloth")
    c.dots([(8 + sway + i * 4, bot) for i in range(0, 8)], (60, 8, 12))   # barra irregular
    c.detail(m_line(14, top + 2, 12 + sway, bot - 2), "cloth")

    # ---- pernas ------------------------------------------------------
    for (lx0, lift) in ((15, pose["lift_l"]), (23, pose["lift_r"])):
        top_y = 46 + oy
        foot = GROUND - lift
        c.paint(m_rect(lx0, top_y, lx0 + 7, foot - 8), "skin")            # coxa
        c.paint(m_rect(lx0, foot - 9, lx0 + 7, foot - 2), "bronze")       # greva
        c.paint(m_rect(lx0 - 1, foot - 3, lx0 + 8, foot), "leather")      # sandália
        c.dots([(lx0 + 3, foot - 8), (lx0 + 4, foot - 8)], (255, 220, 120))  # brilho no joelho

    # ---- túnica / saia ----------------------------------------------
    c.paint(m_rect(13, 41 + oy, 31, 50 + oy), "cloth")
    for i in range(0, 5):
        c.dots([(15 + i * 4, 46 + oy), (15 + i * 4, 47 + oy), (15 + i * 4, 48 + oy)], (110, 18, 22))
    c.paint(m_rect(13, 40 + oy, 31, 43 + oy), "leather")                  # cinto
    c.dots([(21, 41 + oy), (22, 41 + oy)], (255, 220, 120))               # fivela

    # ---- tronco: peitoral de bronze ---------------------------------
    chest = m_poly([(12, 23 + oy), (32, 23 + oy), (31, 31 + oy), (30, 41 + oy), (14, 41 + oy), (13, 31 + oy)])
    c.paint(chest, "bronze")
    c.dots([(18, 28 + oy), (19, 29 + oy), (20, 29 + oy), (21, 28 + oy),
            (23, 28 + oy), (24, 29 + oy), (25, 29 + oy), (26, 28 + oy)], (122, 70, 22))   # peitorais
    c.dots([(22, y + oy) for y in range(31, 40)], (122, 70, 22))                          # linha central
    c.dots([(18, 34 + oy), (19, 34 + oy), (25, 34 + oy), (26, 34 + oy),
            (18, 37 + oy), (19, 37 + oy), (25, 37 + oy), (26, 37 + oy)], (122, 70, 22))   # abdômen

    # ---- braço direito (lado esquerdo da imagem) segurando a lança --
    if att == 2:
        c.paint(m_rect(8, 25 + oy, 13, 31 + oy), "bronze")                # ombreira
        c.paint(m_rect(8, 30 + oy, 12, 37 + oy), "skin")
        c.paint(m_rect(7, 34, 12, 39), "skin")                            # punho
    else:
        up = 3 if att == 1 else 0
        c.paint(m_rect(8, 25 + oy, 13, 31 + oy), "bronze")                # ombreira
        c.paint(m_rect(8, 30 + oy, 12, 36 + oy - up), "skin")
        c.paint(m_rect(7, 34 + oy - up, 12, 39 + oy - up), "skin")        # punho

    # ---- escudo (hoplon) no braço esquerdo --------------------------
    scx, scy = 32, 41 + oy
    c.paint(m_rect(31, 24 + oy, 36, 32 + oy), "skin")                      # braço atrás
    c.paint(m_ellipse(scx, scy, 11.5, 11.5), "bronze")                    # aro
    c.detail(m_ellipse(scx, scy, 9, 9), "cloth")                           # campo vermelho
    c.detail(m_line(scx, scy - 6, scx - 4, scy + 5, 2), "gold")           # lambda (Λ)
    c.detail(m_line(scx, scy - 6, scx + 4, scy + 5, 2), "gold")
    c.dots([(scx - 1, scy - 7), (scx, scy - 7)], (255, 230, 120))

    # ---- cabeça / elmo coríntio -------------------------------------
    hy = 12 + oy - lean
    c.paint(m_rect(19, 18 + oy, 25, 23 + oy), "skin")                      # pescoço
    # crista vermelha (transversal)
    c.paint(m_poly([(11, hy - 1), (15, hy - 7), (22, hy - 10), (29, hy - 7), (33, hy - 1),
                    (29, hy - 3), (22, hy - 6), (15, hy - 3)]), "cloth")
    c.paint(m_ellipse(22, hy + 1, 8.5, 8.5), "bronze")                     # calota
    c.paint(m_rect(15, hy + 1, 29, hy + 9), "bronze")                      # bochechas
    c.detail(m_rect(18, hy + 3, 26, hy + 8), "skin")                       # rosto aberto
    c.detail(m_rect(18, hy + 3, 26, hy + 5), "black")                      # fenda dos olhos
    c.detail(m_rect(21, hy + 3, 23, hy + 9), "bronze")                     # protetor de nariz
    c.dots([(19, hy + 4), (25, hy + 4)], (255, 244, 210))                  # olhos
    c.detail(m_rect(19, hy + 8, 25, hy + 10), "hair")                      # barba

    if att == 2:                    # golpe: lança aponta para o espectador
        lanca_diagonal(c, 6, 28, 21, 47, "wood", "steel", 12, 7)
    return c.render()


# =====================================================================
#  BATEDOR  (rápido e frágil: sem escudo, espada curta, corre inclinado)
# =====================================================================
def batedor(pose):
    W, H = 40, 60
    c = Canvas(W, H)
    bob = pose["bob"]
    att = pose.get("attack", 0)
    oy = -bob
    sway = pose["sway"]
    GROUND = 58
    hy = 11 + oy + 1                      # cabeça levemente inclinada p/ frente

    # capa curta (atrás)
    c.paint(m_poly([(11, 21 + oy), (29, 21 + oy), (34 + sway, 44 + oy), (6 + sway, 44 + oy)]), "cloth2")
    c.dots([(7 + sway + i * 4, 44 + oy) for i in range(0, 7)], (40, 8, 20))

    # pernas (passada larga)
    for (lx0, lift) in ((12, pose["lift_l"]), (22, pose["lift_r"])):
        foot = GROUND - lift * 1.3
        foot = int(foot)
        c.paint(m_rect(lx0, 40 + oy, lx0 + 6, foot - 3), "skin")
        c.paint(m_rect(lx0, foot - 12, lx0 + 6, foot - 3), "leather")       # faixas de couro na canela
        for yy in range(foot - 11, foot - 3, 3):
            c.dots([(lx0 + 1 + i, yy) for i in range(4)], (190, 130, 74))
        c.paint(m_rect(lx0 - 1, foot - 3, lx0 + 7, foot), "leather")        # sandália

    # tanga
    c.paint(m_poly([(13, 38 + oy), (27, 38 + oy), (28, 46 + oy), (12, 46 + oy)]), "cloth2")
    c.paint(m_rect(13, 36 + oy, 27, 39 + oy), "leather")                   # cinto

    # tronco nu e musculoso
    c.paint(m_poly([(11, 22 + oy), (29, 22 + oy), (27, 30 + oy), (26, 37 + oy), (14, 37 + oy), (13, 30 + oy)]), "skin")
    dk = (150, 84, 50)
    c.dots([(16, 27 + oy), (17, 28 + oy), (18, 28 + oy), (19, 27 + oy),
            (21, 27 + oy), (22, 28 + oy), (23, 28 + oy), (24, 27 + oy)], dk)
    c.dots([(20, y + oy) for y in range(29, 36)], dk)
    c.dots([(17, 32 + oy), (18, 32 + oy), (22, 32 + oy), (23, 32 + oy)], dk)
    c.paint(m_line(12, 23 + oy, 26, 37 + oy, 2), "leather", outline=False)  # talabarte
    c.dots([(19, 30 + oy), (20, 31 + oy)], (240, 200, 110))

    # braço esquerdo (lado direito da imagem) com pelta (escudo pequeno)
    c.paint(m_rect(28, 23 + oy, 32, 31 + oy), "skin")
    c.paint(m_ellipse(33, 34 + oy, 5.5, 6.5), "leather")
    c.detail(m_ellipse(33, 34 + oy, 3.2, 4), "bronze")
    c.dots([(33, 34 + oy), (33, 33 + oy)], (255, 232, 140))

    # cabeça com pilos (capacete cônico)
    c.paint(m_rect(18, hy + 7, 23, hy + 11), "skin")                       # pescoço
    c.paint(m_rect(15, hy - 1, 26, hy + 8), "skin")                        # rosto
    c.detail(m_rect(15, hy + 5, 26, hy + 8), "hair")                       # barba
    c.dots([(18, hy + 3), (23, hy + 3)], (255, 244, 210))                  # olhos
    c.dots([(18, hy + 2), (19, hy + 2), (22, hy + 2), (23, hy + 2)], (60, 30, 20))  # sobrancelhas
    c.paint(m_poly([(14, hy), (27, hy), (24, hy - 7), (21, hy - 10), (17, hy - 7)]), "bronze")
    c.paint(m_rect(13, hy - 1, 28, hy + 1), "bronze")                      # aba
    c.dots([(20, hy - 11), (21, hy - 11)], (200, 30, 30))                  # borla vermelha

    # braço direito (lado esquerdo da imagem) com xiphos (espada curta)
    if att == 1:                           # preparando: espada erguida atrás da cabeça
        c.paint(m_rect(8, 22 + oy, 12, 28 + oy), "skin")
        c.paint(m_rect(7, 14, 11, 24), "skin")
        c.paint(m_line(9, 15, 6, 1, 2), "steel")
        c.paint(m_rect(6, 14, 12, 16), "leather")
    elif att == 2:                         # golpe: corte diagonal na frente do corpo
        c.paint(m_rect(8, 24 + oy, 12, 30 + oy), "skin")
        c.paint(m_rect(8, 28, 13, 34), "skin")
        c.paint(m_line(6, 20, 30, 50, 3), "steel")
        c.paint(m_rect(8, 29, 14, 32), "leather")
        c.dots([(14, 28), (20, 36), (26, 44)], (255, 255, 255))
    else:
        c.paint(m_rect(8, 23 + oy, 12, 30 + oy), "skin")
        c.paint(m_rect(6, 29 + oy, 11, 34 + oy), "skin")
        c.paint(m_line(7, 30 + oy, 3, 15 + oy, 2), "steel")
        c.paint(m_rect(4, 29 + oy, 10, 31 + oy), "leather")
        c.dots([(3, 16 + oy), (4, 20 + oy)], (255, 255, 255))
    return c.render()


# =====================================================================
#  CAMPEÃO  (tanque: armadura negra com ouro, escudo enorme, lento)
# =====================================================================
def campeao(pose):
    W, H = 56, 80
    c = Canvas(W, H)
    bob = pose["bob"]
    att = pose.get("attack", 0)
    oy = -bob
    sway = pose["sway"]
    GROUND = 78
    hy = 16 + oy - (1 if att == 1 else 0)

    # lança (atrás)
    sx = 8
    if att == 1:
        c.paint(m_rect(sx, 3, sx + 3, GROUND - 5), "wood")
        c.paint(m_poly([(sx - 2, 10), (sx + 1.5, 1), (sx + 5, 10), (sx + 1.5, 13)]), "gold")
    elif att == 0:
        c.paint(m_rect(sx, 6 + oy, sx + 3, GROUND), "wood")
        c.paint(m_poly([(sx - 2, 13 + oy), (sx + 1.5, 3 + oy), (sx + 5, 13 + oy), (sx + 1.5, 16 + oy)]), "gold")

    # capa larga
    top, bot = 27 + oy, 68 + oy
    c.paint(m_poly([(9, top), (47, top), (53 + sway, bot), (3 + sway, bot)]), "cloth2")
    c.dots([(5 + sway + i * 4, bot) for i in range(0, 12)], (34, 6, 16))
    c.detail(m_line(16, top + 3, 12 + sway, bot - 3), "cloth2")
    c.detail(m_line(40, top + 3, 44 + sway, bot - 3), "cloth2")

    # pernas blindadas
    for (lx0, lift) in ((17, pose["lift_l"]), (30, pose["lift_r"])):
        foot = GROUND - lift
        c.paint(m_rect(lx0, 58 + oy, lx0 + 9, foot - 10), "plate")
        c.paint(m_rect(lx0, foot - 12, lx0 + 9, foot - 3), "plate")
        c.detail(m_rect(lx0 + 1, foot - 12, lx0 + 8, foot - 10), "gold")     # joelheira
        c.paint(m_rect(lx0 - 1, foot - 4, lx0 + 10, foot), "black")           # bota

    # saia de couro com faixa dourada
    c.paint(m_rect(16, 53 + oy, 40, 63 + oy), "leather")
    for i in range(0, 7):
        c.dots([(18 + i * 3, y + oy) for y in range(57, 63)], (60, 34, 20))
    c.paint(m_rect(16, 51 + oy, 40, 55 + oy), "gold")

    # peitoral negro com detalhes dourados
    c.paint(m_poly([(14, 29 + oy), (42, 29 + oy), (40, 40 + oy), (38, 52 + oy), (18, 52 + oy), (16, 40 + oy)]), "plate")
    c.dots([(x, 35 + oy) for x in range(19, 26)] + [(x, 35 + oy) for x in range(31, 38)], (224, 172, 40))
    c.dots([(28, y + oy) for y in range(36, 50)], (224, 172, 40))
    c.dots([(22, 40 + oy), (23, 41 + oy), (33, 40 + oy), (32, 41 + oy)], (224, 172, 40))

    # ombreiras enormes
    c.paint(m_ellipse(11, 31 + oy, 7, 6), "plate")
    c.detail(m_ellipse(11, 31 + oy, 4.5, 3.5), "gold")
    c.paint(m_ellipse(45, 31 + oy, 7, 6), "plate")
    c.detail(m_ellipse(45, 31 + oy, 4.5, 3.5), "gold")

    # braço da lança (esquerda da imagem)
    up = 4 if att == 1 else 0
    if att != 2:
        c.paint(m_rect(8, 35 + oy, 14, 46 + oy - up), "plate")
        c.paint(m_rect(7, 44 + oy - up, 14, 51 + oy - up), "skin")

    # escudo gigante
    scx, scy = 38, 52 + oy
    c.paint(m_ellipse(scx, scy, 16.5, 16.5), "plate")
    c.detail(m_ellipse(scx, scy, 14, 14), "gold")
    c.detail(m_ellipse(scx, scy, 12, 12), "black")
    c.detail(m_line(scx, scy - 8, scx - 6, scy + 8, 3), "gold")             # lambda
    c.detail(m_line(scx, scy - 8, scx + 6, scy + 8, 3), "gold")
    c.dots([(scx - 1, scy - 9), (scx, scy - 9), (scx + 1, scy - 9)], (255, 232, 140))

    # cabeça: elmo negro com crista dourada alta
    c.paint(m_rect(23, hy + 8, 33, hy + 14), "plate")                       # pescoço/gorjal
    c.paint(m_poly([(14, hy - 3), (20, hy - 12), (28, hy - 15), (36, hy - 12), (42, hy - 3),
                    (36, hy - 6), (28, hy - 9), (20, hy - 6)]), "cloth")    # plumagem vermelha
    c.paint(m_poly([(18, hy - 4), (24, hy - 10), (28, hy - 12), (32, hy - 10), (38, hy - 4),
                    (32, hy - 6), (28, hy - 8), (24, hy - 6)]), "gold")     # suporte dourado
    c.paint(m_ellipse(28, hy + 1, 10.5, 10.5), "plate")                     # calota
    c.paint(m_rect(18, hy + 1, 38, hy + 11), "plate")                       # bochechas
    c.detail(m_rect(21, hy + 3, 35, hy + 9), "black")                       # viseira
    c.detail(m_rect(26, hy + 3, 30, hy + 11), "plate")                      # protetor de nariz
    c.dots([(22, hy + 5), (23, hy + 5), (33, hy + 5), (34, hy + 5)], (255, 190, 40))  # olhos âmbar
    c.dots([(x, hy - 2) for x in range(20, 37)], (224, 172, 40))            # friso dourado

    if att == 2:                                  # golpe: lança gigante vindo na direção do espectador
        c.paint(m_rect(9, 38, 15, 48), "plate")
        c.paint(m_rect(8, 46, 15, 53), "skin")
        lanca_diagonal(c, 7, 34, 24, 60, "wood", "gold", 17, 10, cabo_grosso=3)
    return c.render()

# =====================================================================
def montar_sheet(fn, nome, outdir):
    frames = [fn(p) for p in WALK_POSES] + [fn(p) for p in ATTACK_POSES]
    w, h = frames[0].size
    sheet = Image.new("RGBA", (w * FRAMES, h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.paste(f, (i * w, 0))
    os.makedirs(outdir, exist_ok=True)
    caminho = os.path.join(outdir, nome + ".png")
    sheet.save(caminho)
    print(f"  {caminho}  ({w}x{h} por quadro, {FRAMES} quadros)")
    return sheet


def main():
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(raiz, "assets", "images", "enemies")
    print("Gerando espartanos...")
    montar_sheet(hoplita, "hoplita", out)
    montar_sheet(batedor, "batedor", out)
    montar_sheet(campeao, "campeao", out)


if __name__ == "__main__":
    main()
