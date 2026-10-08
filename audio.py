import pygame


class AudioManager:

    def __init__(self):
        pygame.mixer.init()
        self.enabled = True

    def play_music(self):
        pygame.mixer.music.load("assets/music/trilha_sonora.mp3")
        pygame.mixer.music.set_volume(0.4)
        pygame.mixer.music.play(-1)

    def play_shoot(self):
        pass

    def play_zombie_attack(self):
        pass

    def play_powerup(self):
        pass

    def play_explosion(self):
        pass

    def play_game_over(self):
        pass

    def play_round_start(self):
        pass