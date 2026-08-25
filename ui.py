import pygame

from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    PLAYER_MAX_HP,
    WHITE,
    BLACK,
    RED,
    YELLOW,
    ORANGE,
)

from powerups import POWERUP_LABELS


class UI:

    def __init__(self, screen):

        self.screen = screen

        self.font = pygame.font.SysFont(
            "arial",
            20
        )

        self.big_font = pygame.font.SysFont(
            "arial",
            48,
            bold=True
        )

    def draw(
        self,
        player,
        round_num,
        zombies,
        state,
        notification,
        notification_timer,
    ):

        screen = self.screen

        # Vida

        hp_ratio = (
            max(0, player.hp) /
            PLAYER_MAX_HP
        )

        pygame.draw.rect(
            screen,
            (60, 20, 20),
            (
                20,
                SCREEN_HEIGHT - 40,
                220,
                22,
            ),
        )

        pygame.draw.rect(
            screen,
            RED,
            (
                20,
                SCREEN_HEIGHT - 40,
                int(220 * hp_ratio),
                22,
            ),
        )

        pygame.draw.rect(
            screen,
            WHITE,
            (
                20,
                SCREEN_HEIGHT - 40,
                220,
                22,
            ),
            2,
        )

        hp_text = self.font.render(
            f"HP {int(player.hp)}/{PLAYER_MAX_HP}",
            True,
            WHITE,
        )

        screen.blit(
            hp_text,
            (26, SCREEN_HEIGHT - 38)
        )

        # Rodada

        text = self.font.render(
            f"Rodada: {round_num}",
            True,
            YELLOW,
        )

        screen.blit(text, (20, 16))

        # Abates

        text = self.font.render(
            f"Abates: {player.kills}",
            True,
            WHITE,
        )

        screen.blit(text, (20, 42))

        # Zumbis

        alive = sum(
            1
            for zombie in zombies
            if zombie.alive
        )

        text = self.font.render(
            f"Zumbis na arena: {alive}",
            True,
            WHITE,
        )

        screen.blit(text, (20, 68))

        # Power-ups

        y = 100

        for name, remaining in player.active_powerups.items():

            text = self.font.render(
                f"{POWERUP_LABELS[name]}: {remaining:.1f}s",
                True,
                ORANGE,
            )

            screen.blit(
                text,
                (20, y)
            )

            y += 24

        # Notificação

        if notification_timer > 0:

            text = self.big_font.render(
                notification,
                True,
                YELLOW,
            )

            rect = text.get_rect(
                center=(
                    SCREEN_WIDTH // 2,
                    70,
                )
            )

            screen.blit(
                text,
                rect,
            )

        # Game Over

        if state == "game_over":

            overlay = pygame.Surface(
                (
                    SCREEN_WIDTH,
                    SCREEN_HEIGHT,
                )
            )

            overlay.set_alpha(190)

            overlay.fill(BLACK)

            screen.blit(
                overlay,
                (0, 0)
            )

            text = self.big_font.render(
                "FIM DE JOGO",
                True,
                RED,
            )

            screen.blit(
                text,
                text.get_rect(
                    center=(
                        SCREEN_WIDTH // 2,
                        SCREEN_HEIGHT // 2 - 60,
                    )
                ),
            )

            text = self.font.render(
                f"Você sobreviveu até a rodada {round_num} "
                f"com {player.kills} abates.",
                True,
                WHITE,
            )

            screen.blit(
                text,
                text.get_rect(
                    center=(
                        SCREEN_WIDTH // 2,
                        SCREEN_HEIGHT // 2,
                    )
                ),
            )

            text = self.font.render(
                "Pressione R para reiniciar",
                True,
                YELLOW,
            )

            screen.blit(
                text,
                text.get_rect(
                    center=(
                        SCREEN_WIDTH // 2,
                        SCREEN_HEIGHT // 2 + 40,
                    )
                ),
            )