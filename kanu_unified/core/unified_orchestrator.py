"""
KÁNU Unified Orchestrator
Intègre KÁNU LLM, KÁNU V2, et World Model dans un système cohérent

"Born from love. Bound by physics."
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
import time

# Add paths
kanu_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(kanu_root / 'kanu_llm_prototype'))
sys.path.insert(0, str(kanu_root / 'kanu_v2'))
sys.path.insert(0, str(kanu_root / 'kanu_intelligence'))

# Import KÁNU LLM
from model.kanu_architecture import create_kanu_model
from inference.kanu_inference import KANUInference

# Import KÁNU V2
from kanu_v2_orchestrator import KANUV2

# Import World Model
from world_model.simulation_v2 import WorldModelV2

# Import Intelligence
try:
    from intelligence_orchestrator import KANUIntelligence
except ImportError:
    KANUIntelligence = None

logger = logging.getLogger(__name__)


class UnifiedOrchestrator:
    """
    Orchestrateur unifié pour tout le système KÁNU
    
    Intègre:
    - KÁNU LLM (1-3B paramètres) pour compréhension langage
    - KÁNU V2 (multi-agents) pour design engineering
    - World Model V2 pour simulations physiques
    - Intelligence Orchestrator pour coordination
    """
    
    def __init__(
        self,
        llm_model_size: str = "1b",
        llm_checkpoint: Optional[str] = None,
        device: str = "cuda",
        enable_v2: bool = True,
        enable_world_model: bool = True
    ):
        logger.info("="*60)
        logger.info("KÁNU Unified System - Initializing")
        logger.info("Born from love. Bound by physics.")
        logger.info("="*60)
        
        self.device = device
        self.enable_v2 = enable_v2
        self.enable_world_model = enable_world_model
        
        # Initialize KÁNU LLM
        logger.info(f"Loading KÁNU LLM ({llm_model_size})...")
        self.llm = self._init_llm(llm_model_size, llm_checkpoint, device)
        
        # Initialize KÁNU V2
        if enable_v2:
            logger.info("Loading KÁNU V2 (Multi-Agents)...")
            self.v2 = KANUV2()
        else:
            self.v2 = None
        
        # Initialize World Model
        if enable_world_model:
            logger.info("Loading World Model V2...")
            self.world_model = WorldModelV2()
        else:
            self.world_model = None
        
        # Initialize Intelligence Orchestrator
        if KANUIntelligence:
            logger.info("Loading Intelligence Orchestrator...")
            self.intelligence = KANUIntelligence()
        else:
            self.intelligence = None
        
        # Session state
        self.current_mode = "chat"  # chat, design, training
        self.conversation_history = []
        self.active_design_session = None
        
        logger.info("✓ KÁNU Unified System Ready")
        logger.info(f"  - LLM: {llm_model_size.upper()} ({self.llm.model.get_num_params()/1e9:.2f}B params)")
        logger.info(f"  - V2 Multi-Agents: {'Enabled' if enable_v2 else 'Disabled'}")
        logger.info(f"  - World Model: {'Enabled' if enable_world_model else 'Disabled'}")
        logger.info(f"  - Device: {device}")
    
    def _init_llm(self, model_size: str, checkpoint: Optional[str], device: str):
        """Initialize KÁNU LLM"""
        from transformers import AutoTokenizer
        import torch
        
        try:
            # Create model
            logger.info(f"  Creating model architecture: {model_size}")
            model = create_kanu_model(model_size)
            logger.info(f"  Model created successfully")
            
            # Load checkpoint if provided
            if checkpoint and Path(checkpoint).exists():
                logger.info(f"  Loading checkpoint: {checkpoint}")
                checkpoint_data = torch.load(checkpoint, map_location=device)
                model.load_state_dict(checkpoint_data['model_state_dict'])
                logger.info(f"  Checkpoint loaded successfully")
            else:
                logger.info("  Using untrained model (random weights)")
            
            # Load tokenizer
            logger.info("  Loading tokenizer...")
            tokenizer = AutoTokenizer.from_pretrained("gpt2")
            tokenizer.pad_token = tokenizer.eos_token
            logger.info("  Tokenizer loaded successfully")
            
            # Create inference engine
            logger.info(f"  Creating inference engine on {device}...")
            inference = KANUInference(model, tokenizer, device)
            logger.info("  Inference engine ready")
            
            return inference
            
        except Exception as e:
            logger.error(f"  Failed to initialize LLM: {e}", exc_info=True)
            raise RuntimeError(f"LLM initialization failed: {e}") from e
    
    def process_request(self, user_input: str, mode: str = "auto") -> Dict[str, Any]:
        """
        Point d'entrée principal - route intelligemment vers LLM ou V2
        
        Args:
            user_input: Message utilisateur
            mode: "auto", "chat", "design", "training"
        
        Returns:
            Response complète avec métadonnées
        """
        start_time = time.time()
        
        # Quick responses for simple greetings
        if self._is_simple_greeting(user_input):
            greetings_fr = [
                "Bonjour! Je suis KÁNU, votre assistant d'ingénierie. Comment puis-je vous aider aujourd'hui?",
                "Salut! Prêt à travailler sur des projets d'ingénierie passionnants?",
                "Bonjour! Que puis-je faire pour vous aujourd'hui? Design, calculs, ou questions techniques?"
            ]
            greetings_en = [
                "Hello! I'm KÁNU, your engineering intelligence assistant. How can I help you today?",
                "Hi! Ready to work on some exciting engineering projects?",
                "Hello! What can I do for you today? Design, calculations, or technical questions?"
            ]
            
            import random
            is_french = any(word in user_input.lower() for word in ['bonjour', 'salut', 'bonsoir', 'ça'])
            response = random.choice(greetings_fr if is_french else greetings_en)
            
            return {
                'response': response,
                'mode': 'chat',
                'source': 'KÁNU Quick Response',
                'physics_validated': True,
                'warnings': [],
                'elapsed_time': time.time() - start_time
            }
        
        # Auto-detect mode
        if mode == "auto":
            if self._is_design_request(user_input):
                mode = "design"
            else:
                mode = "chat"
        
        # Router vers le bon système
        if mode == "chat":
            result = self._handle_chat(user_input)
        elif mode == "design":
            result = self._handle_design(user_input)
        elif mode == "training":
            result = self._handle_training_request(user_input)
        else:
            result = {
                'response': "Mode non reconnu. Utilisez: chat, design, ou training",
                'mode': mode,
                'error': True
            }
        
        # Add metadata
        result['elapsed_time'] = time.time() - start_time
        result['mode'] = mode
        result['timestamp'] = time.time()
        
        return result
    
    def _is_design_request(self, text: str) -> bool:
        """Détecte si c'est une demande de design engineering"""
        design_keywords = [
            'design', 'concevoir', 'créer', 'développer',
            'engine', 'moteur', 'rocket', 'fusée',
            'optimize', 'optimiser', 'improve', 'améliorer',
            'calculate', 'calculer', 'simulate', 'simuler',
            'build', 'construire', 'make', 'fabriquer'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in design_keywords)
    
    def _detect_mode(self, user_input: str) -> str:
        """Détecte automatiquement le mode approprié"""
        input_lower = user_input.lower()
        
        # Keywords pour design engineering
        design_keywords = [
            'design', 'concevoir', 'build', 'construire', 'engineer',
            'rocket', 'engine', 'moteur', 'fusée', 'thrust', 'poussée',
            'chamber pressure', 'pression', 'nozzle', 'tuyère',
            'create a', 'développer', 'optimize', 'optimiser'
        ]
        
        # Keywords pour training
        training_keywords = [
            'train', 'entraîner', 'learn', 'apprendre', 'teach',
            'enseigner', 'improve', 'améliorer', 'fine-tune'
        ]
        
        # Check design
        if any(keyword in input_lower for keyword in design_keywords):
            return "design"
        
        # Check training
        if any(keyword in input_lower for keyword in training_keywords):
            return "training"
        
        # Default to chat
        return "chat"
    
    def _is_simple_greeting(self, text: str) -> bool:
        """Détecte les salutations simples"""
        greetings = [
            'bonjour', 'salut', 'hello', 'hi', 'hey',
            'bonsoir', 'good morning', 'good evening',
            'ça va', 'comment vas-tu', 'how are you'
        ]
        
        text_lower = text.lower().strip()
        return any(greeting in text_lower for greeting in greetings) and len(text.split()) < 10
    
    def _handle_chat(self, user_input: str) -> Dict[str, Any]:
        """Mode chat simple avec KÁNU LLM"""
        logger.info("Routing to KÁNU LLM (chat mode)")
        
        # Use LLM for chat
        result = self.llm.chat(
            user_input,
            self.conversation_history,
            language="auto"
        )
        
        # Update history
        self.conversation_history.append({
            'role': 'user',
            'content': user_input
        })
        self.conversation_history.append({
            'role': 'assistant',
            'content': result['response']
        })
        
        # Keep only last 10 turns
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        return {
            'response': result['response'],
            'physics_validated': result['physics_validated'],
            'warnings': result['warnings'],
            'language': result['language'],
            'source': 'KÁNU LLM'
        }
    
    def _handle_design(self, user_input: str) -> Dict[str, Any]:
        """Mode design engineering complet avec V2"""
        logger.info("Routing to KÁNU V2 (design mode)")
        
        if not self.v2:
            return {
                'response': "KÁNU V2 not enabled. Enable it in configuration.",
                'error': True
            }
        
        # Use V2 for complete engineering workflow
        v2_result = self.v2.chat(user_input)
        
        # Enhance with LLM explanation if needed
        if v2_result.get('workflow_step') in ['STEP_7_RANK_EXPLAIN', 'STEP_10_DELIVER_PACKAGE']:
            # Use LLM to make explanation more natural
            llm_enhancement = self.llm.generate(
                f"Explain this engineering result in clear terms:\n{v2_result['response']['message'][:500]}",
                max_new_tokens=200,
                temperature=0.5
            )
            v2_result['llm_enhancement'] = llm_enhancement
        
        return {
            'response': v2_result['response']['message'],
            'workflow_status': v2_result.get('workflow_status'),
            'physics_violations': v2_result.get('physics_violations_detected', 0),
            'designs_rejected': v2_result.get('designs_rejected', 0),
            'source': 'KÁNU V2',
            'llm_enhancement': v2_result.get('llm_enhancement')
        }
    
    def _handle_training_request(self, user_input: str) -> Dict[str, Any]:
        """Handle training-related requests"""
        return {
            'response': "Training mode - Use the Intensive Training dashboard tab to configure and start training.",
            'source': 'System',
            'action_required': 'open_training_tab'
        }
    
    def simulate_design(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate a design using World Model V2
        Accessible from both LLM and V2
        """
        if not self.world_model:
            return {
                'error': 'World Model not enabled',
                'success': False
            }
        
        logger.info("Running World Model V2 simulation...")
        
        # Run simulation
        result = self.world_model.run_simulation(design)
        
        # Use LLM to explain results
        explanation_prompt = f"""Explain these simulation results in clear terms:

Design: {design.get('name', 'Unnamed')}
Success: {result.success}
Performance: ISP {result.performance.get('isp_s', 0):.1f}s, Thrust {result.performance.get('thrust_kn', 0):.1f} kN
Failure modes: {len(result.failure_modes)}

Provide a brief, clear explanation."""
        
        explanation = self.llm.generate(
            explanation_prompt,
            max_new_tokens=200,
            temperature=0.5
        )
        
        return {
            'simulation_result': result,
            'explanation': explanation,
            'success': result.success
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get complete system status"""
        status = {
            'unified_system': 'operational',
            'current_mode': self.current_mode,
            'components': {}
        }
        
        # LLM status
        status['components']['llm'] = {
            'loaded': True,
            'parameters': self.llm.model.get_num_params(),
            'device': self.device
        }
        
        # V2 status
        if self.v2:
            status['components']['v2'] = self.v2.get_system_status()
        
        # World Model status
        if self.world_model:
            status['components']['world_model'] = {
                'loaded': True,
                'simulations_run': len(self.world_model.simulation_history)
            }
        
        # Conversation
        status['conversation'] = {
            'turns': len(self.conversation_history),
            'active_session': self.active_design_session is not None
        }
        
        return status
    
    def reset_session(self):
        """Reset current session"""
        self.conversation_history = []
        self.active_design_session = None
        self.current_mode = "chat"
        
        if self.v2:
            # Reset V2 workflow
            self.v2.workflow.reset()
        
        logger.info("Session reset")


def create_unified_system(
    llm_size: str = "1b",
    llm_checkpoint: Optional[str] = None,
    device: str = "auto"
) -> UnifiedOrchestrator:
    """
    Factory function to create unified KÁNU system
    
    Args:
        llm_size: "1b", "2b", or "3b"
        llm_checkpoint: Path to LLM checkpoint (optional)
        device: "cuda", "cpu", or "auto"
    
    Returns:
        UnifiedOrchestrator instance
    """
    import torch
    
    # Auto-detect device
    if device == "auto":
        if torch.cuda.is_available():
            device = "cuda"
        else:
            device = "cpu"
    
    # Create orchestrator
    orchestrator = UnifiedOrchestrator(
        llm_model_size=llm_size,
        llm_checkpoint=llm_checkpoint,
        device=device,
        enable_v2=True,
        enable_world_model=True
    )
    
    return orchestrator
