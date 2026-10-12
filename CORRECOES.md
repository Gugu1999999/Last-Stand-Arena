# Relatório de correções e novidades

Tudo abaixo foi verificado no código que estava no repositório (`Last-Stand-Arena-main`).

## Bugs corrigidos

| # | Problema encontrado | Onde estava | Como ficou |
|---|---|---|---|
| 1 | **Power-ups não eram coletáveis.** A coleta só acontecia se o jogador chegasse a `distância <= 1.2` unidades do item (o jogador tem raio de 20 e anda 220 por segundo: praticamente impossível). | `game.py` → `collect_powerups` | Raio de coleta de 75 + "ímã" (o item voa até o jogador quando ele chega perto) + coluna de luz no item + seta na borda da tela quando o item está fora do campo de visão. |
| 2 | **Item desenhado "flutuando" no horizonte.** A altura na tela era fixa (`half_h + size * 0.7`), sem relação com a distância. | `game.py` (Renderer) | O item é projetado no chão com a mesma câmera dos inimigos, com sombra, brilho e ícone. |
| 3 | Itens nunca sumiam do chão. | `game.py` | Somem depois de 15 s (piscam nos últimos 4 s). Máximo de 5 itens no chão. |
| 4 | **"Sobreposição da wave sobre a explosão".** Ao pegar a explosão todos morriam no mesmo frame; no frame seguinte já começava a rodada nova, e o aviso `"XXXXX N - EXPLOSÃO!"` era sobrescrito na hora por `"RODADA N"` (duas chamadas seguidas de `notify`). Sobrava até um texto de debug (`XXXXX`). | `game.py` → `start_next_round(explosion=...)` | A explosão agora é uma **onda de choque** que sai do jogador e vai matando os inimigos conforme passa. A rodada nova só começa depois de uma **pausa de 3,2 s** ("ARENA LIMPA"). Avisos grandes (banner) e pequenos (toast) ficam em posições diferentes da tela e nunca se cobrem. |
| 5 | **Classe `Renderer` duplicada.** Estava colada no final do `game.py` (a do `renderer.py` era uma versão antiga, sem power-ups; a do `game.py` "ganhava" por ser definida por último). | `game.py` linhas ~459-894 | Só existe uma: `renderer.py`. O `game.py` ficou só com a lógica do jogo. |
| 6 | **A vida dos zumbis não fazia nada.** `waves.py` calculava `hp = 1 + round // 5`, mas todo tiro executava `zombie.alive = False`. | `waves.py`, `game.py` | Cada tipo de inimigo tem vida própria (`enemy.py`) e cada tiro tira 1 de vida. |
| 7 | Todos os inimigos nasciam de uma vez e ficavam empilhados no mesmo ponto. | `waves.py` | Saem pelos 4 portões, aos poucos, em ordem embaralhada; e há separação para não se sobreporem. |
| 8 | Dano instantâneo: o inimigo batia no mesmo instante em que chegava, sem aviso. | `zombie.py` | O inimigo "arma" o golpe (animação de ~0,3-0,6 s) antes de bater; dá para reagir. Levar um tiro interrompe o golpe. |
| 9 | **Parede e sprites usavam projeções diferentes.** Os raios da parede variavam linearmente com o ângulo, os sprites usavam tangente (perspectiva). Desalinhava, principalmente com a visão ampliada (110°). | `game.py` (Renderer) | Tudo usa a mesma projeção em perspectiva. |
| 10 | Mira com tolerância fixa de 4° para qualquer distância/tamanho. | `game.py` → `try_shoot` | O acerto depende do tamanho do inimigo e da distância (com uma pequena ajuda de mira). |
| 11 | Caminho da música relativo à pasta onde o jogo é executado (`"assets/music/..."`): quebra se rodar de outra pasta/IDE. | `audio.py` | Caminhos relativos ao próprio arquivo (`config.py`). |
| 12 | `AudioManager()` era criado **antes** de `pygame.init()` e sem proteção: se não houver placa de som ou o arquivo faltar, o jogo fecha com erro. | `game.py`, `audio.py` | Ordem corrigida; áudio à prova de falhas (sem som, o jogo continua). |
| 13 | Com `ESC` o mouse era liberado, mas o jogo continuava rodando (inimigos atacando) e `mouse_held` podia ficar "preso" no tiro contínuo. | `game.py` | `ESC` agora **pausa**. Perder o foco da janela também pausa. Clicar volta ao jogo sem atirar. |
| 14 | O FOV "pulava" instantaneamente ao pegar/perder a visão ampliada. | `player.py` | Transição suave. |
| 15 | Bala desenhada sempre na linha do horizonte, sem relação com a arma. | `game.py` (Renderer) | Traçante 3D que sai da arma e vai até o alvo. |
| 16 | `assets/images`, `assets/fonts` e `assets/sounds` estão no repositório como **arquivos vazios** (não pastas). Qualquer tentativa de salvar uma imagem em `assets/images/` falha. | repositório | Veja "Antes de copiar" abaixo. |

## Novidades

- **Cenário:** `fundo2.png` virou a parede da arena (ray casting com textura). A imagem é repetida em 4 faixas de 90°, espelhadas, uma por portão, e **os portões ficam exatamente nos 4 pontos de onde os inimigos saem**. Ao andar até a parede, ela se aproxima de verdade.
- **Arma:** vista traseira do `arma.png` (a que um FPS mostra), com balanço ao andar, coice, clarão no tiro e "arrasto" ao girar a câmera.
- **3 inimigos espartanos** (pixel-art, 4 quadros de caminhada + preparar golpe + golpe):
  | Tipo | Papel | Vida | Velocidade | Dano |
  |---|---|---|---|---|
  | Hoplita | básico (escudo, lança) | 2 | normal | 12 |
  | Batedor | rápido, frágil, corre em zigue-zague | 1 | 1,75x | 8 |
  | Campeão | tanque (armadura negra, escudo gigante) | 5 | 0,62x | 24 |
  O Batedor aparece a partir da rodada 2 e o Campeão a partir da rodada 4. Para mexer nos números: `enemy.py` (tipos) e `waves.py` (composição das ondas).
- **Efeitos:** flash e tremor de tela, partículas (sangue, faíscas, poeira, fogo, brilhos), manchas de sangue no chão, areia/pedras no chão (dão noção de movimento), sombra dos inimigos, queda e desaparecimento dos corpos, flash branco ao acertar, inimigos azulados quando congelados, marcador de acerto na mira, vinheta de dano e de vida baixa, vinheta escura nas bordas (reforça a visão limitada), onda de choque da explosão no chão.
- **HUD:** barra de vida, rodada, abates, inimigos restantes, cartões dos power-ups ativos com ícone e tempo, contagem regressiva entre rodadas, tela de pausa e de fim de jogo.

## Antes de copiar para o repositório

1. **Apague** `assets/images`, `assets/fonts` e `assets/sounds` (são arquivos vazios). Este pacote traz `assets/images/` e `assets/fonts/` como pastas de verdade.
2. **Apague** `zombie.py` (substituído por `enemy.py`).
3. `git add` nos PNGs novos (`assets/images/**`).
