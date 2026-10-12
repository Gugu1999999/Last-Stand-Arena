# Last Stand Arena

Jogo de sobrevivência em primeira pessoa (ray casting) em uma arena circular. Espartanos saem
pelos 4 portões em ondas cada vez mais fortes; você só enxerga um cone de visão.

## Como rodar

```bash
pip install -r requirements.txt
python main.py
```

Python 3.9+. Pode rodar de qualquer pasta.

## Controles

| Tecla / ação | Função |
|---|---|
| `W` `A` `S` `D` | andar |
| Mouse | olhar ao redor |
| Clique esquerdo (segurar com *Tiro contínuo*) | atirar |
| `ESC` | pausar / continuar |
| `R` | reiniciar (no fim de jogo) |

## Power-ups (soltos ao abater espartanos; é só chegar perto para pegar)

| Item | Efeito |
|---|---|
| Visão ampliada | abre o campo de visão de 70° para 110° por 8 s |
| Tiro contínuo | cadência muito maior por 7 s (segure o clique) |
| Paralisação | congela todos os inimigos por 4 s |
| Explosão | onda de choque que elimina todos os espartanos da arena e encerra a rodada |

## Quem mexe em quê (papéis do grupo)

| Papel | Arquivos |
|---|---|
| **Líder** | `game.py`, `main.py`, `config.py`, `utils.py` |
| **Desenvolvedor 1** (tiro, inimigos, pontuação, vitória/derrota) | `enemy.py` (tipos e IA), `shoot.py`, `game.py` → `try_shoot` |
| **Desenvolvedor 2** (itens, vida/energia, ondas) | `powerups.py`, `waves.py`, `player.py` |
| **Artes** | `assets/images/**`, `sprites.py`, `renderer.py`, `effects.py`, `tools/` |
| **Artes e Desenvolvimento** (menu, HUD, telas) | `ui.py` |
| **Artes e Testes** (sons, testes, balanceamento) | `audio.py`, `assets/sfx/`, `tests/` |

## Trocar imagens e sons (sem mexer em código)

- **Cenário:** substitua `assets/images/fundo2.png` (mesmo tamanho; a linha onde a parede encontra a areia
  está em `WALL_TEXTURE_BASE_ROW` no `config.py`). A imagem é repetida em 4 faixas espelhadas, com o centro de
  cada faixa sendo um portão.
- **Arma:** `assets/images/arma_costas.png`. Para recortar outra vista do `arma.png`:
  `python tools/preparar_arma.py topo` (opções no topo do arquivo).
- **Inimigos:** `assets/images/enemies/hoplita.png`, `batedor.png`, `campeao.png`. Cada um é uma faixa com
  **6 quadros do mesmo tamanho**: `0-3` caminhada, `4` preparando o golpe, `5` golpe. O tamanho do quadro pode ser
  qualquer um (o jogo escala sozinho), mas mantenha a ordem. Os sprites atuais foram gerados por código
  (`python tools/gerar_espartanos.py`) e servem de base para o time de Artes redesenhar.
- **Sons:** coloque na pasta `assets/sfx/` com estes nomes (`.wav`, `.ogg` ou `.mp3`): `tiro` (já existe),
  `explosao`, `powerup`, `impacto`, `morte`, `dano`, `ataque`, `rodada`, `game_over`. Os que não existirem
  são simplesmente ignorados. A música é `assets/music/trilha_sonora.mp3`.

## Ajustar o balanceamento

| O que | Onde |
|---|---|
| Vida, velocidade, dano, alcance de cada espartano | `ENEMY_TYPES` em `enemy.py` |
| Quantos inimigos / quando cada tipo aparece / velocidade por rodada | `waves.py` |
| Chance de drop, duração dos power-ups, raio de coleta | `config.py` |
| Pausa entre rodadas, velocidade da explosão | `config.py` |

## Testes

```bash
python tests/teste_automatico.py            # rápido (~20 s)
python tests/teste_automatico.py --longo    # + 10 min de jogo simulado por um robô
python tests/teste_automatico.py --capturas # salva imagens em tests/capturas/
```

Roda sem abrir janela. Veja também `TESTING.md` para o roteiro de testes manuais.

## Como o ray casting funciona aqui (resumo)

Para cada coluna da tela, um raio sai do jogador; a distância até a parede circular da arena
(interseção raio-círculo, `utils.ray_circle_distance`) define a altura da faixa da parede e qual pedaço do
`fundo2.png` aparece. Inimigos, itens e partículas são "billboards" projetados com a mesma câmera
(`renderer.project`) e desenhados do mais longe para o mais perto. Detalhes no topo de `renderer.py`.

Veja `CORRECOES.md` para a lista do que foi corrigido e adicionado.
