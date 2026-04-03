"""
Training script for KÁNU LLM
Run this to train the model from scratch or fine-tune
"""
import torch
import argparse
import logging
from pathlib import Path
from transformers import AutoTokenizer

from model.kanu_architecture import create_kanu_model
from training.trainer import KANUTrainer, EngineeringDataset, create_engineering_dataset

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Train KÁNU LLM")
    
    # Model arguments
    parser.add_argument("--model_size", type=str, default="1b", choices=["1b", "2b", "3b"],
                       help="Model size (1b, 2b, or 3b parameters)")
    parser.add_argument("--checkpoint", type=str, default=None,
                       help="Path to checkpoint to resume from")
    
    # Data arguments
    parser.add_argument("--dataset", type=str, default="./datasets/engineering_dataset.json",
                       help="Path to training dataset")
    parser.add_argument("--val_dataset", type=str, default=None,
                       help="Path to validation dataset (optional)")
    parser.add_argument("--create_dataset", action="store_true",
                       help="Create initial dataset if it doesn't exist")
    
    # Training arguments
    parser.add_argument("--epochs", type=int, default=10,
                       help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=4,
                       help="Batch size per device")
    parser.add_argument("--gradient_accumulation", type=int, default=4,
                       help="Gradient accumulation steps")
    parser.add_argument("--learning_rate", type=float, default=3e-4,
                       help="Learning rate")
    parser.add_argument("--warmup_steps", type=int, default=1000,
                       help="Warmup steps")
    parser.add_argument("--max_grad_norm", type=float, default=1.0,
                       help="Max gradient norm for clipping")
    
    # System arguments
    parser.add_argument("--device", type=str, default="cuda",
                       help="Device to use (cuda or cpu)")
    parser.add_argument("--use_amp", action="store_true", default=True,
                       help="Use automatic mixed precision")
    parser.add_argument("--save_dir", type=str, default="./checkpoints",
                       help="Directory to save checkpoints")
    
    # Logging arguments
    parser.add_argument("--log_interval", type=int, default=100,
                       help="Log every N steps")
    parser.add_argument("--eval_interval", type=int, default=1000,
                       help="Evaluate every N steps")
    parser.add_argument("--save_interval", type=int, default=5000,
                       help="Save checkpoint every N steps")
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("KÁNU LLM Training")
    logger.info("Florynx Labs")
    logger.info('"Born from love. Bound by physics."')
    logger.info("="*60)
    
    # Create dataset if requested
    dataset_path = Path(args.dataset)
    if args.create_dataset or not dataset_path.exists():
        logger.info("Creating initial engineering dataset...")
        create_engineering_dataset(str(dataset_path))
    
    # Load tokenizer
    logger.info("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained("gpt2")
    tokenizer.pad_token = tokenizer.eos_token
    
    # Create datasets
    logger.info(f"Loading training dataset from {args.dataset}")
    train_dataset = EngineeringDataset(args.dataset, tokenizer, max_length=512)
    
    val_dataset = None
    if args.val_dataset:
        logger.info(f"Loading validation dataset from {args.val_dataset}")
        val_dataset = EngineeringDataset(args.val_dataset, tokenizer, max_length=512)
    
    # Create model
    logger.info(f"Creating KÁNU-{args.model_size.upper()} model...")
    model = create_kanu_model(args.model_size)
    
    logger.info(f"Model parameters: {model.get_num_params()/1e9:.2f}B")
    
    # Create trainer
    logger.info("Initializing trainer...")
    trainer = KANUTrainer(
        model=model,
        train_dataset=train_dataset,
        val_dataset=val_dataset,
        learning_rate=args.learning_rate,
        batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation,
        max_epochs=args.epochs,
        warmup_steps=args.warmup_steps,
        max_grad_norm=args.max_grad_norm,
        save_dir=args.save_dir,
        use_amp=args.use_amp,
        log_interval=args.log_interval,
        eval_interval=args.eval_interval,
        save_interval=args.save_interval
    )
    
    # Load checkpoint if provided
    if args.checkpoint:
        logger.info(f"Loading checkpoint from {args.checkpoint}")
        trainer.load_checkpoint(args.checkpoint)
    
    # Start training
    logger.info("Starting training...")
    logger.info(f"Device: {trainer.device}")
    logger.info(f"Effective batch size: {args.batch_size * args.gradient_accumulation}")
    logger.info(f"Total epochs: {args.epochs}")
    
    try:
        trainer.train()
        logger.info("Training completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("Training interrupted by user")
        trainer.save_checkpoint("interrupted.pt")
        logger.info("Checkpoint saved")
    
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
