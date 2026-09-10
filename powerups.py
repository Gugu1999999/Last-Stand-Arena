POWERUP_TYPES = [
    "vision",
    "rapid_fire",
    "freeze",
    "explosion",
]

POWERUP_LABELS = {
    "vision": "VISÃO AMPLIADA",
    "rapid_fire": "TIRO CONTÍNUO",
    "freeze": "PARALISAÇÃO",
    "explosion": "EXPLOSÃO",
}

# Peso relativo de cada power-up dentro do sorteio (quanto maior, mais chance).
# Explosão estava saindo raríssimo (mesma chance dos outros); agora sai bem mais.
POWERUP_WEIGHTS = {
    "vision": 1,
    "rapid_fire": 1,
    "freeze": 1,
    "explosion": 2,
}