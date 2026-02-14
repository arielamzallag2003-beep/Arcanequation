# Arcane Equation

Un mini-jeu Python (Pygame) où la magie rencontre les équations.

## Concept
- Tu incarnes une mage arcanique.
- Pour lancer des sorts, tu dois résoudre des équations du premier degré.
- Les réponses correctes infligent des dégâts au boss du Néant.
- Les mauvaises réponses te blessent et te laissent vulnérable.

## Contrôles (clavier français AZERTY)
- **ZQSD** : déplacement
- **Entrée** : valider la réponse
- **Retour arrière** : corriger la saisie
- **R** : relancer une partie (après fin de partie)
- **Échap** : quitter

## Lancer le jeu
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

## Assets visuels
Le jeu charge des sprites/texture depuis `assets/`.
Si nécessaire, ils peuvent être régénérés via :

```bash
python3 scripts/generate_assets.py
```

> Note: les fichiers BMP générés sont ignorés par Git pour éviter les problèmes de PR avec les binaires.
