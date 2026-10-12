import os

import pygame

from config import SFX_DIR, MUSIC_DIR

# nome do som -> (arquivos aceitos dentro de assets/sfx, volume)
# Só "tiro" existe hoje. Para adicionar os outros, basta colocar o arquivo
# com um desses nomes na pasta assets/sfx (wav, ogg ou mp3) -- sem mexer em código.
SFX_FILES = {
    "shoot":       (["tiro.mp3", "tiro.wav", "tiro.ogg"], 0.55),
    "explosion":   (["explosao.wav", "explosao.ogg", "explosao.mp3"], 0.9),
    "powerup":     (["powerup.wav", "powerup.ogg", "powerup.mp3"], 0.7),
    "hit":         (["impacto.wav", "impacto.ogg", "impacto.mp3"], 0.5),
    "kill":        (["morte.wav", "morte.ogg", "morte.mp3"], 0.6),
    "hurt":        (["dano.wav", "dano.ogg", "dano.mp3"], 0.8),
    "enemy_attack": (["ataque.wav", "ataque.ogg", "ataque.mp3"], 0.6),
    "round_start": (["rodada.wav", "rodada.ogg", "rodada.mp3"], 0.7),
    "game_over":   (["game_over.wav", "game_over.ogg", "game_over.mp3"], 0.9),
}

MUSIC_FILE = "trilha_sonora.mp3"


class AudioManager:
    """Toca sons. Se não houver placa de som ou o arquivo não existir, não faz nada (nunca quebra o jogo)."""

    def __init__(self):

        self.enabled = False
        self.sounds = {}
        self.music_loaded = False

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.set_num_channels(20)
            self.enabled = True
        except pygame.error as err:
            print(f"[audio] sem áudio disponível: {err}")
            return

        for name, (candidates, volume) in SFX_FILES.items():
            for filename in candidates:
                path = os.path.join(SFX_DIR, filename)
                if os.path.exists(path):
                    try:
                        sound = pygame.mixer.Sound(path)
                        sound.set_volume(volume)
                        self.sounds[name] = sound
                        break
                    except pygame.error as err:
                        print(f"[audio] não consegui carregar {path}: {err}")

        music_path = os.path.join(MUSIC_DIR, MUSIC_FILE)
        if os.path.exists(music_path):
            try:
                pygame.mixer.music.load(music_path)
                self.music_loaded = True
            except pygame.error as err:
                print(f"[audio] não consegui carregar a música: {err}")

    # ------------------------------------------------------------------
    def play(self, name):
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    def play_music(self, volume=0.35):
        if self.enabled and self.music_loaded:
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(-1)

    def stop_music(self):
        if self.enabled and self.music_loaded:
            pygame.mixer.music.fadeout(800)

    def pause_music(self):
        if self.enabled and self.music_loaded:
            pygame.mixer.music.pause()

    def resume_music(self):
        if self.enabled and self.music_loaded:
            pygame.mixer.music.unpause()

    # atalhos (mantidos com os nomes que o time já usava)
    def play_shoot(self):
        self.play("shoot")

    def play_zombie_attack(self):
        self.play("enemy_attack")

    def play_powerup(self):
        self.play("powerup")

    def play_explosion(self):
        self.play("explosion")
