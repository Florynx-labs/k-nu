# 🚀 KÁNU Unified System

> **"Born from love. Bound by physics."**

## Vue d'Ensemble

KÁNU Unified intègre tous les composants du système KÁNU dans une architecture cohérente:

- **KÁNU LLM** (1-3B paramètres) - Compréhension langage naturel FR/EN
- **KÁNU V2** - Multi-agents + World Model pour design engineering
- **Intensive Training** - Entraînement adaptatif avec monitoring temps réel
- **Unified Dashboard** - Interface web complète

## Architecture

```
KÁNU Unified System
├── Unified Orchestrator (auto-routing intelligent)
│   ├── KÁNU LLM (chat, raisonnement)
│   ├── KÁNU V2 (design engineering complet)
│   └── World Model V2 (simulations physiques)
│
├── Resource Manager (adaptation CPU/GPU dynamique)
│
├── Intensive Trainer (entraînement adaptatif)
│   ├── Monitoring temps réel
│   ├── Enrichissement dataset automatique
│   ├── Capture pensées agents
│   └── Détection nouvelles connaissances
│
└── Unified Dashboard (interface web Gradio)
    ├── Chat Intelligent
    ├── Engineering Design
    ├── Intensive Training
    ├── System Monitor
    └── Configuration
```

## Installation

```bash
cd kanu_unified
pip install -r requirements.txt
```

## Démarrage Rapide

### 1. Lancer le Dashboard Unifié

```bash
python dashboard/unified_dashboard.py
```

Ouvrir http://localhost:7860

### 2. Charger le Système

Dans l'onglet "Configuration":
1. Choisir taille modèle (1B/2B/3B)
2. Sélectionner device (Auto/CUDA/CPU)
3. Activer V2 et World Model
4. Cliquer "Charger Système"

### 3. Utiliser le Chat

Dans l'onglet "Chat Intelligent":
- Mode Auto détecte automatiquement si chat simple ou design engineering
- Support bilingue FR/EN
- Validation physique automatique

### 4. Lancer Entraînement Intensif

Dans l'onglet "Entraînement Intensif":
1. Choisir durée (heures)
2. Sélectionner device
3. Configurer fréquence checkpoints
4. Activer adaptation dynamique
5. Cliquer "Démarrer Entraînement"

**Fonctionnalités:**
- ⚡ Adaptation automatique CPU/GPU selon charge système
- 📊 Monitoring temps réel (loss, ressources, tokens/s)
- 💭 Affichage pensées des agents
- 💡 Détection nouvelles connaissances
- 📚 Enrichissement automatique dataset
- 💾 Checkpointing intelligent

## Fonctionnalités Clés

### Auto-Routing Intelligent

```python
# Chat simple → KÁNU LLM
"What is Newton's second law?"
→ Routed to LLM

# Design engineering → KÁNU V2
"Design a 50 kN vacuum rocket engine"
→ Routed to V2 (workflow complet 10 étapes)
```

### Adaptation Dynamique Ressources

```
Charge système faible:
→ Utilise 95% GPU/CPU

Autre processus détecté:
→ Réduit à 60% GPU/CPU
→ Maintient qualité entraînement
→ Évite ralentissement système
```

### Monitoring Temps Réel

```
[00:15:30] Step 1530 | Loss: 2.456 | GPU: 95% | CPU: 45%
  💭 Physics Agent: Validating thermal limits...
  💭 Manufacturing Agent: Checking weldability...
  💡 New knowledge: Niobium C-103 melting point: 2750K
```

## Utilisation Programmatique

```python
from core.unified_orchestrator import create_unified_system

# Créer système unifié
system = create_unified_system(
    llm_size="1b",
    llm_checkpoint="./checkpoints/best_model.pt",
    device="cuda"
)

# Chat
result = system.process_request(
    "Design a high-efficiency vacuum engine",
    mode="auto"  # Auto-routing
)

print(result['response'])
print(f"Mode: {result['mode']}")  # "design"
print(f"Source: {result['source']}")  # "KÁNU V2"
```

## Configuration

Voir `KANU_UNIFIED_ARCHITECTURE.md` pour documentation complète de l'architecture.

## Performance

**Entraînement Intensif (1B sur RTX 3090):**
- Tokens/s: ~8,500 (95% GPU)
- Tokens/s: ~5,100 (60% GPU adaptatif)
- Adaptation: <1 seconde
- Overhead monitoring: <2%

**Inférence:**
- Chat simple: ~1-2s
- Design complet V2: ~30-60s (avec simulations)

## Roadmap

- [x] Architecture unifiée
- [x] Auto-routing LLM ↔ V2
- [x] Intensive training adaptatif
- [x] Dashboard complet
- [x] Monitoring temps réel
- [ ] Rust core integration
- [ ] Distributed training
- [ ] API REST
- [ ] Cloud deployment

---

**KÁNU Unified - L'intelligence d'ingénierie complète** 🚀⚛️

*Born from love. Bound by physics. Powered by integration.*
