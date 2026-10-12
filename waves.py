import math
import random

from config import ARENA_RADIUS, GATE_ANGLES


class SpawnOrder:
    """Um inimigo agendado para nascer `time` segundos depois do início da onda."""

    def __init__(self, time, kind, gate_angle):
        self.time = time
        self.kind = kind
        self.gate_angle = gate_angle


class WaveManager:

    def __init__(self):
        self.round_num = 0

    def start_next_round(self):
        """Avança a rodada e devolve (fila_de_spawn, velocidade_base)."""

        self.round_num += 1

        return self.build_queue(self.round_num), self.base_speed(self.round_num)

    # -- dificuldade ----------------------------------------------------
    @staticmethod
    def base_speed(round_num):
        return min(55 + round_num * 6, 230)

    @staticmethod
    def enemy_count(round_num):
        return 4 + round_num * 2

    @staticmethod
    def composition(round_num):
        """Quantos de cada tipo nascem nesta rodada."""

        total = WaveManager.enemy_count(round_num)

        champions = max(0, (round_num - 2) // 2)          # a partir da rodada 4
        champions = min(champions, max(1, total // 4)) if round_num >= 4 else 0

        scouts = 0
        if round_num >= 2:
            share = min(0.40, 0.10 + 0.04 * round_num)
            scouts = round(total * share)

        hoplites = max(1, total - champions - scouts)

        return {"hoplita": hoplites, "batedor": scouts, "campeao": champions}

    def build_queue(self, round_num):
        """
        Em vez de nascer todo mundo de uma vez (e empilhar), os inimigos saem
        dos 4 portões aos poucos, em ordem embaralhada.
        """

        comp = self.composition(round_num)

        kinds = []
        for kind, amount in comp.items():
            kinds += [kind] * amount
        random.shuffle(kinds)

        # campeões não saem logo de cara: ficam para a segunda metade da onda
        kinds.sort(key=lambda k: 1 if k == "campeao" else 0)
        head = [k for k in kinds if k != "campeao"]
        tail = [k for k in kinds if k == "campeao"]
        random.shuffle(head)
        cut = len(head) // 2
        kinds = head[:cut] + tail + head[cut:]

        gates = []
        queue = []
        t = 0.4

        for kind in kinds:
            if not gates:                      # ciclo embaralhado: usa os 4 portões
                gates = GATE_ANGLES[:]
                random.shuffle(gates)

            queue.append(SpawnOrder(t, kind, gates.pop()))

            t += random.uniform(0.35, 0.85) * max(0.55, 1.0 - round_num * 0.03)

        return queue

    @staticmethod
    def spawn_position(gate_angle):
        angle = gate_angle + random.uniform(-0.07, 0.07)
        radius = ARENA_RADIUS - 70

        return math.cos(angle) * radius, math.sin(angle) * radius
