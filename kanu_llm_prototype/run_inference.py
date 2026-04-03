"""
Inference script for KÁNU LLM
Test the model with prompts
"""
import torch
import argparse
import logging
from transformers import AutoTokenizer

from model.kanu_architecture import create_kanu_model
from inference.kanu_inference import KANUInference

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Run KÁNU inference")
    
    parser.add_argument("--checkpoint", type=str, required=True,
                       help="Path to model checkpoint")
    parser.add_argument("--model_size", type=str, default="1b",
                       choices=["1b", "2b", "3b"],
                       help="Model size")
    parser.add_argument("--device", type=str, default="cuda",
                       help="Device (cuda or cpu)")
    parser.add_argument("--prompt", type=str, default=None,
                       help="Prompt to generate from")
    parser.add_argument("--interactive", action="store_true",
                       help="Interactive mode")
    parser.add_argument("--language", type=str, default="auto",
                       choices=["auto", "en", "fr"],
                       help="Language preference")
    parser.add_argument("--max_tokens", type=int, default=512,
                       help="Maximum tokens to generate")
    parser.add_argument("--temperature", type=float, default=0.7,
                       help="Sampling temperature")
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("KÁNU LLM Inference")
    logger.info('"Born from love. Bound by physics."')
    logger.info("="*60)
    
    # Load model
    logger.info(f"Loading KÁNU-{args.model_size.upper()} from {args.checkpoint}")
    
    model = create_kanu_model(args.model_size)
    checkpoint = torch.load(args.checkpoint, map_location=args.device)
    model.load_state_dict(checkpoint['model_state_dict'])
    
    tokenizer = AutoTokenizer.from_pretrained("gpt2")
    tokenizer.pad_token = tokenizer.eos_token
    
    inference = KANUInference(model, tokenizer, args.device)
    
    logger.info("Model loaded successfully")
    logger.info(f"Parameters: {model.get_num_params()/1e9:.2f}B")
    
    if args.interactive:
        # Interactive mode
        logger.info("\nInteractive mode - Type 'quit' to exit")
        logger.info("You can ask questions in English or French\n")
        
        conversation_history = []
        
        while True:
            try:
                user_input = input("\nYou: ")
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not user_input.strip():
                    continue
                
                # Get response
                result = inference.chat(
                    user_input,
                    conversation_history,
                    args.language
                )
                
                print(f"\nKÁNU: {result['response']}")
                
                if not result['physics_validated']:
                    print(f"\n⚠️ Physics warnings:")
                    for warning in result['warnings']:
                        print(f"  - {warning}")
                
                # Update history
                conversation_history.append({'role': 'user', 'content': user_input})
                conversation_history.append({'role': 'assistant', 'content': result['response']})
                
            except KeyboardInterrupt:
                break
        
        logger.info("\nGoodbye!")
    
    elif args.prompt:
        # Single prompt mode
        logger.info(f"\nPrompt: {args.prompt}\n")
        
        response = inference.generate(
            args.prompt,
            max_new_tokens=args.max_tokens,
            temperature=args.temperature,
            language=args.language
        )
        
        print(f"KÁNU: {response}")
    
    else:
        # Demo mode
        logger.info("\nRunning demo prompts...\n")
        
        demo_prompts = [
            ("What is Newton's second law?", "en"),
            ("Qu'est-ce que la thermodynamique?", "fr"),
            ("How does a rocket engine work?", "en"),
            ("Explain specific impulse", "en"),
        ]
        
        for prompt, lang in demo_prompts:
            print(f"\n{'='*60}")
            print(f"Prompt: {prompt}")
            print(f"{'='*60}")
            
            response = inference.generate(
                prompt,
                max_new_tokens=300,
                temperature=0.7,
                language=lang
            )
            
            print(f"\nKÁNU: {response}\n")


if __name__ == "__main__":
    main()
