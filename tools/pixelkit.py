"""
pixelkit.py
===========
Mini biblioteca para desenhar pixel-art por código (usada pelo gerar_espartanos.py).

Ideia: cada "parte" do personagem (elmo, escudo, braço...) é desenhada como uma
máscara de pixels com um MATERIAL (bronze, tecido, pele...). Na hora de gerar a
imagem final, cada material vira 3 tons (escuro/médio/claro) e a luz vem do
canto superior esquerdo, então as bordas de cima/esquerda ficam claras e as de
baixo/direita ficam escuras. Cada parte ganha também um contorno escuro.
"""
import math
from PIL import Image

OUTLINE = (30, 18, 22)

# material: (escuro, médio, claro)
RAMPS = {
    "bronze":  ((104, 60, 22),  (168, 104, 38), (232, 178, 84)),
    "gold":    ((150, 100, 20), (226, 174, 40), (255, 230, 120)),
    "cloth":   ((92, 14, 18),   (172, 30, 32),  (226, 70, 54)),
    "cloth2":  ((60, 14, 30),   (112, 24, 44),  (170, 50, 70)),
    "skin":    ((156, 90, 54),  (210, 138, 90), (242, 182, 128)),
    "leather": ((72, 42, 24),   (120, 74, 42),  (170, 112, 62)),
    "wood":    ((92, 56, 28),   (140, 92, 48),  (190, 138, 78)),
    "steel":   ((84, 92, 106),  (158, 168, 182), (234, 240, 246)),
    "plate":   ((34, 34, 44),   (72, 72, 88),   (132, 132, 152)),
    "hair":    ((34, 22, 16),   (72, 46, 28),   (112, 74, 44)),
    "black":   ((8, 6, 8),      (20, 16, 20),   (44, 36, 44)),
    "white":   ((200, 196, 188), (244, 240, 230), (255, 255, 255)),
}


# ---------------------------------------------------------------- máscaras
def m_rect(x0, y0, x1, y1):
    """retângulo [x0,x1) x [y0,y1)"""
    return {(x, y) for y in range(int(y0), int(y1)) for x in range(int(x0), int(x1))}


def m_ellipse(cx, cy, rx, ry):
    out = set()
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                out.add((x, y))
    return out


def m_poly(pts):
    """polígono preenchido (varredura por linhas)"""
    ys = [p[1] for p in pts]
    out = set()
    n = len(pts)
    for y in range(int(math.floor(min(ys))), int(math.ceil(max(ys))) + 1):
        yc = y + 0.5
        xs = []
        for i in range(n):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % n]
            if (y0 <= yc < y1) or (y1 <= yc < y0):
                xs.append(x0 + (yc - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            for x in range(int(round(xs[i])), int(round(xs[i + 1]))):
                out.add((x, y))
    return out


def m_line(x0, y0, x1, y1, thick=1):
    out = set()
    steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    for i in range(steps + 1):
        t = i / steps
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        for dx in range(thick):
            for dy in range(thick):
                out.add((int(round(x)) + dx - thick // 2, int(round(y)) + dy - thick // 2))
    return out


def m_mirror(mask, axis_x2):
    """espelha a máscara em torno de x = axis_x2/2"""
    return {(axis_x2 - 1 - x, y) for (x, y) in mask}


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.cells = {}   # (x,y) -> ("m", material) | ("c", (r,g,b))

    def paint(self, mask, mat, outline=True):
        """pinta uma parte (com contorno próprio, por trás do preenchimento)"""
        mask = {(x, y) for (x, y) in mask if 0 <= x < self.w and 0 <= y < self.h}
        if outline:
            for (x, y) in mask:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    p = (x + dx, y + dy)
                    if p not in mask and 0 <= p[0] < self.w and 0 <= p[1] < self.h:
                        self.cells[p] = ("c", OUTLINE)
        for p in mask:
            self.cells[p] = ("m", mat)

    def dots(self, pts, color):
        for (x, y) in pts:
            if 0 <= x < self.w and 0 <= y < self.h:
                self.cells[(x, y)] = ("c", color)

    def detail(self, mask, mat):
        """pinta SEM contorno (detalhes dentro de uma parte já pintada)"""
        self.paint(mask, mat, outline=False)

    # ------------------------------------------------------------- saída
    def render(self):
        img = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        px = img.load()

        def same(x, y, mat):
            c = self.cells.get((x, y))
            return c is not None and c[0] == "m" and c[1] == mat

        for (x, y), cell in self.cells.items():
            if cell[0] == "c":
                px[x, y] = cell[1] + (255,)
                continue
            mat = cell[1]
            dark, mid, light = RAMPS[mat]
            up, left = same(x, y - 1, mat), same(x - 1, y, mat)
            down, right = same(x, y + 1, mat), same(x + 1, y, mat)
            hl = (not up) or (not left)
            dk = (not down) or (not right)
            if hl and not dk:
                col = light
            elif dk and not hl:
                col = dark
            else:
                col = mid
            px[x, y] = col + (255,)
        # contorno externo final (garante silhueta fechada)
        for (x, y) in list(self.cells.keys()):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p = (x + dx, y + dy)
                if p not in self.cells and 0 <= p[0] < self.w and 0 <= p[1] < self.h:
                    px[p[0], p[1]] = OUTLINE + (255,)
        return img
