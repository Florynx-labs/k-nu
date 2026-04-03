#!/usr/bin/env python3
"""
KÁNU CLI - Command Line Interface for KÁNU System
Manage training, models, inference, and system operations

Usage:
    kanu train --model 1b --duration 24h
    kanu inference --model 1b --checkpoint ./checkpoints/model.pt
    kanu dashboard --port 7860
    kanu status
"""
import argparse
import sys
import logging
from pathlib import Path
from typing import Optional
import json

# Add paths
kanu_root = Path(__file__).parent
sys.path.insert(0, str(kanu_root / 'kanu_llm_prototype'))
sys.path.insert(0, str(kanu_root / 'kanu_unified'))
sys.path.insert(0, str(kanu_root / 'kanu_v2'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_banner():
    """Print KÁNU banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   ██╗  ██╗ █████╗ ███╗   ██╗██╗   ██╗                   ║
    ║   ██║ ██╔╝██╔══██╗████╗  ██║██║   ██║                   ║
    ║   █████╔╝ ███████║██╔██╗ ██║██║   ██║                   ║
    ║   ██╔═██╗ ██╔══██║██║╚██╗██║██║   ██║                   ║
    ║   ██║  ██╗██║  ██║██║ ╚████║╚██████╔╝                   ║
    ║   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝                    ║
    ║                                                           ║
    ║   Physics-First Generative Engineering AI                ║
    ║   "Born from love. Bound by physics."                    ║
    ║   Developed by Florynx Labs                              ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def cmd_train(args):
    """Train KÁNU models"""
    print_banner()
    logger.info("="*60)
    logger.info("KÁNU TRAINING MODE")
    logger.info("="*60)
    
    if args.mode == "intensive":
        logger.info("Starting Intensive Adaptive Training...")
        from training.intensive_trainer import IntensiveTrainer
        from model.kanu_architecture import create_kanu_model
        from training.trainer import EngineeringDataset, create_engineering_dataset
        from transformers import AutoTokenizer
        import torch
        
        # Parse duration
        duration_hours = parse_duration(args.duration)
        
        # Create dataset if needed
        dataset_path = Path(args.dataset)
        if not dataset_path.exists():
            logger.info("Creating initial dataset...")
            create_engineering_dataset(str(dataset_path))
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained("gpt2")
        tokenizer.pad_token = tokenizer.eos_token
        
        # Load dataset
        train_dataset = EngineeringDataset(str(dataset_path), tokenizer, max_length=512)
        
        # Create model
        logger.info(f"Creating KÁNU-{args.model.upper()} model...")
        model = create_kanu_model(args.model)
        logger.info(f"Model parameters: {model.get_num_params()/1e9:.2f}B")
        
        # Load checkpoint if provided
        if args.checkpoint:
            logger.info(f"Loading checkpoint: {args.checkpoint}")
            checkpoint = torch.load(args.checkpoint, map_location='cpu')
            model.load_state_dict(checkpoint['model_state_dict'])
        
        # Create trainer
        trainer = IntensiveTrainer(
            model=model,
            train_dataset=train_dataset,
            duration_hours=duration_hours,
            checkpoint_frequency=args.checkpoint_freq,
            device=args.device,
            learning_rate=args.lr,
            batch_size=args.batch_size,
            gradient_accumulation=args.grad_accum,
            enable_adaptive=args.adaptive,
            enable_dataset_enrichment=args.enrich_dataset,
            save_dir=args.save_dir
        )
        
        # Start training
        trainer.train()
        
    else:
        logger.info("Starting Standard Training...")
        from model.kanu_architecture import create_kanu_model
        from training.trainer import KANUTrainer, EngineeringDataset, create_engineering_dataset
        from transformers import AutoTokenizer
        
        # Create dataset if needed
        dataset_path = Path(args.dataset)
        if not dataset_path.exists():
            logger.info("Creating initial dataset...")
            create_engineering_dataset(str(dataset_path))
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained("gpt2")
        tokenizer.pad_token = tokenizer.eos_token
        
        # Load dataset
        train_dataset = EngineeringDataset(str(dataset_path), tokenizer, max_length=512)
        
        # Create model
        logger.info(f"Creating KÁNU-{args.model.upper()} model...")
        model = create_kanu_model(args.model)
        logger.info(f"Model parameters: {model.get_num_params()/1e9:.2f}B")
        
        # Create trainer
        trainer = KANUTrainer(
            model=model,
            train_dataset=train_dataset,
            learning_rate=args.lr,
            batch_size=args.batch_size,
            gradient_accumulation_steps=args.grad_accum,
            max_epochs=args.epochs,
            save_dir=args.save_dir
        )
        
        # Start training
        trainer.train()


def cmd_inference(args):
    """Run inference with KÁNU"""
    print_banner()
    logger.info("="*60)
    logger.info("KÁNU INFERENCE MODE")
    logger.info("="*60)
    
    from model.kanu_architecture import create_kanu_model
    from inference.kanu_inference import KANUInference
    from transformers import AutoTokenizer
    import torch
    
    # Load model
    logger.info(f"Loading KÁNU-{args.model.upper()} model...")
    model = create_kanu_model(args.model)
    
    # Load checkpoint
    if args.checkpoint:
        logger.info(f"Loading checkpoint: {args.checkpoint}")
        checkpoint = torch.load(args.checkpoint, map_location=args.device)
        model.load_state_dict(checkpoint['model_state_dict'])
    else:
        logger.warning("No checkpoint provided - using untrained model")
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained("gpt2")
    tokenizer.pad_token = tokenizer.eos_token
    
    # Create inference engine
    inference = KANUInference(model, tokenizer, args.device)
    
    logger.info("Inference engine ready!")
    logger.info("Type your questions (or 'exit' to quit)")
    logger.info("-" * 60)
    
    # Interactive loop
    conversation_history = []
    while True:
        try:
            user_input = input("\n> ")
            if user_input.lower() in ['exit', 'quit', 'q']:
                break
            
            if not user_input.strip():
                continue
            
            # Generate response
            result = inference.chat(user_input, conversation_history)
            
            print(f"\nKÁNU: {result['response']}")
            
            if result.get('warnings'):
                print(f"\n⚠️  Warnings: {', '.join(result['warnings'])}")
            
            # Update history
            conversation_history.append({'role': 'user', 'content': user_input})
            conversation_history.append({'role': 'assistant', 'content': result['response']})
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break


def cmd_dashboard(args):
    """Launch KÁNU dashboard"""
    print_banner()
    logger.info("="*60)
    logger.info("KÁNU DASHBOARD")
    logger.info("="*60)
    
    import subprocess
    
    if args.type == "unified":
        dashboard_path = kanu_root / "kanu_unified" / "dashboard" / "unified_dashboard.py"
        logger.info(f"Launching Unified Dashboard on port {args.port}...")
    else:
        dashboard_path = kanu_root / "kanu_llm_prototype" / "dashboard" / "kanu_dashboard.py"
        logger.info(f"Launching LLM Dashboard on port {args.port}...")
    
    if not dashboard_path.exists():
        logger.error(f"Dashboard not found: {dashboard_path}")
        return
    
    # Launch dashboard
    subprocess.run([sys.executable, str(dashboard_path)])


def cmd_status(args):
    """Show KÁNU system status"""
    print_banner()
    logger.info("="*60)
    logger.info("KÁNU SYSTEM STATUS")
    logger.info("="*60)
    
    import torch
    
    # System info
    print("\n📊 System Information:")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  PyTorch: {torch.__version__}")
    print(f"  CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"  CUDA Version: {torch.version.cuda}")
        print(f"  GPU Count: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"    GPU {i}: {torch.cuda.get_device_name(i)}")
    
    # Check components
    print("\n🔧 Components:")
    components = {
        'KÁNU LLM': kanu_root / 'kanu_llm_prototype',
        'KÁNU V2': kanu_root / 'kanu_v2',
        'KÁNU Unified': kanu_root / 'kanu_unified',
        'Rust Core': kanu_root / 'rust_core'
    }
    
    for name, path in components.items():
        status = "✓ Installed" if path.exists() else "✗ Missing"
        print(f"  {name}: {status}")
    
    # Check checkpoints
    print("\n💾 Checkpoints:")
    checkpoint_dirs = [
        kanu_root / 'kanu_llm_prototype' / 'checkpoints',
        kanu_root / 'kanu_unified' / 'checkpoints'
    ]
    
    total_checkpoints = 0
    for cp_dir in checkpoint_dirs:
        if cp_dir.exists():
            checkpoints = list(cp_dir.glob('*.pt'))
            total_checkpoints += len(checkpoints)
            if checkpoints:
                print(f"  {cp_dir.name}: {len(checkpoints)} checkpoint(s)")
                for cp in checkpoints[:3]:
                    size_mb = cp.stat().st_size / (1024 * 1024)
                    print(f"    - {cp.name} ({size_mb:.1f} MB)")
    
    if total_checkpoints == 0:
        print("  No checkpoints found")
    
    # Check datasets
    print("\n📚 Datasets:")
    dataset_dirs = [
        kanu_root / 'kanu_llm_prototype' / 'datasets',
        kanu_root / 'data'
    ]
    
    for ds_dir in dataset_dirs:
        if ds_dir.exists():
            datasets = list(ds_dir.glob('*.json'))
            if datasets:
                print(f"  {ds_dir.name}: {len(datasets)} dataset(s)")


def cmd_list_models(args):
    """List available models"""
    print_banner()
    logger.info("="*60)
    logger.info("AVAILABLE MODELS")
    logger.info("="*60)
    
    print("\n🤖 Model Sizes:")
    models = {
        'tiny': {'params': '50M', 'layers': 6, 'hidden': 512},
        'small': {'params': '100M', 'layers': 12, 'hidden': 768},
        '1b': {'params': '1.0B', 'layers': 24, 'hidden': 2048},
        '2b': {'params': '2.0B', 'layers': 32, 'hidden': 2560},
        '3b': {'params': '3.0B', 'layers': 40, 'hidden': 2816}
    }
    
    for size, info in models.items():
        print(f"\n  KÁNU-{size.upper()}:")
        print(f"    Parameters: {info['params']}")
        print(f"    Layers: {info['layers']}")
        print(f"    Hidden Size: {info['hidden']}")
    
    print("\n💡 Usage:")
    print("  kanu train --model 1b --duration 24h")
    print("  kanu inference --model 1b --checkpoint ./checkpoints/model.pt")


def cmd_save_model(args):
    """Save model configuration"""
    print_banner()
    logger.info("Saving model configuration...")
    
    config = {
        'model_size': args.model,
        'checkpoint': args.checkpoint,
        'device': args.device,
        'timestamp': str(Path(args.checkpoint).stat().st_mtime) if Path(args.checkpoint).exists() else None
    }
    
    config_path = kanu_root / 'model_config.json'
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"✓ Model configuration saved to {config_path}")


def parse_duration(duration_str: str) -> float:
    """Parse duration string to hours"""
    duration_str = duration_str.lower()
    if 'h' in duration_str:
        return float(duration_str.replace('h', ''))
    elif 'm' in duration_str:
        return float(duration_str.replace('m', '')) / 60
    elif 'd' in duration_str:
        return float(duration_str.replace('d', '')) * 24
    else:
        return float(duration_str)


def main():
    parser = argparse.ArgumentParser(
        description="KÁNU CLI - Manage KÁNU AI System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Train a tiny 50M model for 2 minutes (quick test)
  kanu train --model tiny --duration 2m --mode intensive
  
  # Train a 1B model for 24 hours with intensive mode
  kanu train --model 1b --duration 24h --mode intensive
  
  # Train with standard mode for 10 epochs
  kanu train --model 1b --epochs 10
  
  # Run inference with a checkpoint
  kanu inference --model 1b --checkpoint ./checkpoints/model.pt
  
  # Launch unified dashboard
  kanu dashboard --type unified --port 7860
  
  # Check system status
  kanu status
  
  # List available models
  kanu list-models
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Train command
    train_parser = subparsers.add_parser('train', help='Train KÁNU models')
    train_parser.add_argument('--model', type=str, default='1b', 
                             choices=['tiny', 'small', '1b', '2b', '3b'],
                             help='Model size to train (tiny=50M, small=100M, 1b, 2b, 3b)')
    train_parser.add_argument('--mode', type=str, default='standard', choices=['standard', 'intensive'],
                             help='Training mode')
    train_parser.add_argument('--duration', type=str, default='24h',
                             help='Training duration (e.g., 24h, 48h, 7d) - for intensive mode')
    train_parser.add_argument('--epochs', type=int, default=10,
                             help='Number of epochs - for standard mode')
    train_parser.add_argument('--checkpoint', type=str, default=None,
                             help='Checkpoint to resume from')
    train_parser.add_argument('--checkpoint-freq', type=str, default='1h',
                             help='Checkpoint frequency (e.g., 30m, 1h, 2h)')
    train_parser.add_argument('--dataset', type=str, 
                             default='./kanu_llm_prototype/datasets/engineering_dataset.json',
                             help='Path to training dataset')
    train_parser.add_argument('--device', type=str, default='cuda',
                             help='Device to use (cuda or cpu)')
    train_parser.add_argument('--lr', type=float, default=3e-4,
                             help='Learning rate')
    train_parser.add_argument('--batch-size', type=int, default=1,
                             help='Batch size')
    train_parser.add_argument('--grad-accum', type=int, default=4,
                             help='Gradient accumulation steps')
    train_parser.add_argument('--adaptive', action='store_true', default=True,
                             help='Enable adaptive training')
    train_parser.add_argument('--enrich-dataset', action='store_true', default=True,
                             help='Enable dataset enrichment')
    train_parser.add_argument('--save-dir', type=str, default='./checkpoints',
                             help='Directory to save checkpoints')
    train_parser.set_defaults(func=cmd_train)
    
    # Inference command
    inference_parser = subparsers.add_parser('inference', help='Run inference')
    inference_parser.add_argument('--model', type=str, default='1b', 
                                 choices=['tiny', 'small', '1b', '2b', '3b'],
                                 help='Model size (tiny=50M, small=100M, 1b, 2b, 3b)')
    inference_parser.add_argument('--checkpoint', type=str, required=True,
                                 help='Path to model checkpoint')
    inference_parser.add_argument('--device', type=str, default='cuda',
                                 help='Device to use (cuda or cpu)')
    inference_parser.set_defaults(func=cmd_inference)
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser('dashboard', help='Launch dashboard')
    dashboard_parser.add_argument('--type', type=str, default='unified', choices=['unified', 'llm'],
                                  help='Dashboard type')
    dashboard_parser.add_argument('--port', type=int, default=7860,
                                  help='Port to run dashboard on')
    dashboard_parser.set_defaults(func=cmd_dashboard)
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')
    status_parser.set_defaults(func=cmd_status)
    
    # List models command
    list_parser = subparsers.add_parser('list-models', help='List available models')
    list_parser.set_defaults(func=cmd_list_models)
    
    # Save model command
    save_parser = subparsers.add_parser('save-model', help='Save model configuration')
    save_parser.add_argument('--model', type=str, required=True, 
                            choices=['tiny', 'small', '1b', '2b', '3b'],
                            help='Model size')
    save_parser.add_argument('--checkpoint', type=str, required=True,
                            help='Path to checkpoint')
    save_parser.add_argument('--device', type=str, default='cuda',
                            help='Device')
    save_parser.set_defaults(func=cmd_save_model)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    args.func(args)


if __name__ == "__main__":
    main()
