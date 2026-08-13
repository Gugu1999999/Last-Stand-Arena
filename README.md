# Last Stand Arena — Protótipo Jogável

Protótipo em **Python + pygame** do jogo descrito no documento de design.
Implementa visão em primeira pessoa via **ray casting** (estilo Doom),
arena circular, zumbis vindos dos 4 lados, ondas progressivas e power-ups.

## Como rodar

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Rode o jogo:
   ```bash
   python main.py
   ```

Requer Python 3.9+ e um ambiente com suporte a janela gráfica (rode localmente
na sua máquina, não em servidores sem display).

## Controles

| Tecla / Ação      | Função                          |
|-------------------|----------------------------------|
| `W` / `S`         | Andar para frente / para trás    |
| `A` / `D`         | Deslocamento lateral (strafe)    |
| Mouse             | Olhar ao redor (câmera)          |
| Clique esquerdo   | Atirar                           |
| `ESC`             | Liberar / prender o mouse        |
| `R`               | Reiniciar (após Game Over)       |

## O que já está implementado

- **Ray casting real**: cada coluna da tela é um raio lançado a partir do
  jogador; a distância até a parede da arena (um círculo) é calculada
  analiticamente (interseção raio-círculo) e corrigida contra o efeito
  "olho de peixe", exatamente como descrito na seção 3 do GDD.
- **Campo de visão em cone**: o FOV padrão é limitado (70°) e pode ser
  ampliado temporariamente pelo power-up de visão.
- **Arena circular / coliseu**: o jogador colide com a borda e não pode
  sair dela.
- **Zumbis dos 4 lados**: cada onda nasce em 4 clusters (N/S/L/O) na borda
  da arena e avança em direção ao jogador.
- **Ondas infinitas e progressivas**: a cada rodada, mais zumbis nascem e
  ficam mais rápidos (com um teto de velocidade para manter o jogo justo).
- **Power-ups ao eliminar zumbis** (chance de 18% por abate):
  - `VISÃO AMPLIADA` — aumenta o FOV temporariamente.
  - `TIRO CONTÍNUO` — remove o cooldown entre tiros.
  - `PARALISAÇÃO` — congela todos os zumbis por alguns segundos.
  - `EXPLOSÃO` — elimina instantaneamente todos os zumbis da arena.
- **HUD**: vida, rodada atual, abates, zumbis vivos e power-ups ativos.
- **Game Over e reinício** (`R`).

## Estrutura do código (`main.py`)

- `ray_circle_distance()` — matemática do ray casting contra a arena circular.
- `Player` — posição, ângulo, vida, FOV, power-ups ativos, movimento/colisão.
- `Zombie` — posição, velocidade, vida, IA simples de perseguição/ataque.
- `Game.cast_and_draw()` — renderização em primeira pessoa (paredes via
  raycasting + zumbis como sprites "billboard" projetados por ângulo/distância).
- `Game.update()` / `Game.run()` — laço principal, ondas, tiro, power-ups.

## Próximos passos sugeridos

- Texturizar as paredes (hoje são coloridas por sombreamento de distância).
- Trocar os zumbis por sprites/imagens em vez de formas geométricas.
- Adicionar áudio direcional para ameaças fora do campo de visão.
- Variar tipos de zumbi (corredor, tanque) e adicionar outras armas
  (inspiração Contra Online).
- Sistema de som e efeitos de partícula para tiros e explosões.
