# 🚀 Quick Start - KÁNU Local Dashboard

## Lancement Rapide

```bash
cd kanu_unified/dashboard_local
python app.py
```

Ouvrir: **http://localhost:5000**

---

## Première Utilisation

### 1. Charger le Système (IMPORTANT!)

**Aller à l'onglet ⚙️ Config**

**Choisir la taille du modèle:**

| Modèle | Paramètres | RAM Requise | Vitesse | Usage |
|--------|-----------|-------------|---------|-------|
| **Tiny** | ~50M | ~500 MB | ⚡⚡⚡ Très rapide | Tests rapides |
| **Small** | ~100M | ~1 GB | ⚡⚡ Rapide | Tests |
| **1B** | ~1.4B | ~6 GB | ⚡ Normal | **Recommandé** |
| **2B** | ~2B | ~10 GB | 🐌 Lent | Haute qualité |
| **3B** | ~3B | ~15 GB | 🐌🐌 Très lent | Meilleure qualité |

**Pour débuter:** Choisir **Tiny** ou **Small** pour tester rapidement!

**Device:** Auto (détecte automatiquement GPU ou CPU)

**Cliquer:** 🚀 Load System

⏱️ **Attendre** que le message de succès apparaisse (10-30 secondes selon le modèle)

---

### 2. Tester le Chat

**Onglet 💬 Chat**

Exemples de questions:
```
Qu'est-ce que la deuxième loi de Newton?
What is thermodynamics?
Explique-moi la poussée d'un moteur-fusée
```

**Mode Auto** détecte automatiquement si c'est une question simple ou un design engineering.

---

### 3. Résolution de Problèmes

**Onglet 🧠 Reasoning**

Exemple:
```
Calculate the thrust of a rocket engine with:
- Chamber pressure: 10 MPa
- Nozzle exit pressure: 0.1 MPa
- Mass flow rate: 100 kg/s
- Exit velocity: 3000 m/s
```

Cliquer **Solve Step-by-Step** pour voir le raisonnement détaillé.

---

### 4. Entraînement (Optionnel)

**Onglet 🎓 Training**

**Configuration minimale pour test:**
- Durée: **0.1 heures** (6 minutes)
- Device: Auto
- Checkpoint: 30m
- ✓ Adaptive CPU/GPU
- ✓ Auto Dataset Enrichment

Cliquer **🚀 Start Training**

Voir les métriques en temps réel!

---

## Troubleshooting

### ❌ Erreur "System not loaded"
→ Retourner à l'onglet Config et charger le système

### ❌ Crash lors du chargement
→ Essayer un modèle plus petit (Tiny ou Small)
→ Vérifier la RAM disponible

### ❌ Réponses lentes
→ Normal pour les gros modèles (1B+)
→ Utiliser Tiny/Small pour tests rapides

### ❌ "No module named 'transformers'"
```bash
pip install transformers
```

---

## Modèles Recommandés par Usage

**Tests rapides / Développement:**
- ✅ **Tiny** (50M) - Charge en 5 secondes, répond instantanément

**Démo / Présentation:**
- ✅ **Small** (100M) - Bon compromis vitesse/qualité

**Production / Usage réel:**
- ✅ **1B** - Meilleur compromis qualité/performance

**Haute qualité:**
- ⚠️ **2B** ou **3B** - Nécessite beaucoup de RAM

---

## Commandes Utiles

**Arrêter le serveur:**
```
Ctrl+C dans le terminal
```

**Relancer:**
```bash
python app.py
```

**Vérifier les logs:**
Les logs s'affichent directement dans le terminal.

---

**KÁNU Local Dashboard - Fast, Simple, Powerful** 🚀
