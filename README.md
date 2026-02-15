# Arcane Equation

Jeu Python/Pygame où la **magie est pilotée par des équations** (pas un quiz d'équations).

## Gameplay
- Tu ajustes des **canaux mathématiques** (`a`, `b`, `c`, `ω`, `φ`).
- Chaque école de sort (linéaire, quadratique, sinusoïdale) calcule sa puissance à partir de ces paramètres.
- Tu construis donc ton build magique en temps réel via les coefficients.

## Contrôles AZERTY (clavier français)
- `ZQSD` déplacement.
- `1..9` modulation des canaux d'équations.
- `F/G/H` lance les 3 sorts.
- `Espace` active une barrière magique consommant du mana.
- `R` recommencer (fin de partie).
- `Échap` quitter.

## Lancer
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

## Assets
Les sprites/texture BMP sont générés localement au besoin et ignorés par Git.

## Système avancé
- Statuts: brûlure, ralentissement et bouclier dynamique.
- IA ennemie à phases: pression, récupération, désespoir.
- Intentions ennemies affichées dans l'UI, combo et suivi du dernier sort.

## Direction visuelle
- Fond astral animé, grilles arcanes pulsées, glow des projectiles.
- Impacts avec particules et léger camera shake pour renforcer le feedback.
