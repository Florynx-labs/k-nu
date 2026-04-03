# 🚀 KÁNU - Architecture Unifiée Complète

> **"Born from love. Bound by physics."**
> Developed by Florynx Labs

## Vue d'Ensemble

KÁNU est un système d'intelligence d'ingénierie complet intégrant:
- **KÁNU LLM** - Modèle de langage 1-3B paramètres (FR/EN)
- **KÁNU V2** - Système multi-agents avec World Model
- **KÁNU Rust Core** - Moteur de calcul haute performance
- **Dashboard Unifié** - Interface complète d'entraînement et interaction

---

## 📁 Structure du Projet

```
kanu/
│
├── kanu_llm_prototype/           # Mini-LLM 1-3B paramètres
│   ├── model/
│   │   └── kanu_architecture.py  # Architecture transformer
│   ├── training/
│   │   └── trainer.py            # Système d'entraînement
│   ├── inference/
│   │   └── kanu_inference.py     # Moteur d'inférence
│   └── dashboard/
│       └── app.py                # Dashboard Gradio
│
├── kanu_v2/                      # Système multi-agents
│   ├── mini_llm/
│   │   └── transformer.py        # Reasoner interne
│   ├── agents/
│   │   └── collaborative_agents.py  # Agents spécialisés
│   ├── world_model/
│   │   └── simulation_v2.py      # Simulation physique
│   ├── workflow/
│   │   └── ten_step_workflow.py  # Workflow 10 étapes
│   └── kanu_v2_orchestrator.py   # Orchestrateur principal
│
├── kanu_intelligence/            # Système d'intelligence
│   ├── intelligence_orchestrator.py
│   ├── chat_interface.py
│   └── multi_design_system.py
│
├── kanu-llm/                     # (Legacy - à migrer)
│
├── kanu_unified/                 # 🆕 NOUVEAU - Intégration complète
│   ├── core/
│   │   ├── unified_orchestrator.py    # Orchestrateur unifié
│   │   ├── llm_world_model_bridge.py  # Pont LLM ↔ World Model
│   │   └── resource_manager.py        # Gestion ressources CPU/GPU
│   ├── training/
│   │   ├── intensive_trainer.py       # Entraînement intensif adaptatif
│   │   ├── dataset_enrichment.py      # Enrichissement auto dataset
│   │   └── training_monitor.py        # Monitoring temps réel
│   ├── dashboard/
│   │   └── unified_dashboard.py       # Dashboard unifié complet
│   └── config/
│       └── system_config.yaml         # Configuration système
│
└── KANU_UNIFIED_ARCHITECTURE.md  # 🆕 Cette documentation
```

---

## 🔗 Flux d'Intégration

```
┌─────────────────────────────────────────────────────────────────┐
│                    KÁNU UNIFIED SYSTEM                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  User Input (Dashboard)                                         │
│       ↓                                                          │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Unified Orchestrator                                  │    │
│  │  • Route vers LLM ou V2 selon contexte                 │    │
│  │  • Gestion sessions et état                            │    │
│  └────────────────────────────────────────────────────────┘    │
│       ↓                          ↓                              │
│  ┌──────────────┐          ┌──────────────┐                    │
│  │  KÁNU LLM    │ ←bridge→ │  KÁNU V2     │                    │
│  │  (1-3B)      │          │  (Agents)    │                    │
│  └──────────────┘          └──────────────┘                    │
│       ↓                          ↓                              │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  World Model V2                                        │    │
│  │  • Simulations physiques                               │    │
│  │  • Validation designs                                  │    │
│  │  • Monte Carlo testing                                 │    │
│  └────────────────────────────────────────────────────────┘    │
│       ↓                                                          │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Intensive Training System                             │    │
│  │  • Adaptive CPU/GPU usage                              │    │
│  │  • Real-time monitoring                                │    │
│  │  • Auto dataset enrichment                             │    │
│  └────────────────────────────────────────────────────────┘    │
│       ↓                                                          │
│  Engineering-Ready Output                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Composants Clés

### 1. KÁNU LLM (Mini-LLM 1-3B)
**Localisation:** `kanu_llm_prototype/`

**Rôle:**
- Compréhension langage naturel (FR/EN)
- Génération de texte technique
- Raisonnement étape par étape
- Validation physique de base

**Connexions:**
- → World Model V2 (pour simulations)
- → Agents V2 (pour débats)
- → Dataset (pour entraînement)

### 2. KÁNU V2 (Multi-Agents + World Model)
**Localisation:** `kanu_v2/`

**Rôle:**
- Débat multi-agents spécialisés
- Workflow strict 10 étapes
- Simulations physiques avancées
- Génération de packages engineering

**Connexions:**
- ← LLM (pour raisonnement linguistique)
- → World Model (pour validation)
- → Intelligence Orchestrator

### 3. World Model V2
**Localisation:** `kanu_v2/world_model/simulation_v2.py`

**Rôle:**
- Simulations multi-scénarios
- Monte Carlo analysis
- Failure-first testing
- Surrogate models

**Connexions:**
- ← LLM (reçoit designs à valider)
- ← V2 Agents (reçoit propositions)
- → Training (génère données)

### 4. Unified Orchestrator
**Localisation:** `kanu_unified/core/unified_orchestrator.py`

**Rôle:**
- Point d'entrée unique
- Routage intelligent LLM ↔ V2
- Gestion de sessions
- Coordination globale

### 5. Intensive Training System
**Localisation:** `kanu_unified/training/`

**Rôle:**
- Entraînement adaptatif CPU/GPU
- Détection charge système
- Enrichissement auto dataset
- Monitoring temps réel

---

## 🔄 Scénarios d'Utilisation

### Scénario 1: Chat Simple
```
User: "Comment fonctionne un moteur-fusée?"
  ↓
Unified Orchestrator
  ↓
KÁNU LLM (génération texte)
  ↓
Response: "Un moteur-fusée fonctionne selon..."
```

### Scénario 2: Design Engineering Complet
```
User: "Design a 50 kN vacuum engine"
  ↓
Unified Orchestrator
  ↓
KÁNU V2 (workflow 10 étapes)
  ↓
Multi-Agents (débat concepts)
  ↓
World Model (simulations)
  ↓
KÁNU LLM (explication résultats)
  ↓
Engineering Package complet
```

### Scénario 3: Entraînement Intensif
```
User: Lance entraînement 24h sur GPU
  ↓
Intensive Trainer
  ↓
Resource Manager (détecte GPU disponible)
  ↓
Training Loop (adaptatif)
  ├─ Charge système faible → 100% GPU
  ├─ Autre processus détecté → 60% GPU
  └─ Dataset enrichment automatique
  ↓
Checkpoints + Metrics en temps réel
```

---

## 🎛️ Dashboard Unifié

### Onglets Disponibles

**1. 💬 Chat Intelligent**
- Conversation avec KÁNU LLM
- Auto-routing vers V2 si design complexe
- Validation physique temps réel

**2. 🧠 Engineering Design**
- Workflow complet 10 étapes
- Multi-agents debate
- World Model simulations
- Package delivery

**3. 🎓 Intensive Training**
- Configuration durée (heures/jours)
- Sélection CPU/GPU
- Fréquence entraînement
- Adaptation charge système
- Monitoring temps réel:
  - Loss curves
  - GPU/CPU usage
  - Dataset growth
  - Agent thoughts
  - New knowledge acquired

**4. 📊 System Monitor**
- État de tous les composants
- Ressources utilisées
- Performances
- Logs système

**5. 📚 Knowledge Base**
- Dataset viewer
- Physics rules
- Engineering constraints
- Training history

**6. ⚙️ Configuration**
- Model settings
- Training parameters
- Resource allocation
- System preferences

---

## 🚀 Démarrage Rapide

### Installation Complète

```bash
# Installer toutes les dépendances
cd kanu
pip install -r kanu_llm_prototype/requirements.txt
pip install -r kanu_unified/requirements.txt

# Créer dataset initial
cd kanu_llm_prototype
python -c "from training.trainer import create_engineering_dataset; create_engineering_dataset('./datasets/engineering_dataset.json')"
```

### Lancer le Dashboard Unifié

```bash
cd kanu_unified
python dashboard/unified_dashboard.py
```

Ouvrir http://localhost:7860

### Lancer Entraînement Intensif

Via Dashboard:
1. Aller à l'onglet "🎓 Intensive Training"
2. Choisir durée (ex: 24 heures)
3. Sélectionner GPU ou CPU
4. Configurer fréquence (ex: toutes les 2h)
5. Activer adaptation charge système
6. Cliquer "Start Intensive Training"

Via CLI:
```bash
python kanu_unified/training/intensive_trainer.py \
  --duration 24 \
  --device gpu \
  --frequency 2h \
  --adaptive \
  --model_size 1b
```

---

## 🔧 Configuration Système

**Fichier:** `kanu_unified/config/system_config.yaml`

```yaml
# KÁNU Unified Configuration

llm:
  model_size: "1b"  # 1b, 2b, 3b
  checkpoint: "./checkpoints/best_model.pt"
  device: "cuda"  # cuda, cpu, auto

v2:
  enable_agents: true
  enable_world_model: true
  workflow_strict: true

training:
  intensive:
    max_gpu_usage: 0.95  # 95% max
    min_gpu_usage: 0.30  # 30% min si autre processus
    adaptation_interval: 10  # secondes
    checkpoint_frequency: "1h"
    dataset_enrichment: true
    
  resources:
    auto_detect: true
    prefer_gpu: true
    fallback_cpu: true

dashboard:
  port: 7860
  share: false
  auth: false

monitoring:
  log_interval: 100
  save_metrics: true
  show_agent_thoughts: true
  show_new_knowledge: true
```

---

## 📈 Entraînement Intensif Adaptatif

### Fonctionnalités

**1. Détection Automatique Ressources**
```python
# Détecte automatiquement:
- GPU disponibles (CUDA, ROCm, MPS)
- CPU cores et threads
- RAM disponible
- Charge système actuelle
```

**2. Adaptation Dynamique**
```python
# Si charge système faible:
→ Utilise 95% GPU/CPU

# Si autre processus détecté:
→ Réduit à 60% GPU/CPU
→ Maintient qualité entraînement
→ Évite ralentissement système
```

**3. Enrichissement Dataset Automatique**
```python
# Pendant l'entraînement:
- Génère nouveaux exemples
- Valide contre physique
- Ajoute au dataset
- Re-entraîne sur nouvelles données
```

**4. Monitoring Temps Réel**
```python
# Affiche en direct:
- Loss curves (train/val)
- GPU/CPU usage %
- Memory usage
- Tokens/second
- Agent thoughts
- New knowledge acquired
- Physics violations detected
```

### Exemple de Session

```
🎓 INTENSIVE TRAINING SESSION
Duration: 24 hours
Device: NVIDIA RTX 3090 (24GB)
Model: KÁNU-1B

[00:00:00] Starting training...
[00:00:10] GPU Usage: 95% | Loss: 3.245 | Tokens/s: 8500
[00:00:20] GPU Usage: 95% | Loss: 3.198 | Tokens/s: 8520

[00:15:30] ⚠️ Other process detected (Chrome)
[00:15:31] Adapting: GPU 95% → 60%
[00:15:32] GPU Usage: 60% | Loss: 3.012 | Tokens/s: 5100

[00:20:00] Process ended
[00:20:01] Restoring: GPU 60% → 95%
[00:20:02] GPU Usage: 95% | Loss: 2.998 | Tokens/s: 8550

[01:00:00] 💡 New knowledge acquired:
  - "Niobium C-103 melting point: 2750K"
  - "LOX/CH4 optimal mixture ratio: 3.5"
  
[01:00:01] Dataset enriched: +15 examples
[01:00:02] Checkpoint saved: checkpoint_1h.pt

[02:00:00] 🧠 Agent thoughts captured:
  - Physics Agent: "Validating thermal limits..."
  - Manufacturing Agent: "Checking weldability..."
  
[24:00:00] ✓ Training completed!
Final Loss: 1.234
Total examples processed: 2.4M
New knowledge: 342 items
Checkpoints saved: 24
```

---

## 🎯 Roadmap

- [x] KÁNU LLM architecture (1-3B)
- [x] KÁNU V2 multi-agents
- [x] World Model V2
- [x] Dashboard de base
- [ ] **Architecture unifiée** ← EN COURS
- [ ] **Intensive training system** ← EN COURS
- [ ] **Dashboard unifié complet** ← EN COURS
- [ ] Rust core integration
- [ ] Distributed training
- [ ] Cloud deployment
- [ ] Mobile app

---

## 📞 Support

**Documentation:** Ce fichier + READMEs individuels
**Issues:** GitHub Issues
**Email:** support@florynxlabs.com

---

**KÁNU - Your unified physics-bound engineering intelligence** 🚀⚛️

*Born from love. Bound by physics. Powered by integration.*
