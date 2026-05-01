"""
KÁNU Unified Dashboard
Interface complète intégrant LLM, V2, World Model, et Intensive Training

"Born from love. Bound by physics."
"""
import gradio as gr
import sys
from pathlib import Path
import logging
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import torch
from threading import Thread
import time
from datetime import datetime, timedelta
from typing import Optional

# Add paths
kanu_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(kanu_root / 'kanu_llm_prototype'))
sys.path.insert(0, str(kanu_root / 'kanu_v2'))
sys.path.insert(0, str(kanu_root / 'kanu_unified'))

from core.unified_orchestrator import create_unified_system, UnifiedOrchestrator
from core.resource_manager import ResourceManager
from training.intensive_trainer import IntensiveTrainer, TrainingMetrics
from model.kanu_architecture import create_kanu_model
from training.trainer import EngineeringDataset
from transformers import AutoTokenizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UnifiedDashboard:
    """
    Dashboard unifié complet pour KÁNU
    
    Onglets:
    1. Chat Intelligent (LLM + V2 auto-routing)
    2. Engineering Design (V2 workflow complet)
    3. Intensive Training (entraînement adaptatif)
    4. System Monitor (ressources et statut)
    5. Knowledge Base (dataset et connaissances)
    6. Configuration (paramètres système)
    """
    
    def __init__(self):
        self.orchestrator: Optional[UnifiedOrchestrator] = None
        self.resource_manager = ResourceManager()
        self.intensive_trainer: Optional[IntensiveTrainer] = None
        self.training_thread: Optional[Thread] = None
        
        # Training metrics queue
        self.training_metrics = []
        self.training_active = False
        self.thoughts_buffer = []
        
        logger.info("KÁNU Unified Dashboard initialized")
    
    def create_interface(self):
        """Crée l'interface Gradio complète"""
        
        with gr.Blocks(
            title="KÁNU Unified System - Florynx Labs",
            theme=gr.themes.Soft(),
            css="""
            .header { text-align: center; padding: 20px; }
            .status-box { border: 2px solid #4CAF50; border-radius: 10px; padding: 15px; }
            .warning-box { border: 2px solid #FF9800; border-radius: 10px; padding: 15px; }
            .error-box { border: 2px solid #F44336; border-radius: 10px; padding: 15px; }
            """
        ) as demo:
            
            gr.Markdown("""
            <div class="header">
            
            # 🚀 KÁNU - Unified Engineering Intelligence System
            ### Developed by Florynx Labs
            > *"Born from love. Bound by physics."*
            
            **Système complet intégrant:**
            - 🧠 KÁNU LLM (1-3B paramètres, FR/EN)
            - 🤖 KÁNU V2 (Multi-Agents + World Model)
            - 🔬 Physics Validation (Anti-hallucination)
            - 🎓 Intensive Adaptive Training
            
            </div>
            """)
            
            with gr.Tabs():
                
                # ============================================================
                # TAB 1: Chat Intelligent
                # ============================================================
                with gr.Tab("💬 Chat Intelligent"):
                    gr.Markdown("""
                    ### Chat avec KÁNU (Auto-routing LLM ↔ V2)
                    
                    Le système détecte automatiquement si votre demande nécessite:
                    - **Chat simple** → KÁNU LLM
                    - **Design engineering** → KÁNU V2 (workflow complet)
                    - **Simulations physiques** → World Model V2
                    """)
                    
                    with gr.Row():
                        with gr.Column(scale=2):
                            chatbot = gr.Chatbot(
                                label="Conversation",
                                height=600,
                                show_label=True
                            )
                            
                            with gr.Row():
                                msg_input = gr.Textbox(
                                    label="Votre message",
                                    placeholder="Posez une question ou demandez un design...",
                                    lines=3,
                                    scale=4
                                )
                            
                            with gr.Row():
                                send_btn = gr.Button("Envoyer", variant="primary", scale=1)
                                clear_btn = gr.Button("Effacer", scale=1)
                            
                            with gr.Row():
                                mode_choice = gr.Radio(
                                    choices=["Auto", "Chat", "Design"],
                                    value="Auto",
                                    label="Mode"
                                )
                                language_choice = gr.Radio(
                                    choices=["Auto", "English", "Français"],
                                    value="Auto",
                                    label="Langue"
                                )
                        
                        with gr.Column(scale=1):
                            gr.Markdown("### Informations")
                            
                            current_mode = gr.Textbox(
                                label="Mode actuel",
                                value="Chat",
                                interactive=False
                            )
                            
                            source_system = gr.Textbox(
                                label="Système utilisé",
                                value="KÁNU LLM",
                                interactive=False
                            )
                            
                            physics_status = gr.Textbox(
                                label="Validation Physique",
                                value="✓ Aucune violation",
                                interactive=False
                            )
                            
                            warnings_box = gr.Textbox(
                                label="Avertissements",
                                value="Aucun",
                                interactive=False,
                                lines=5
                            )
                            
                            workflow_status = gr.Textbox(
                                label="Statut Workflow (V2)",
                                value="N/A",
                                interactive=False,
                                lines=3
                            )
                    
                    def chat_respond(message, history, mode, language):
                        if not self.orchestrator:
                            return history, "Chat", "N/A", "⚠️ Système non chargé", "Chargez le système d'abord", "N/A"
                        
                        # Map choices
                        mode_map = {"Auto": "auto", "Chat": "chat", "Design": "design"}
                        mode_str = mode_map[mode]
                        
                        # Process request
                        result = self.orchestrator.process_request(message, mode_str)
                        
                        # Update history
                        history.append((message, result['response']))
                        
                        # Extract info
                        actual_mode = result.get('mode', 'chat').capitalize()
                        source = result.get('source', 'Unknown')
                        
                        # Physics validation
                        if result.get('physics_validated', True):
                            phys_status = "✓ Physique validée"
                        else:
                            phys_status = "⚠️ Avertissements détectés"
                        
                        # Warnings
                        warnings = result.get('warnings', [])
                        warnings_text = "\n".join(warnings) if warnings else "Aucun"
                        
                        # Workflow status
                        workflow = result.get('workflow_status', {})
                        if workflow:
                            wf_text = f"Étape: {workflow.get('current_step', 'N/A')}\n"
                            wf_text += f"Progrès: {workflow.get('progress_percent', 0):.0f}%"
                        else:
                            wf_text = "N/A"
                        
                        return history, actual_mode, source, phys_status, warnings_text, wf_text
                    
                    def clear_chat():
                        if self.orchestrator:
                            self.orchestrator.reset_session()
                        return [], "Chat", "N/A", "✓ Aucune violation", "Aucun", "N/A"
                    
                    send_btn.click(
                        chat_respond,
                        inputs=[msg_input, chatbot, mode_choice, language_choice],
                        outputs=[chatbot, current_mode, source_system, physics_status, warnings_box, workflow_status]
                    )
                    
                    clear_btn.click(
                        clear_chat,
                        outputs=[chatbot, current_mode, source_system, physics_status, warnings_box, workflow_status]
                    )
                
                # ============================================================
                # TAB 2: Intensive Training
                # ============================================================
                with gr.Tab("🎓 Entraînement Intensif"):
                    gr.Markdown("""
                    ### Entraînement Intensif Adaptatif
                    
                    **Fonctionnalités:**
                    - ⚡ Adaptation dynamique CPU/GPU selon charge système
                    - 📊 Monitoring temps réel avec métriques détaillées
                    - 💭 Capture des pensées des agents
                    - 💡 Détection automatique nouvelles connaissances
                    - 📚 Enrichissement automatique du dataset
                    - 💾 Checkpointing intelligent
                    """)
                    
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown("### Configuration")
                            
                            train_duration = gr.Slider(
                                minimum=0.1,
                                maximum=168,  # 1 week
                                value=24,
                                step=0.5,
                                label="Durée (heures)"
                            )
                            
                            train_device = gr.Radio(
                                choices=["Auto", "CUDA", "CPU"],
                                value="Auto",
                                label="Device"
                            )
                            
                            checkpoint_freq = gr.Radio(
                                choices=["30m", "1h", "2h", "4h"],
                                value="1h",
                                label="Fréquence Checkpoints"
                            )
                            
                            enable_adaptive = gr.Checkbox(
                                value=True,
                                label="Adaptation dynamique CPU/GPU"
                            )
                            
                            enable_enrichment = gr.Checkbox(
                                value=True,
                                label="Enrichissement automatique dataset"
                            )
                            
                            enable_agent_monitor = gr.Checkbox(
                                value=True,
                                label="Monitoring pensées agents"
                            )
                            
                            with gr.Row():
                                start_train_btn = gr.Button("🚀 Démarrer Entraînement", variant="primary")
                                stop_train_btn = gr.Button("⏹️ Arrêter", variant="stop")
                        
                        with gr.Column(scale=2):
                            gr.Markdown("### Statut Entraînement")
                            
                            training_status = gr.Textbox(
                                label="Statut",
                                value="Prêt à démarrer",
                                interactive=False,
                                lines=3
                            )
                            
                            progress_bar = gr.Slider(
                                minimum=0,
                                maximum=100,
                                value=0,
                                label="Progrès (%)",
                                interactive=False
                            )
                            
                            metrics_display = gr.Textbox(
                                label="Métriques en Temps Réel",
                                value="",
                                interactive=False,
                                lines=8
                            )
                            
                            agent_thoughts = gr.Textbox(
                                label="💭 Pensées des Agents",
                                value="",
                                interactive=False,
                                lines=4
                            )
                            
                            new_knowledge = gr.Textbox(
                                label="💡 Nouvelles Connaissances",
                                value="",
                                interactive=False,
                                lines=4
                            )
                    
                    with gr.Row():
                        with gr.Column():
                            loss_plot = gr.Plot(label="Loss Curve")
                        
                        with gr.Column():
                            resource_plot = gr.Plot(label="Utilisation Ressources")
                    
                    def start_training(duration, device, checkpoint_freq, adaptive, enrichment, agent_monitor):
                        if self.training_active:
                            return "⚠️ Entraînement déjà en cours", 0, "", "", "", None, None
                        
                        if not self.orchestrator:
                            return "⚠️ Chargez le système d'abord", 0, "", "", "", None, None
                        
                        # Map device
                        device_map = {"Auto": "auto", "CUDA": "cuda", "CPU": "cpu"}
                        device_str = device_map[device]
                        
                        if device_str == "auto":
                            device_str = "cuda" if torch.cuda.is_available() else "cpu"
                        
                        # Create dataset
                        try:
                            tokenizer = AutoTokenizer.from_pretrained("gpt2")
                            tokenizer.pad_token = tokenizer.eos_token
                            
                            dataset_path = kanu_root / "kanu_llm_prototype" / "datasets" / "engineering_dataset.json"
                            train_dataset = EngineeringDataset(str(dataset_path), tokenizer)
                            
                            # Create trainer
                            self.intensive_trainer = IntensiveTrainer(
                                model=self.orchestrator.llm.model,
                                train_dataset=train_dataset,
                                duration_hours=duration,
                                checkpoint_frequency=checkpoint_freq,
                                device=device_str,
                                enable_adaptive=adaptive,
                                enable_dataset_enrichment=enrichment,
                                enable_agent_monitoring=agent_monitor,
                                metrics_callback=self._on_training_metrics
                            )
                            
                            # Start training in thread
                            self.training_active = True
                            self.training_thread = Thread(target=self.intensive_trainer.train, daemon=True)
                            self.training_thread.start()
                            
                            status = f"✓ Entraînement démarré\n"
                            status += f"Durée: {duration}h\n"
                            status += f"Device: {device_str.upper()}\n"
                            status += f"Adaptatif: {'Oui' if adaptive else 'Non'}"
                            
                            return status, 0, "", "", "", None, None
                        
                        except Exception as e:
                            return f"❌ Erreur: {str(e)}", 0, "", "", "", None, None
                    
                    def stop_training():
                        if self.intensive_trainer:
                            self.intensive_trainer.stop()
                            self.training_active = False
                            return "⏹️ Entraînement arrêté"
                        return "Aucun entraînement en cours"
                    
                    def update_training_status():
                        """Update training status periodically"""
                        if not self.training_active or not self.intensive_trainer:
                            return "Prêt à démarrer", 0, "", "", "", None, None
                        
                        status_dict = self.intensive_trainer.get_status()
                        
                        if status_dict['status'] == 'not_training':
                            self.training_active = False
                            return "Entraînement terminé", 100, "", "", "", None, None
                        
                        # Format status
                        elapsed = timedelta(seconds=int(status_dict['elapsed_seconds']))
                        remaining = timedelta(seconds=int(status_dict['remaining_seconds']))
                        
                        status_text = f"🏃 En cours\n"
                        status_text += f"Temps écoulé: {elapsed}\n"
                        status_text += f"Temps restant: {remaining}\n"
                        status_text += f"Étape: {status_dict['global_step']}\n"
                        status_text += f"Epoch: {status_dict['current_epoch']}"
                        
                        progress = status_dict['progress_percent']
                        
                        # Latest metrics
                        metrics_text = ""
                        latest = status_dict.get('latest_metrics')
                        if latest:
                            metrics_text = f"Loss: {latest['loss']:.4f}\n"
                            metrics_text += f"LR: {latest['learning_rate']:.2e}\n"
                            metrics_text += f"GPU: {latest['gpu_usage_percent']:.0f}%\n"
                            metrics_text += f"CPU: {latest['cpu_usage_percent']:.0f}%\n"
                            metrics_text += f"Tokens/s: {latest['tokens_per_second']:.0f}\n"
                            metrics_text += f"Dataset: {latest['dataset_size']} (+{latest['new_examples_added']})"
                            
                        # Agent thoughts from live stream
                        new_thoughts = status_dict.get('thoughts', [])
                        if new_thoughts:
                            self.thoughts_buffer.extend(new_thoughts)
                            # Keep only last 20 thoughts for display
                            if len(self.thoughts_buffer) > 20:
                                self.thoughts_buffer = self.thoughts_buffer[-20:]
                        
                        thoughts_text = "\n".join(self.thoughts_buffer)
                        
                        # New knowledge
                        knowledge_text = ""
                        if latest and latest.get('new_knowledge'):
                            knowledge_text = "\n".join(latest['new_knowledge'])
                        
                        # Create plots
                        loss_fig = self._create_loss_plot()
                        resource_fig = self._create_resource_plot()
                        
                        return (
                            status_text,
                            progress,
                            metrics_text,
                            thoughts_text,
                            knowledge_text,
                            loss_fig,
                            resource_fig
                        )
                    
                    start_train_btn.click(
                        start_training,
                        inputs=[train_duration, train_device, checkpoint_freq, enable_adaptive, enable_enrichment, enable_agent_monitor],
                        outputs=[training_status, progress_bar, metrics_display, agent_thoughts, new_knowledge, loss_plot, resource_plot]
                    )
                    
                    stop_train_btn.click(
                        stop_training,
                        outputs=[training_status]
                    )
                    
                    # Auto-refresh training status (manual refresh for now)
                    # Note: Auto-refresh every N seconds removed in Gradio 6.0
                    # Users can manually refresh or we can implement with gr.Timer
                
                # ============================================================
                # TAB 3: System Monitor
                # ============================================================
                with gr.Tab("📊 Monitoring Système"):
                    gr.Markdown("### État du Système KÁNU")
                    
                    with gr.Row():
                        with gr.Column():
                            system_status = gr.Textbox(
                                label="Statut Système",
                                lines=10,
                                interactive=False
                            )
                        
                        with gr.Column():
                            resource_status = gr.Textbox(
                                label="Ressources",
                                lines=10,
                                interactive=False
                            )
                    
                    refresh_btn = gr.Button("🔄 Rafraîchir")
                    
                    def get_system_status():
                        if not self.orchestrator:
                            return "Système non chargé", "N/A"
                        
                        status = self.orchestrator.get_system_status()
                        
                        status_text = f"Système: {status['unified_system']}\n"
                        status_text += f"Mode: {status['current_mode']}\n\n"
                        
                        # Components
                        for comp_name, comp_status in status['components'].items():
                            status_text += f"{comp_name.upper()}:\n"
                            for key, value in comp_status.items():
                                status_text += f"  {key}: {value}\n"
                            status_text += "\n"
                        
                        # Resources
                        resource_report = self.resource_manager.get_usage_report()
                        
                        res_text = f"CPU: {resource_report['cpu']['usage_percent']:.1f}%\n"
                        res_text += f"RAM: {resource_report['ram']['usage_percent']:.1f}%\n\n"
                        
                        if resource_report['gpu']['available']:
                            for i, gpu in enumerate(resource_report['gpu']['devices']):
                                res_text += f"GPU {i}: {gpu['name']}\n"
                                res_text += f"  Utilization: {gpu['utilization_percent']:.1f}%\n"
                                res_text += f"  Memory: {gpu['memory_used_gb']:.1f}/{gpu['memory_total_gb']:.1f} GB\n"
                        else:
                            res_text += "GPU: Non disponible"
                        
                        return status_text, res_text
                    
                    refresh_btn.click(
                        get_system_status,
                        outputs=[system_status, resource_status]
                    )
                
                # ============================================================
                # TAB 4: Configuration
                # ============================================================
                with gr.Tab("⚙️ Configuration"):
                    gr.Markdown("### Chargement et Configuration du Système")
                    
                    with gr.Row():
                        with gr.Column():
                            model_size = gr.Radio(
                                choices=["1B", "2B", "3B"],
                                value="1B",
                                label="Taille Modèle LLM"
                            )
                            
                            checkpoint_path = gr.Textbox(
                                label="Checkpoint LLM (optionnel)",
                                placeholder="./checkpoints/best_model.pt",
                                value=""
                            )
                            
                            device_config = gr.Radio(
                                choices=["Auto", "CUDA", "CPU"],
                                value="Auto",
                                label="Device"
                            )
                            
                            enable_v2 = gr.Checkbox(
                                value=True,
                                label="Activer KÁNU V2 (Multi-Agents)"
                            )
                            
                            enable_world_model = gr.Checkbox(
                                value=True,
                                label="Activer World Model V2"
                            )
                            
                            load_btn = gr.Button("🚀 Charger Système", variant="primary")
                        
                        with gr.Column():
                            load_status = gr.Textbox(
                                label="Statut Chargement",
                                lines=15,
                                interactive=False
                            )
                    
                    def load_system(size, checkpoint, device, v2, world_model):
                        try:
                            size_str = size.lower().replace('b', 'b')
                            device_str = device.lower()
                            
                            if device_str == "auto":
                                device_str = "cuda" if torch.cuda.is_available() else "cpu"
                            
                            checkpoint_path_str = checkpoint if checkpoint and Path(checkpoint).exists() else None
                            
                            self.orchestrator = create_unified_system(
                                llm_size=size_str,
                                llm_checkpoint=checkpoint_path_str,
                                device=device_str
                            )
                            
                            status = "✓ Système KÁNU chargé avec succès!\n\n"
                            status += f"LLM: {size}\n"
                            status += f"Paramètres: {self.orchestrator.llm.model.get_num_params()/1e9:.2f}B\n"
                            status += f"Device: {device_str.upper()}\n"
                            status += f"V2: {'Activé' if v2 else 'Désactivé'}\n"
                            status += f"World Model: {'Activé' if world_model else 'Désactivé'}\n\n"
                            
                            if checkpoint_path_str:
                                status += f"Checkpoint: {checkpoint_path_str}\n"
                            else:
                                status += "Poids: Non entraînés (aléatoires)\n"
                            
                            return status
                        
                        except Exception as e:
                            return f"❌ Erreur: {str(e)}"
                    
                    load_btn.click(
                        load_system,
                        inputs=[model_size, checkpoint_path, device_config, enable_v2, enable_world_model],
                        outputs=[load_status]
                    )
            
            return demo
    
    def _on_training_metrics(self, metrics: TrainingMetrics):
        """Callback pour nouvelles métriques"""
        self.training_metrics.append(metrics)
        # Keep only last 1000
        if len(self.training_metrics) > 1000:
            self.training_metrics = self.training_metrics[-1000:]
    
    def _create_loss_plot(self):
        """Crée le graphique de loss"""
        if not self.training_metrics:
            return None
        
        steps = [m.step for m in self.training_metrics]
        losses = [m.loss for m in self.training_metrics]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=steps, y=losses, mode='lines', name='Loss'))
        fig.update_layout(
            title="Training Loss",
            xaxis_title="Step",
            yaxis_title="Loss",
            height=300
        )
        
        return fig
    
    def _create_resource_plot(self):
        """Crée le graphique d'utilisation ressources"""
        if not self.training_metrics:
            return None
        
        steps = [m.step for m in self.training_metrics]
        gpu_usage = [m.gpu_usage_percent for m in self.training_metrics]
        cpu_usage = [m.cpu_usage_percent for m in self.training_metrics]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=steps, y=gpu_usage, mode='lines', name='GPU %'))
        fig.add_trace(go.Scatter(x=steps, y=cpu_usage, mode='lines', name='CPU %'))
        fig.update_layout(
            title="Resource Usage",
            xaxis_title="Step",
            yaxis_title="Usage %",
            height=300
        )
        
        return fig
    
    def launch(self, share: bool = False):
        """Lance le dashboard"""
        demo = self.create_interface()
        demo.launch(
            share=share,
            server_name="0.0.0.0",
            server_port=7860,
            show_error=True
        )


if __name__ == "__main__":
    logger.info("="*60)
    logger.info("KÁNU Unified Dashboard")
    logger.info("Florynx Labs")
    logger.info('"Born from love. Bound by physics."')
    logger.info("="*60)
    
    dashboard = UnifiedDashboard()
    dashboard.launch(share=False)
