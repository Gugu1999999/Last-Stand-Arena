import pygame


class AudioManager:

    def __init__(self):
        pygame.mixer.init()
        self.enabled = True

    def play_music(self):
        pygame.mixer.music.load("assets/music/trilha_sonora.mp3")
        pygame.mixer.music.set_volume(0.1)
        pygame.mixer.music.play(-1)
        
    def play_shoot(self):
        sound = pygame.mixer.Sound("assets/sfx/tiro.mp3")
        sound.set_volume(0.4)
        sound.play()

    def play_zombie_attack(self):
        sound = pygame.mixer.Sound("assets/sfx/ataquezombie.mp3")
        sound.set_volume(0.2)
        sound.play()

    def play_powerup(self):
        sound = pygame.mixer.Sound("assets/sfx/powerup.mp3")
        sound.set_volume(0.4)
        sound.play()

    def play_explosion(self):
        sound = pygame.mixer.Sound("assets/sfx/explosao.mp3")
        sound.set_volume(0.4)
        sound.play()

    def play_game_over(self):
        sound = pygame.mixer.Sound("assets/sfx/gameover.mp3")
        sound.set_volume(0.8)
        sound.play()

    def play_round_start(self):
        sound = pygame.mixer.Sound("assets/sfx/restart.mp3")
        sound.set_volume(0.7)
        sound.play()