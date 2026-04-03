"""
KÁNU Dashboard
Web interface for training, monitoring, and interacting with KÁNU LLM

Built with Gradio for simplicity and ease of use
"""
import gradio as gr
import torch
import json
import plotly.graph_objects as go
from pathlib import Path
import logging
from typing import List, Dict, Any
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from model.kanu_architecture import create_kanu_model, KANUConfig
from inference.kanu_inference import KANUInference, load_kanu_for_inference
from training.trainer import KANUTrainer, EngineeringDataset, create_engineering_dataset

logger = logging.getLogger(__name__)


class KANUDashboard:
    """
    Complete dashboard for KÁNU LLM
    """
    
    def __init__(self):
        self.model = None
        self.inference = None
        self.trainer = None
        self.conversation_history = []
        
        # Paths
        self.checkpoint_dir = Path("./checkpoints")
        self.dataset_dir = Path("./datasets")
        self.checkpoint_dir.mkdir(exist_ok=True)
        self.dataset_dir.mkdir(exist_ok=True)
        
        logger.info("KÁNU Dashboard initialized")
    
    def create_interface(self):
        """Create Gradio interface"""
        
        with gr.Blocks(title="KÁNU LLM - Florynx Labs", theme=gr.themes.Soft()) as demo:
            
            gr.Markdown("""
            # 🚀 KÁNU LLM - Physics-First Language Model
            ### Developed by Florynx Labs
            > *"Born from love. Bound by physics."*
            
            A bilingual (FR/EN) language model for engineering and scientific reasoning.
            Never hallucinates. Always obeys the laws of physics.
            """)
            
            with gr.Tabs():
                
                # ============================================================
                # TAB 1: Chat Interface
                # ============================================================
                with gr.Tab("💬 Chat with KÁNU"):
                    gr.Markdown("### Interact with KÁNU in French or English")
                    
                    with gr.Row():
                        with gr.Column(scale=2):
                            chatbot = gr.Chatbot(
                                label="Conversation",
                                height=500,
                                show_label=True
                            )
                            
                            with gr.Row():
                                msg_input = gr.Textbox(
                                    label="Your message",
                                    placeholder="Ask KÁNU anything about physics or engineering...",
                                    lines=3
                                )
                            
                            with gr.Row():
                                send_btn = gr.Button("Send", variant="primary")
                                clear_btn = gr.Button("Clear")
                            
                            language_choice = gr.Radio(
                                choices=["Auto", "English", "Français"],
                                value="Auto",
                                label="Language"
                            )
                        
                        with gr.Column(scale=1):
                            gr.Markdown("### Response Info")
                            physics_status = gr.Textbox(
                                label="Physics Validation",
                                value="✓ No violations",
                                interactive=False
                            )
                            warnings_box = gr.Textbox(
                                label="Warnings",
                                value="None",
                                interactive=False,
                                lines=5
                            )
                    
                    # Chat functions
                    def respond(message, history, language):
                        if not self.inference:
                            return history, "⚠️ Model not loaded", "Load a model first"
                        
                        # Convert language choice
                        lang_map = {"Auto": "auto", "English": "en", "Français": "fr"}
                        lang = lang_map[language]
                        
                        # Get response
                        result = self.inference.chat(message, self.conversation_history, lang)
                        
                        # Update history
                        history.append((message, result['response']))
                        self.conversation_history.append({'role': 'user', 'content': message})
                        self.conversation_history.append({'role': 'assistant', 'content': result['response']})
                        
                        # Physics status
                        if result['physics_validated']:
                            status = "✓ Physics validated"
                        else:
                            status = "⚠️ Physics warnings detected"
                        
                        # Warnings
                        warnings = "\n".join(result['warnings']) if result['warnings'] else "None"
                        
                        return history, status, warnings
                    
                    def clear_chat():
                        self.conversation_history = []
                        return [], "✓ No violations", "None"
                    
                    send_btn.click(
                        respond,
                        inputs=[msg_input, chatbot, language_choice],
                        outputs=[chatbot, physics_status, warnings_box]
                    )
                    
                    clear_btn.click(
                        clear_chat,
                        outputs=[chatbot, physics_status, warnings_box]
                    )
                
                # ============================================================
                # TAB 2: Step-by-Step Reasoning
                # ============================================================
                with gr.Tab("🧠 Step-by-Step Reasoning"):
                    gr.Markdown("### Solve engineering problems with detailed reasoning")
                    
                    with gr.Row():
                        with gr.Column():
                            problem_input = gr.Textbox(
                                label="Engineering Problem",
                                placeholder="e.g., Calculate the thrust of a rocket engine with 20 MPa chamber pressure...",
                                lines=5
                            )
                            
                            reasoning_lang = gr.Radio(
                                choices=["Auto", "English", "Français"],
                                value="Auto",
                                label="Language"
                            )
                            
                            solve_btn = gr.Button("Solve Step-by-Step", variant="primary")
                        
                        with gr.Column():
                            steps_output = gr.Textbox(
                                label="Reasoning Steps",
                                lines=15,
                                interactive=False
                            )
                            
                            final_answer = gr.Textbox(
                                label="Final Answer",
                                lines=3,
                                interactive=False
                            )
                            
                            reasoning_validation = gr.Textbox(
                                label="Physics Validation",
                                value="",
                                interactive=False
                            )
                    
                    def solve_problem(problem, language):
                        if not self.inference:
                            return "Load a model first", "", "⚠️ No model loaded"
                        
                        lang_map = {"Auto": "auto", "English": "en", "Français": "fr"}
                        lang = lang_map[language]
                        
                        result = self.inference.step_by_step_reasoning(problem, lang)
                        
                        # Format steps
                        steps_text = result['reasoning']
                        
                        # Validation
                        if result['physics_validated']:
                            validation = "✓ All physics checks passed"
                        else:
                            validation = "⚠️ Warnings:\n" + "\n".join(result['warnings'])
                        
                        return steps_text, result['final_answer'], validation
                    
                    solve_btn.click(
                        solve_problem,
                        inputs=[problem_input, reasoning_lang],
                        outputs=[steps_output, final_answer, reasoning_validation]
                    )
                
                # ============================================================
                # TAB 3: Model Management
                # ============================================================
                with gr.Tab("⚙️ Model Management"):
                    gr.Markdown("### Load and manage KÁNU models")
                    
                    with gr.Row():
                        with gr.Column():
                            model_size = gr.Radio(
                                choices=["1B", "2B", "3B"],
                                value="1B",
                                label="Model Size"
                            )
                            
                            checkpoint_path = gr.Textbox(
                                label="Checkpoint Path (optional)",
                                placeholder="./checkpoints/best_model.pt",
                                value=""
                            )
                            
                            device_choice = gr.Radio(
                                choices=["CUDA", "CPU"],
                                value="CUDA" if torch.cuda.is_available() else "CPU",
                                label="Device"
                            )
                            
                            load_model_btn = gr.Button("Load Model", variant="primary")
                            create_new_btn = gr.Button("Create New Model")
                        
                        with gr.Column():
                            model_info = gr.Textbox(
                                label="Model Information",
                                lines=10,
                                interactive=False
                            )
                    
                    def load_model(size, checkpoint, device):
                        try:
                            device_str = device.lower()
                            size_str = size.lower().replace('b', 'b')
                            
                            if checkpoint and Path(checkpoint).exists():
                                # Load from checkpoint
                                self.inference = load_kanu_for_inference(
                                    checkpoint,
                                    size_str,
                                    device_str
                                )
                                self.model = self.inference.model
                                
                                info = f"✓ Model loaded from checkpoint\n"
                                info += f"Size: {size}\n"
                                info += f"Parameters: {self.model.get_num_params()/1e9:.2f}B\n"
                                info += f"Device: {device}\n"
                                info += f"Checkpoint: {checkpoint}\n"
                            else:
                                # Create new model
                                self.model = create_kanu_model(size_str)
                                self.model.to(device_str)
                                
                                from transformers import AutoTokenizer
                                tokenizer = AutoTokenizer.from_pretrained("gpt2")
                                tokenizer.pad_token = tokenizer.eos_token
                                
                                self.inference = KANUInference(self.model, tokenizer, device_str)
                                
                                info = f"✓ New model created\n"
                                info += f"Size: {size}\n"
                                info += f"Parameters: {self.model.get_num_params()/1e9:.2f}B\n"
                                info += f"Device: {device}\n"
                                info += f"Status: Untrained (random weights)\n"
                            
                            return info
                        
                        except Exception as e:
                            return f"❌ Error: {str(e)}"
                    
                    load_model_btn.click(
                        load_model,
                        inputs=[model_size, checkpoint_path, device_choice],
                        outputs=[model_info]
                    )
                    
                    create_new_btn.click(
                        lambda size, device: load_model(size, "", device),
                        inputs=[model_size, device_choice],
                        outputs=[model_info]
                    )
                
                # ============================================================
                # TAB 4: Dataset Management
                # ============================================================
                with gr.Tab("📚 Dataset"):
                    gr.Markdown("### View and manage training dataset")
                    
                    with gr.Row():
                        with gr.Column():
                            create_dataset_btn = gr.Button("Create Initial Dataset", variant="primary")
                            load_dataset_btn = gr.Button("Load Dataset")
                            
                            dataset_path = gr.Textbox(
                                label="Dataset Path",
                                value="./datasets/engineering_dataset.json",
                                placeholder="./datasets/engineering_dataset.json"
                            )
                        
                        with gr.Column():
                            dataset_info = gr.Textbox(
                                label="Dataset Info",
                                lines=5,
                                interactive=False
                            )
                    
                    dataset_viewer = gr.Dataframe(
                        label="Dataset Examples",
                        headers=["Category", "Language", "Text Preview"],
                        interactive=False
                    )
                    
                    def create_dataset_action(path):
                        try:
                            dataset = create_engineering_dataset(path)
                            
                            info = f"✓ Dataset created\n"
                            info += f"Examples: {len(dataset)}\n"
                            info += f"Path: {path}\n"
                            
                            # Format for display
                            data = []
                            for item in dataset:
                                preview = item['text'][:100] + "..."
                                data.append([item['category'], item['language'], preview])
                            
                            return info, data
                        
                        except Exception as e:
                            return f"❌ Error: {str(e)}", []
                    
                    def load_dataset_action(path):
                        try:
                            with open(path, 'r', encoding='utf-8') as f:
                                dataset = json.load(f)
                            
                            info = f"✓ Dataset loaded\n"
                            info += f"Examples: {len(dataset)}\n"
                            info += f"Path: {path}\n"
                            
                            # Format for display
                            data = []
                            for item in dataset:
                                preview = item['text'][:100] + "..."
                                data.append([item['category'], item['language'], preview])
                            
                            return info, data
                        
                        except Exception as e:
                            return f"❌ Error: {str(e)}", []
                    
                    create_dataset_btn.click(
                        create_dataset_action,
                        inputs=[dataset_path],
                        outputs=[dataset_info, dataset_viewer]
                    )
                    
                    load_dataset_btn.click(
                        load_dataset_action,
                        inputs=[dataset_path],
                        outputs=[dataset_info, dataset_viewer]
                    )
                
                # ============================================================
                # TAB 5: Training
                # ============================================================
                with gr.Tab("🎓 Training"):
                    gr.Markdown("### Train KÁNU model")
                    
                    gr.Markdown("""
                    **Note:** Training a 1-3B parameter model requires significant compute resources.
                    For full training, use a GPU with at least 16GB VRAM.
                    """)
                    
                    with gr.Row():
                        with gr.Column():
                            train_dataset_path = gr.Textbox(
                                label="Training Dataset",
                                value="./datasets/engineering_dataset.json"
                            )
                            
                            train_epochs = gr.Slider(
                                minimum=1,
                                maximum=100,
                                value=10,
                                step=1,
                                label="Epochs"
                            )
                            
                            train_batch_size = gr.Slider(
                                minimum=1,
                                maximum=32,
                                value=4,
                                step=1,
                                label="Batch Size"
                            )
                            
                            train_lr = gr.Number(
                                value=3e-4,
                                label="Learning Rate"
                            )
                            
                            start_training_btn = gr.Button("Start Training", variant="primary")
                            stop_training_btn = gr.Button("Stop Training", variant="stop")
                        
                        with gr.Column():
                            training_status = gr.Textbox(
                                label="Training Status",
                                lines=10,
                                interactive=False
                            )
                            
                            training_plot = gr.Plot(label="Training Metrics")
                    
                    def start_training(dataset_path, epochs, batch_size, lr):
                        if not self.model:
                            return "❌ Load a model first", None
                        
                        try:
                            # This is a placeholder - actual training would run in background
                            status = f"⚠️ Training interface ready\n\n"
                            status += f"To train the model, use the training script:\n\n"
                            status += f"python train_kanu.py \\\n"
                            status += f"  --model_size 1b \\\n"
                            status += f"  --dataset {dataset_path} \\\n"
                            status += f"  --epochs {epochs} \\\n"
                            status += f"  --batch_size {batch_size} \\\n"
                            status += f"  --learning_rate {lr}\n\n"
                            status += f"Training in the dashboard is coming soon!"
                            
                            return status, None
                        
                        except Exception as e:
                            return f"❌ Error: {str(e)}", None
                    
                    start_training_btn.click(
                        start_training,
                        inputs=[train_dataset_path, train_epochs, train_batch_size, train_lr],
                        outputs=[training_status, training_plot]
                    )
                
                # ============================================================
                # TAB 6: About
                # ============================================================
                with gr.Tab("ℹ️ About"):
                    gr.Markdown("""
                    # KÁNU - Physics-First Language Model
                    
                    **Developed by:** Florynx Labs
                    
                    **Motto:** *"Born from love. Bound by physics."*
                    
                    ## What is KÁNU?
                    
                    KÁNU is a large language model (1-3 billion parameters) designed specifically for 
                    engineering and scientific reasoning. Unlike general-purpose LLMs, KÁNU:
                    
                    - ✅ **Never hallucinates** - All outputs are validated against physical laws
                    - ✅ **Bilingual** - Fluent in both French and English
                    - ✅ **Physics-bound** - Obeys the laws of thermodynamics, mechanics, and materials science
                    - ✅ **Step-by-step reasoning** - Shows its work, not just answers
                    - ✅ **Engineering-focused** - Trained on physics, materials, and engineering knowledge
                    
                    ## Architecture
                    
                    - **Model:** Transformer decoder (GPT-style)
                    - **Parameters:** 1B, 2B, or 3B
                    - **Context:** 2048 tokens
                    - **Embeddings:** Rotary Position Embeddings (RoPE)
                    - **Attention:** Multi-head self-attention
                    - **Activation:** GELU
                    
                    ## Training
                    
                    KÁNU is trained on a curated dataset of:
                    - Physics principles (mechanics, thermodynamics, fluid dynamics)
                    - Engineering knowledge (rocket engines, materials, structures)
                    - Problem-solving methodologies
                    - Anti-hallucination examples
                    
                    ## Use Cases
                    
                    - Engineering design assistance
                    - Physics problem solving
                    - Technical education
                    - Research support
                    - Design validation
                    
                    ## Version
                    
                    **Current Version:** 0.1.0 (Prototype)
                    
                    ## License
                    
                    MIT License - Florynx Labs
                    
                    ---
                    
                    *Built with PyTorch, Transformers, and Gradio*
                    """)
            
            return demo
    
    def launch(self, share: bool = False):
        """Launch the dashboard"""
        demo = self.create_interface()
        demo.launch(share=share, server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    dashboard = KANUDashboard()
    dashboard.launch(share=False)
