"""
KÁNU Local Dashboard - Flask Backend
100% Local, No External Dependencies, Fast & Lightweight

"Born from love. Bound by physics."
"""
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import sys
from pathlib import Path
import logging
import json
import torch
from threading import Thread, Lock
import time
from datetime import datetime
import queue

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

app = Flask(__name__)
CORS(app)  # Enable CORS for local development

# Global state
orchestrator = None
resource_manager = ResourceManager()
intensive_trainer = None
training_thread = None
training_active = False
training_metrics_queue = queue.Queue()
conversation_history = []
state_lock = Lock()

# Metrics storage
metrics_history = []
MAX_METRICS = 1000


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/api/system/status', methods=['GET'])
def get_system_status():
    """Get complete system status"""
    with state_lock:
        status = {
            'orchestrator_loaded': orchestrator is not None,
            'training_active': training_active,
            'conversation_turns': len(conversation_history),
            'metrics_count': len(metrics_history)
        }
        
        if orchestrator:
            status['orchestrator_status'] = orchestrator.get_system_status()
        
        # Resource usage
        status['resources'] = resource_manager.get_usage_report()
        
        return jsonify(status)


@app.route('/api/system/load', methods=['POST'])
def load_system():
    """Load KÁNU system"""
    global orchestrator
    
    data = request.json
    model_size = data.get('model_size', '1b')
    checkpoint = data.get('checkpoint', None)
    device = data.get('device', 'auto')
    
    try:
        with state_lock:
            logger.info(f"Loading KÁNU system: {model_size}, {device}")
            
            if device == 'auto':
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
            
            # Create orchestrator with better error handling
            try:
                orchestrator = create_unified_system(
                    llm_size=model_size,
                    llm_checkpoint=checkpoint if checkpoint else None,
                    device=device
                )
            except Exception as e:
                logger.error(f"Failed to create orchestrator: {e}", exc_info=True)
                raise
            
            # Get parameters safely
            try:
                num_params = orchestrator.llm.model.get_num_params()
                if num_params >= 1e9:
                    params_str = f"{num_params/1e9:.2f}B"
                else:
                    params_str = f"{num_params/1e6:.0f}M"
            except Exception as e:
                logger.warning(f"Could not get parameter count: {e}")
                params_str = "Unknown"
            
            return jsonify({
                'success': True,
                'message': f'KÁNU {model_size.upper()} loaded successfully',
                'device': device,
                'parameters': params_str
            })
    
    except Exception as e:
        logger.error(f"Error loading system: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat with KÁNU"""
    global conversation_history
    
    if not orchestrator:
        return jsonify({
            'success': False,
            'error': 'System not loaded. Please load the system first.'
        }), 400
    
    data = request.json
    message = data.get('message', '')
    mode = data.get('mode', 'auto')
    
    try:
        with state_lock:
            result = orchestrator.process_request(message, mode)
            
            conversation_history.append({
                'role': 'user',
                'content': message,
                'timestamp': time.time()
            })
            conversation_history.append({
                'role': 'assistant',
                'content': result['response'],
                'timestamp': time.time()
            })
            
            # Keep only last 50 turns
            if len(conversation_history) > 100:
                conversation_history = conversation_history[-100:]
            
            return jsonify({
                'success': True,
                'response': result['response'],
                'mode': result.get('mode', 'chat'),
                'source': result.get('source', 'KÁNU'),
                'physics_validated': result.get('physics_validated', True),
                'warnings': result.get('warnings', []),
                'elapsed_time': result.get('elapsed_time', 0)
            })
    
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    """Get conversation history"""
    with state_lock:
        return jsonify({
            'success': True,
            'history': conversation_history[-20:]  # Last 20 messages
        })


@app.route('/api/chat/clear', methods=['POST'])
def clear_chat():
    """Clear conversation history"""
    global conversation_history
    
    with state_lock:
        conversation_history = []
        if orchestrator:
            orchestrator.reset_session()
    
    return jsonify({'success': True})


@app.route('/api/training/start', methods=['POST'])
def start_training():
    """Start intensive training"""
    global intensive_trainer, training_thread, training_active
    
    if not orchestrator:
        return jsonify({
            'success': False,
            'error': 'System not loaded'
        }), 400
    
    if training_active:
        return jsonify({
            'success': False,
            'error': 'Training already active'
        }), 400
    
    data = request.json
    duration = data.get('duration', 1.0)
    device = data.get('device', 'auto')
    checkpoint_freq = data.get('checkpoint_freq', '1h')
    adaptive = data.get('adaptive', True)
    enrichment = data.get('enrichment', True)
    
    try:
        # Create dataset
        tokenizer = AutoTokenizer.from_pretrained("gpt2")
        tokenizer.pad_token = tokenizer.eos_token
        
        dataset_path = kanu_root / "kanu_llm_prototype" / "datasets" / "engineering_dataset.json"
        train_dataset = EngineeringDataset(str(dataset_path), tokenizer)
        
        # Create trainer with memory-optimized settings
        intensive_trainer = IntensiveTrainer(
            model=orchestrator.llm.model,
            train_dataset=train_dataset,
            duration_hours=duration,
            checkpoint_frequency=checkpoint_freq,
            device=device if device != 'auto' else ('cuda' if torch.cuda.is_available() else 'cpu'),
            batch_size=1,  # Small batch to avoid OOM
            gradient_accumulation=8,  # Compensate with more accumulation
            enable_adaptive=adaptive,
            enable_dataset_enrichment=enrichment,
            enable_agent_monitoring=False,  # Disabled to save memory
            metrics_callback=lambda m: training_metrics_queue.put(m)
        )
        
        # Start training thread
        training_active = True
        training_thread = Thread(target=_training_worker, daemon=True)
        training_thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Training started for {duration} hours'
        })
    
    except Exception as e:
        logger.error(f"Training start error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _training_worker():
    """Training worker thread"""
    global training_active
    
    try:
        intensive_trainer.train()
    except Exception as e:
        logger.error(f"Training error: {e}")
    finally:
        training_active = False


@app.route('/api/training/stop', methods=['POST'])
def stop_training():
    """Stop training"""
    global training_active
    
    if intensive_trainer:
        intensive_trainer.stop()
        training_active = False
        return jsonify({'success': True})
    
    return jsonify({
        'success': False,
        'error': 'No training active'
    }), 400


@app.route('/api/training/status', methods=['GET'])
def get_training_status():
    """Get training status"""
    if not training_active or not intensive_trainer:
        return jsonify({
            'success': True,
            'active': False
        })
    
    status = intensive_trainer.get_status()
    
    return jsonify({
        'success': True,
        'active': True,
        'status': status
    })


@app.route('/api/training/metrics', methods=['GET'])
def get_training_metrics():
    """Get training metrics"""
    global metrics_history
    
    # Drain queue
    while not training_metrics_queue.empty():
        try:
            metric = training_metrics_queue.get_nowait()
            metrics_history.append({
                'timestamp': metric.timestamp,
                'step': metric.step,
                'loss': metric.loss,
                'lr': metric.learning_rate,
                'gpu_usage': metric.gpu_usage_percent,
                'cpu_usage': metric.cpu_usage_percent,
                'tokens_per_sec': metric.tokens_per_second
            })
            
            # Keep only last MAX_METRICS
            if len(metrics_history) > MAX_METRICS:
                metrics_history = metrics_history[-MAX_METRICS:]
        except queue.Empty:
            break
    
    return jsonify({
        'success': True,
        'metrics': metrics_history[-100:]  # Last 100 points
    })


@app.route('/api/resources', methods=['GET'])
def get_resources():
    """Get resource usage"""
    report = resource_manager.get_usage_report()
    return jsonify({
        'success': True,
        'resources': report
    })


@app.route('/api/dataset/view', methods=['GET'])
def view_dataset():
    """View dataset"""
    try:
        dataset_path = kanu_root / "kanu_llm_prototype" / "datasets" / "engineering_dataset.json"
        
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        return jsonify({
            'success': True,
            'dataset': dataset[:50],  # First 50 examples
            'total': len(dataset)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/generate', methods=['POST'])
def generate():
    """Generate text with LLM"""
    if not orchestrator:
        return jsonify({
            'success': False,
            'error': 'System not loaded'
        }), 400
    
    data = request.json
    prompt = data.get('prompt', '')
    max_tokens = data.get('max_tokens', 200)
    temperature = data.get('temperature', 0.7)
    
    try:
        response = orchestrator.llm.generate(
            prompt,
            max_new_tokens=max_tokens,
            temperature=temperature
        )
        
        return jsonify({
            'success': True,
            'response': response
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/reasoning', methods=['POST'])
def step_by_step_reasoning():
    """Step-by-step reasoning"""
    if not orchestrator:
        return jsonify({
            'success': False,
            'error': 'System not loaded'
        }), 400
    
    data = request.json
    problem = data.get('problem', '')
    language = data.get('language', 'auto')
    
    try:
        result = orchestrator.llm.step_by_step_reasoning(problem, language)
        
        return jsonify({
            'success': True,
            'result': result
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    logger.info("="*60)
    logger.info("KÁNU Local Dashboard")
    logger.info("Florynx Labs")
    logger.info('"Born from love. Bound by physics."')
    logger.info("="*60)
    logger.info("Starting server on http://localhost:5000")
    logger.info("="*60)
    
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)
