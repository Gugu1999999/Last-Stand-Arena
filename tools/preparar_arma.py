"""
preparar_arma.py
================
Recorta UMA vista da arma do sprite sheet `assets/images/arma.png` e salva em
`assets/images/arma_costas.png` (é esse arquivo que o jogo carrega).

Uso (na raiz do projeto):
    python tools/preparar_arma.py            # vista "costas" (padrão, a do FPS)
    python tools/preparar_arma.py topo       # outra vista, se quiserem testar

Vistas disponíveis (caixas [x0, y0, x1, y1] dentro do arma.png de 1536x1024):
"""
import os
import sys
from PIL import Image

VISTAS = {
    "costas":       (810, 155, 914, 476),    # vista traseira  <- usada no jogo
    "frente":       (655, 155, 754, 471),
    "topo":         (713, 508, 814, 916),
    "baixo":        (940, 503, 1048, 927),
    "tres_quartos": (303, 540, 607, 927),
    "lado_esq":     (105, 164, 602, 480),
    "lado_dir":     (989, 164, 1481, 482),
}


def main():
    vista = sys.argv[1] if len(sys.argv) > 1 else "costas"
    if vista not in VISTAS:
        sys.exit(f"Vista inválida. Opções: {', '.join(VISTAS)}")
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pasta = os.path.join(raiz, "assets", "images")
    img = Image.open(os.path.join(pasta, "arma.png")).convert("RGBA")
    x0, y0, x1, y1 = VISTAS[vista]
    corte = img.crop((x0 - 6, y0 - 6, x1 + 6, y1 + 6))
    bbox = corte.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    corte = corte.crop(bbox)
    # alfa "quase opaco" (254) vira totalmente opaco onde há desenho
    r, g, b, a = corte.split()
    a = a.point(lambda v: 255 if v > 200 else v)
    corte = Image.merge("RGBA", (r, g, b, a))
    destino = os.path.join(pasta, "arma_costas.png")
    corte.save(destino)
    print(f"Vista '{vista}' salva em {destino} ({corte.width}x{corte.height})")


if __name__ == "__main__":
    main()
