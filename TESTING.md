# Roteiro de testes manuais

Rode `python tests/teste_automatico.py` antes de cada merge. Depois jogue e marque:

## Jogabilidade
- [ ] O jogo abre sem erro e a música toca
- [ ] WASD e mouse respondem bem; o jogador não atravessa a parede
- [ ] Tiro acerta quem está na mira, o X do marcador aparece (vermelho ao abater)
- [ ] Hoplita leva 2 tiros, Batedor 1, Campeão 5 (rodada 1; aumenta com as rodadas)
- [ ] O inimigo "arma" o golpe antes de bater (dá para fugir ou atirar)
- [ ] ESC pausa e libera o mouse; clicar volta ao jogo sem atirar
- [ ] Trocar de janela pausa sozinho

## Ondas
- [ ] Os inimigos saem dos 4 portões, aos poucos
- [ ] Ao terminar: "ARENA LIMPA", pausa de ~3 s, depois "RODADA N+1"
- [ ] Batedores aparecem a partir da rodada 2 e Campeões a partir da rodada 4

## Power-ups
- [ ] Itens aparecem no chão com coluna de luz e dá para pegá-los chegando perto
- [ ] Item fora da visão mostra uma seta na borda da tela
- [ ] Os 4 efeitos funcionam e expiram (HUD mostra o tempo)
- [ ] Explosão: onda de choque no chão, inimigos caem em sequência, a rodada nova só vem depois da pausa

## Visual e som
- [ ] Nada "treme" ou pisca de forma estranha; o FPS aparece no título da janela (meta: 60)
- [ ] Sons faltando não quebram o jogo

## Balanceamento (anote a sensação)
- [ ] Rodada 1-3 muito fácil? Rodada 8+ impossível?
- [ ] Os Batedores são injustos de longe? O Campeão demora demais?
