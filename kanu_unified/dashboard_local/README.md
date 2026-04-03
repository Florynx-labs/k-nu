# 🚀 KÁNU Local Dashboard

Dashboard local 100% sans dépendances externes lourdes (pas de Gradio).

## Caractéristiques

- ✅ **100% Local** - Aucune connexion externe requise
- ✅ **Léger** - Flask + HTML/CSS/JS pur
- ✅ **Rapide** - Pas de latence réseau
- ✅ **Moderne** - UI responsive et élégante
- ✅ **Complet** - Toutes les features des deux dashboards

## Fonctionnalités

### 💬 Chat Intelligent
- Conversation avec KÁNU (FR/EN)
- Auto-routing LLM ↔ V2
- Validation physique temps réel
- Historique de conversation

### 🧠 Step-by-Step Reasoning
- Résolution de problèmes détaillée
- Affichage des étapes
- Validation physique

### 🎓 Entraînement Intensif
- Configuration complète
- Monitoring temps réel
- Graphiques loss et ressources
- Métriques détaillées

### 📚 Dataset Viewer
- Visualisation des exemples
- Statistiques

### 📊 System Monitor
- CPU/RAM/GPU usage
- Informations système

### ⚙️ Configuration
- Chargement modèle (1B/2B/3B)
- Sélection device
- Checkpoints

## Installation

```bash
cd kanu_unified/dashboard_local
pip install -r requirements.txt
```

## Lancement

```bash
python app.py
```

Ouvrir **http://localhost:5000**

## Architecture

```
dashboard_local/
├── app.py                  # Backend Flask
├── templates/
│   └── index.html         # Interface HTML
├── static/
│   ├── css/
│   │   └── style.css      # Styles modernes
│   └── js/
│       └── app.js         # JavaScript
└── requirements.txt
```

## API Endpoints

- `GET /` - Dashboard principal
- `GET /api/system/status` - Statut système
- `POST /api/system/load` - Charger système
- `POST /api/chat` - Chat
- `GET /api/chat/history` - Historique
- `POST /api/chat/clear` - Effacer chat
- `POST /api/training/start` - Démarrer entraînement
- `POST /api/training/stop` - Arrêter entraînement
- `GET /api/training/status` - Statut entraînement
- `GET /api/training/metrics` - Métriques
- `GET /api/resources` - Ressources système
- `GET /api/dataset/view` - Voir dataset
- `POST /api/generate` - Générer texte
- `POST /api/reasoning` - Raisonnement

## Avantages vs Gradio

| Feature | Local Dashboard | Gradio |
|---------|----------------|--------|
| Vitesse | ⚡ Très rapide | 🐌 Lent (connexion externe) |
| Latence | ✅ Aucune | ❌ Élevée |
| Offline | ✅ 100% | ❌ Nécessite connexion |
| Personnalisation | ✅ Totale | ⚠️ Limitée |
| Dépendances | ✅ Légères | ❌ Lourdes |
| UI | ✅ Moderne | ⚠️ Standard |

---

**KÁNU Local Dashboard - Fast, Light, Powerful** 🚀
