# 🚀 Guide Rapide - Entraînement 2 Minutes (50M paramètres)

## Commande Simple

```bash
python kanu_cli.py train --model tiny --duration 2m --mode intensive
```

## Détails de la Commande

- `--model tiny` : Modèle de 50 millions de paramètres (rapide à entraîner)
- `--duration 2m` : Durée de 2 minutes
- `--mode intensive` : Mode d'entraînement intensif avec adaptation dynamique

## Options Supplémentaires

### Avec CPU uniquement
```bash
python kanu_cli.py train --model tiny --duration 2m --mode intensive --device cpu
```

### Avec batch size personnalisé
```bash
python kanu_cli.py train --model tiny --duration 2m --mode intensive --batch-size 2
```

### Avec checkpoint personnalisé
```bash
python kanu_cli.py train --model tiny --duration 2m --mode intensive --save-dir ./my_checkpoints
```

## Autres Durées Possibles

```bash
# 5 minutes
python kanu_cli.py train --model tiny --duration 5m --mode intensive

# 10 minutes
python kanu_cli.py train --model tiny --duration 10m --mode intensive

# 30 minutes
python kanu_cli.py train --model tiny --duration 30m --mode intensive

# 1 heure
python kanu_cli.py train --model tiny --duration 1h --mode intensive
```

## Mode Standard (par époques)

Si vous préférez entraîner par nombre d'époques au lieu de durée :

```bash
# 5 époques
python kanu_cli.py train --model tiny --epochs 5

# 10 époques
python kanu_cli.py train --model tiny --epochs 10
```

## Après l'Entraînement

### Tester le modèle entraîné
```bash
python kanu_cli.py inference --model tiny --checkpoint ./checkpoints/final_checkpoint.pt
```

### Voir le statut
```bash
python kanu_cli.py status
```

## Modèles Disponibles

| Modèle | Paramètres | Recommandation |
|--------|-----------|----------------|
| `tiny` | 50M | Tests rapides (2-10 min) |
| `small` | 100M | Tests moyens (10-30 min) |
| `1b` | 1.0B | Production légère (1-24h) |
| `2b` | 2.0B | Production standard (12-48h) |
| `3b` | 3.0B | Production avancée (24-72h) |

## Exemple Complet

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Lancer l'entraînement de 2 minutes
python kanu_cli.py train --model tiny --duration 2m --mode intensive

# 3. Le checkpoint sera sauvegardé dans ./checkpoints/

# 4. Tester le modèle
python kanu_cli.py inference --model tiny --checkpoint ./checkpoints/final_checkpoint.pt
```

## Monitoring Pendant l'Entraînement

L'entraînement affichera en temps réel :
- ✅ Loss (perte)
- ✅ Learning rate
- ✅ GPU/CPU usage
- ✅ Tokens/seconde
- ✅ Temps restant
- ✅ Pensées des agents (si activé)

## Troubleshooting

### Erreur de mémoire GPU
```bash
# Réduire le batch size
python kanu_cli.py train --model tiny --duration 2m --mode intensive --batch-size 1
```

### Utiliser CPU au lieu de GPU
```bash
python kanu_cli.py train --model tiny --duration 2m --mode intensive --device cpu
```

### Dataset manquant
Le dataset sera créé automatiquement au premier lancement !

---

**Prêt à commencer ? Lancez simplement :**
```bash
python kanu_cli.py train --model tiny --duration 2m --mode intensive
```
