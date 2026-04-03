# 🔧 KÁNU Dashboard - Troubleshooting

## ❌ MemoryError lors de l'entraînement

**Symptôme:**
```
MemoryError
RAM: 0.4/7.8 GB available (94.9% used)
```

**Cause:** Pas assez de RAM disponible pour l'entraînement.

**Solutions:**

### Solution 1: Utiliser un modèle plus petit ✅
```
Tiny (50M) - Utilise ~500 MB RAM
Small (100M) - Utilise ~1 GB RAM
```

### Solution 2: Réduire la durée d'entraînement ✅
```
Au lieu de 1 heure → Essayer 0.1 heure (6 minutes)
```

### Solution 3: Fermer les autres applications ✅
- Fermer navigateurs avec beaucoup d'onglets
- Fermer applications lourdes
- Libérer de la RAM

### Solution 4: Redémarrer le système ✅
Si la RAM reste saturée, redémarrer Windows pour libérer la mémoire.

---

## ❌ Crash lors du chargement du modèle

**Symptôme:**
Le serveur crash après "Loading KÁNU system"

**Solutions:**

### 1. Vérifier la RAM disponible
```powershell
# Dans PowerShell
Get-Process | Sort-Object WS -Descending | Select-Object -First 10
```

### 2. Utiliser le modèle Tiny
Le modèle Tiny charge en 5 secondes et utilise très peu de RAM.

### 3. Vérifier les logs
Les logs dans le terminal indiquent exactement où ça crash.

---

## ❌ "System not loaded"

**Symptôme:**
Erreur "System not loaded. Please load the system first."

**Solution:**
1. Aller à l'onglet **⚙️ Config**
2. Choisir un modèle (recommandé: **Tiny**)
3. Cliquer **🚀 Load System**
4. Attendre le message de succès

---

## ❌ Réponses très lentes

**Symptôme:**
Le chat prend 30+ secondes pour répondre

**Causes possibles:**
- Modèle trop gros (2B ou 3B)
- CPU surchargé
- Pas de GPU disponible

**Solutions:**
1. Utiliser **Tiny** ou **Small** pour tests rapides
2. Fermer autres applications
3. Le modèle 1B est normal qu'il soit lent sur CPU

---

## ❌ Port 5000 déjà utilisé

**Symptôme:**
```
Address already in use
```

**Solution:**
```powershell
# Trouver le processus
netstat -ano | findstr :5000

# Tuer le processus (remplacer PID)
taskkill /PID <PID> /F

# Relancer
python app.py
```

---

## ❌ Module not found

**Symptôme:**
```
ModuleNotFoundError: No module named 'transformers'
```

**Solution:**
```bash
pip install transformers torch
```

---

## 💡 Conseils pour Éviter les Problèmes

### Avant de lancer l'entraînement:

1. **Vérifier la RAM disponible**
   - Minimum 2 GB libre recommandé
   - Fermer applications inutiles

2. **Choisir le bon modèle**
   - **Tiny** si < 2 GB RAM libre
   - **Small** si 2-4 GB RAM libre
   - **1B** si > 4 GB RAM libre

3. **Commencer petit**
   - Durée: 0.1 heure (6 minutes) pour tester
   - Augmenter progressivement si ça marche

4. **Surveiller les ressources**
   - Onglet **📊 Monitor** pour voir CPU/RAM
   - Si RAM > 90%, arrêter l'entraînement

---

## 🆘 Problème Non Résolu?

### Informations à fournir:

1. **Logs complets** du terminal
2. **RAM disponible** (visible dans Monitor)
3. **Modèle utilisé** (Tiny/Small/1B/2B/3B)
4. **Action effectuée** avant le crash

### Commande de diagnostic:
```powershell
# Informations système
systeminfo | findstr /C:"Total Physical Memory" /C:"Available Physical Memory"

# Processus Python actifs
Get-Process python
```

---

## ✅ Configuration Recommandée pour Tests

**Pour éviter tous les problèmes:**

```
Modèle: Tiny (~50M)
Durée: 0.1 heure
Device: Auto
Checkpoint: 30m
✓ Adaptive CPU/GPU
✗ Auto Dataset Enrichment (désactiver pour économiser RAM)
```

Cette configuration fonctionne même avec 1 GB de RAM libre!

---

**Si le problème persiste, redémarrer Windows pour libérer toute la RAM.** 🔄
