import os
import json
import sentencepiece as spm
from typing import List

def train_tokenizer(
    corpus_files: List[str], 
    vocab_size: int = 32768, 
    model_prefix: str = "kanu_tokenizer",
    special_tokens_path: str = "special_tokens.json"
):
    """
    Trains a SentencePiece BPE tokenizer on a given corpus.
    Adds scientific and domain-specific special tokens.
    """
    print(f"Loading special tokens from {special_tokens_path}...")
    with open(special_tokens_path, "r", encoding="utf-8") as f:
        special_tokens_dict = json.load(f)
        
    all_special_tokens = [
        special_tokens_dict["bos_token"],
        special_tokens_dict["eos_token"],
        special_tokens_dict["pad_token"],
        special_tokens_dict["unk_token"]
    ] + special_tokens_dict["additional_special_tokens"]
    
    # We join user defined symbols by comma
    user_defined_symbols = ",".join(all_special_tokens)
    
    corpus_list = ",".join(corpus_files)
    
    print(f"Training SentencePiece tokenizer with {vocab_size} tokens...")
    spm.SentencePieceTrainer.train(
        input=corpus_list,
        model_prefix=model_prefix,
        vocab_size=vocab_size,
        model_type='bpe',
        character_coverage=0.9995,
        user_defined_symbols=user_defined_symbols,
        pad_id=3,
        unk_id=0,
        bos_id=1,
        eos_id=2,
        pad_piece="[PAD]",
        unk_piece="[UNK]",
        bos_piece="[BOS]",
        eos_piece="[EOS]",
        max_sentence_length=16384,
        shuffle_input_sentence=True,
    )
    
    print(f"Tokenizer trained and saved to {model_prefix}.model and {model_prefix}.vocab")

if __name__ == "__main__":
    # Create a dummy corpus file for unit testing if none exists
    dummy_corpus = "dummy_corpus.txt"
    if not os.path.exists(dummy_corpus):
        with open(dummy_corpus, "w", encoding="utf-8") as f:
            for i in range(100):
                f.write(f"This is a dummy sentence for testing the tokenizer. E = mc^2. {i}\n")
                f.write(f"The quick brown fox jumps over the lazy dog. F = m*a.\n")
                
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        special_tokens_path = os.path.join(current_dir, "special_tokens.json")
        train_tokenizer(
            corpus_files=[dummy_corpus],
            vocab_size=128, # Small for testing
            model_prefix="test_kanu_tokenizer",
            special_tokens_path=special_tokens_path
        )
        print("Train tokenizer test passed successfully.")
    finally:
        # Clean up
        if os.path.exists(dummy_corpus):
            os.remove(dummy_corpus)
        if os.path.exists("test_kanu_tokenizer.model"):
            os.remove("test_kanu_tokenizer.model")
        if os.path.exists("test_kanu_tokenizer.vocab"):
            os.remove("test_kanu_tokenizer.vocab")
