<div align="center">
  <img src="kanu_logo.png" alt="KÁNU Logo" width="200"/>
  
  # 🚀 KÁNU - Unified Engineering Intelligence System

  > **"Born from love. Bound by physics."**  
  > Developed by Florynx Labs
</div>

KÁNU est un système d'intelligence d'ingénierie complet qui intègre:
- 🧠 **KÁNU LLM** - Modèle de langage 1-3B paramètres (FR/EN)
- 🤖 **KÁNU V2** - Système multi-agents avec World Model
- 🔬 **Physics Validation** - Anti-hallucination strict
- 🎓 **Intensive Training** - Entraînement adaptatif CPU/GPU
- 🌐 **Unified Dashboard** - Interface web complète

## 🎯 Core Principle

KÁNU ne génère JAMAIS d'idées irréalistes, sci-fi, ou physiquement impossibles.  
Tous les outputs obéissent strictement aux lois de la physique, contraintes d'ingénierie, et fabricabilité réelle.

---

## 🚀 Quick Start

### Option 1: CLI (Recommandé)

```bash
# Installation
pip install -r requirements.txt

# Lancer le dashboard
python kanu_cli.py dashboard --type unified --port 7860

# Entraîner un modèle (mode intensif 24h)
python kanu_cli.py train --model 1b --duration 24h --mode intensive

# Entraîner un modèle (mode standard)
python kanu_cli.py train --model 1b --epochs 10

# Inférence interactive
python kanu_cli.py inference --model 1b --checkpoint ./checkpoints/model.pt

# Voir le statut du système
python kanu_cli.py status

# Lister les modèles disponibles
python kanu_cli.py list-models
```

### Option 2: Dashboard Direct

```bash
cd kanu_unified
pip install -r requirements.txt
python dashboard/unified_dashboard.py
```

Ouvrir **http://localhost:7860**

### Utilisation

1. **Onglet Configuration** → Charger système (1B, Auto)
2. **Onglet Chat** → Conversation intelligente (auto-routing LLM ↔ V2)
3. **Onglet Entraînement** → Lancer session intensive adaptative

---

## 📁 Structure du Projet

```
kanu/
│
├── kanu_unified/              # 🆕 SYSTÈME UNIFIÉ (PRINCIPAL)
│   ├── core/
│   │   ├── unified_orchestrator.py    # Auto-routing intelligent
│   │   └── resource_manager.py        # Gestion ressources CPU/GPU
│   ├── training/
│   │   └── intensive_trainer.py       # Entraînement adaptatif
│   └── dashboard/
│       └── unified_dashboard.py       # Interface web complète
│
├── kanu_llm_prototype/        # Mini-LLM 1-3B paramètres
│   ├── model/                 # Architecture transformer
│   ├── training/              # Système d'entraînement
│   ├── inference/             # Moteur d'inférence
│   └── dashboard/             # Dashboard Gradio
│
├── kanu_v2/                   # Multi-agents + World Model
│   ├── agents/                # Agents spécialisés
│   ├── world_model/           # Simulations physiques
│   ├── workflow/              # Workflow 10 étapes
│   └── kanu_v2_orchestrator.py
│
├── kanu_intelligence/         # Intelligence orchestrator
│
├── rust_core/                 # Moteur Rust haute performance
│
└── KANU_UNIFIED_ARCHITECTURE.md  # Documentation complète
```

---

## ✨ Fonctionnalités Principales

### 1. Auto-Routing Intelligent
```python
"Qu'est-ce que la thermodynamique?"
→ KÁNU LLM (chat simple)

"Design a 50 kN vacuum engine"
→ KÁNU V2 (workflow engineering complet)
```

### 2. Entraînement Intensif Adaptatif
- ⚡ Adaptation dynamique CPU/GPU selon charge système
- 📊 Monitoring temps réel (loss, ressources, tokens/s)
- 💭 Capture pensées des agents
- 💡 Détection nouvelles connaissances
- 📚 Enrichissement automatique dataset

### 3. Dashboard Unifié Complet
- 💬 Chat Intelligent (auto-routing)
- 🎓 Entraînement Intensif (configuration complète)
- 📊 Monitoring Système (ressources temps réel)
- ⚙️ Configuration (chargement modèles)

---

## 📚 Documentation

- **[Architecture Unifiée](KANU_UNIFIED_ARCHITECTURE.md)** - Guide complet du système
- **[KÁNU Unified](kanu_unified/README.md)** - Système unifié
- **[KÁNU LLM](kanu_llm_prototype/README.md)** - Mini-LLM 1-3B
- **[KÁNU V2](kanu_v2/README.md)** - Multi-agents + World Model

---

## 🎯 Philosophie

**"Born from love. Bound by physics."**

### KÁNU va:
- ✅ Dire quand quelque chose est impossible
- ✅ Expliquer pourquoi c'est impossible
- ✅ Proposer alternatives réalistes
- ✅ Valider tout contre physique
- ✅ Livrer outputs engineering-ready

### KÁNU ne va JAMAIS:
- ❌ Générer concepts sci-fi
- ❌ Halluciner physique
- ❌ Inventer fausses données
- ❌ Sauter validations
- ❌ Compromettre sur physique

---

## 🔧 Développement

### CLI KÁNU

Le CLI unifié permet de gérer tous les aspects du système:

**Entraînement:**
```bash
# Mode intensif avec adaptation dynamique CPU/GPU
python kanu_cli.py train --model 1b --duration 24h --mode intensive

# Mode standard avec nombre d'époques
python kanu_cli.py train --model 2b --epochs 20 --batch-size 2

# Reprendre depuis un checkpoint
python kanu_cli.py train --model 1b --checkpoint ./checkpoints/model.pt --duration 12h
```

**Inférence:**
```bash
# Mode interactif
python kanu_cli.py inference --model 1b --checkpoint ./checkpoints/final.pt

# Spécifier le device
python kanu_cli.py inference --model 1b --checkpoint ./checkpoints/final.pt --device cpu
```

**Gestion:**
```bash
# Statut du système
python kanu_cli.py status

# Lister les modèles disponibles
python kanu_cli.py list-models

# Sauvegarder la configuration d'un modèle
python kanu_cli.py save-model --model 1b --checkpoint ./checkpoints/best.pt
```

### Méthode Traditionnelle

**Entraîner le LLM:**
```bash
cd kanu_llm_prototype
python train_kanu.py --model_size 1b --epochs 10
```

**Tester V2:**
```bash
cd kanu_v2
python -c "from kanu_v2_orchestrator import create_kanu_v2; kanu = create_kanu_v2(); print(kanu.get_system_status())"
```

---

## 📊 Performance

**Entraînement Intensif (1B sur RTX 3090):**
- Tokens/s: ~8,500 (95% GPU)
- Tokens/s: ~5,100 (60% GPU adaptatif)
- Adaptation: <1 seconde

**Inférence:**
- Chat simple: ~1-2s
- Design complet V2: ~30-60s

---

## 📄 License

MIT License - Florynx Labs

---

**KÁNU - Your unified physics-bound engineering intelligence** 🚀⚛️

*Born from love. Bound by physics. Powered by integration.*
