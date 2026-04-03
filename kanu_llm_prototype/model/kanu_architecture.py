"""
KÁNU LLM Architecture
Scalable transformer architecture for 1-3 billion parameters

This implementation supports both training from scratch and fine-tuning
from pre-trained models like GPT-Neo or MPT.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple
import math
import logging

logger = logging.getLogger(__name__)


class KANUConfig:
    """
    Configuration for KÁNU LLM
    Supports 1B to 3B parameter models
    """
    def __init__(
        self,
        vocab_size: int = 50257,  # GPT-2 tokenizer vocab size
        max_seq_len: int = 2048,
        d_model: int = 2048,  # Hidden dimension (2048 for ~1B params)
        num_layers: int = 24,  # Number of transformer layers
        num_heads: int = 16,   # Number of attention heads
        d_ff: int = 8192,      # Feed-forward dimension (4x d_model)
        dropout: float = 0.1,
        layer_norm_eps: float = 1e-5,
        use_flash_attention: bool = False,  # For efficiency
        use_rotary_embeddings: bool = True,  # RoPE for better position encoding
    ):
        self.vocab_size = vocab_size
        self.max_seq_len = max_seq_len
        self.d_model = d_model
        self.num_layers = num_layers
        self.num_heads = num_heads
        self.d_ff = d_ff
        self.dropout = dropout
        self.layer_norm_eps = layer_norm_eps
        self.use_flash_attention = use_flash_attention
        self.use_rotary_embeddings = use_rotary_embeddings
        
        # Calculate total parameters
        self.total_params = self._calculate_params()
        logger.info(f"KÁNU Config: {self.total_params/1e9:.2f}B parameters")
    
    def _calculate_params(self) -> int:
        """Calculate total number of parameters"""
        # Embeddings
        embed_params = self.vocab_size * self.d_model
        pos_params = self.max_seq_len * self.d_model
        
        # Each transformer layer
        # Attention: Q, K, V, O projections
        attn_params = 4 * (self.d_model * self.d_model)
        # Feed-forward: 2 linear layers
        ff_params = 2 * (self.d_model * self.d_ff)
        # Layer norms (2 per layer)
        ln_params = 2 * (2 * self.d_model)
        
        layer_params = attn_params + ff_params + ln_params
        total_layer_params = layer_params * self.num_layers
        
        # Output projection
        output_params = self.d_model * self.vocab_size
        
        total = embed_params + pos_params + total_layer_params + output_params
        return total
    
    @classmethod
    def kanu_1b(cls):
        """1 billion parameter configuration"""
        return cls(
            d_model=2048,
            num_layers=24,
            num_heads=16,
            d_ff=8192
        )
    
    @classmethod
    def kanu_2b(cls):
        """2 billion parameter configuration"""
        return cls(
            d_model=2560,
            num_layers=32,
            num_heads=20,
            d_ff=10240
        )
    
    @classmethod
    def kanu_tiny(cls):
        """Tiny model for testing (~50M parameters)"""
        return cls(
            d_model=512,
            num_layers=6,
            num_heads=8,
            d_ff=2048,
            max_seq_len=1024
        )
    
    @classmethod
    def kanu_small(cls):
        """Small model for testing (~100M parameters)"""
        return cls(
            d_model=768,
            num_layers=12,
            num_heads=12,
            d_ff=3072,
            max_seq_len=1024
        )
    
    @classmethod
    def kanu_3b(cls):
        """3 billion parameter configuration"""
        return cls(
            d_model=3072,
            num_layers=32,
            num_heads=24,
            d_ff=12288
        )


class RotaryPositionalEmbedding(nn.Module):
    """
    Rotary Position Embedding (RoPE)
    More efficient than learned positional embeddings
    """
    def __init__(self, dim: int, max_seq_len: int = 2048):
        super().__init__()
        self.dim = dim
        
        # Precompute frequencies
        inv_freq = 1.0 / (10000 ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer('inv_freq', inv_freq)
        
        # Precompute position indices
        t = torch.arange(max_seq_len).type_as(self.inv_freq)
        freqs = torch.einsum('i,j->ij', t, self.inv_freq)
        emb = torch.cat((freqs, freqs), dim=-1)
        self.register_buffer('cos_cached', emb.cos()[None, None, :, :])
        self.register_buffer('sin_cached', emb.sin()[None, None, :, :])
    
    def forward(self, x: torch.Tensor, seq_len: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """Return cos and sin for rotary embedding"""
        return (
            self.cos_cached[:, :, :seq_len, ...],
            self.sin_cached[:, :, :seq_len, ...]
        )


def rotate_half(x: torch.Tensor) -> torch.Tensor:
    """Rotate half the hidden dims of the input"""
    x1, x2 = x.chunk(2, dim=-1)
    return torch.cat((-x2, x1), dim=-1)


def apply_rotary_pos_emb(q: torch.Tensor, k: torch.Tensor, 
                        cos: torch.Tensor, sin: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
    """Apply rotary position embedding to queries and keys"""
    q_embed = (q * cos) + (rotate_half(q) * sin)
    k_embed = (k * cos) + (rotate_half(k) * sin)
    return q_embed, k_embed


class MultiHeadAttention(nn.Module):
    """
    Multi-head self-attention with optional rotary embeddings
    """
    def __init__(self, config: KANUConfig):
        super().__init__()
        self.num_heads = config.num_heads
        self.d_model = config.d_model
        self.d_k = config.d_model // config.num_heads
        
        assert config.d_model % config.num_heads == 0, "d_model must be divisible by num_heads"
        
        # Q, K, V projections
        self.q_proj = nn.Linear(config.d_model, config.d_model)
        self.k_proj = nn.Linear(config.d_model, config.d_model)
        self.v_proj = nn.Linear(config.d_model, config.d_model)
        
        # Output projection
        self.o_proj = nn.Linear(config.d_model, config.d_model)
        
        self.dropout = nn.Dropout(config.dropout)
        
        # Rotary embeddings
        if config.use_rotary_embeddings:
            self.rotary_emb = RotaryPositionalEmbedding(self.d_k, config.max_seq_len)
        else:
            self.rotary_emb = None
    
    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Args:
            x: (batch_size, seq_len, d_model)
            mask: (batch_size, 1, seq_len, seq_len) or None
        Returns:
            (batch_size, seq_len, d_model)
        """
        batch_size, seq_len, _ = x.shape
        
        # Project to Q, K, V
        q = self.q_proj(x)  # (batch, seq_len, d_model)
        k = self.k_proj(x)
        v = self.v_proj(x)
        
        # Reshape for multi-head attention
        q = q.view(batch_size, seq_len, self.num_heads, self.d_k).transpose(1, 2)
        k = k.view(batch_size, seq_len, self.num_heads, self.d_k).transpose(1, 2)
        v = v.view(batch_size, seq_len, self.num_heads, self.d_k).transpose(1, 2)
        # Now: (batch, num_heads, seq_len, d_k)
        
        # Apply rotary embeddings if enabled
        if self.rotary_emb is not None:
            cos, sin = self.rotary_emb(x, seq_len)
            q, k = apply_rotary_pos_emb(q, k, cos, sin)
        
        # Scaled dot-product attention
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.d_k)
        
        # Apply mask if provided (for causal attention)
        if mask is not None:
            scores = scores.masked_fill(mask == 0, float('-inf'))
        
        # Softmax and dropout
        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        # Apply attention to values
        attn_output = torch.matmul(attn_weights, v)  # (batch, num_heads, seq_len, d_k)
        
        # Reshape and project
        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.view(batch_size, seq_len, self.d_model)
        
        output = self.o_proj(attn_output)
        
        return output


class FeedForward(nn.Module):
    """
    Position-wise feed-forward network with GELU activation
    """
    def __init__(self, config: KANUConfig):
        super().__init__()
        self.fc1 = nn.Linear(config.d_model, config.d_ff)
        self.fc2 = nn.Linear(config.d_ff, config.d_model)
        self.dropout = nn.Dropout(config.dropout)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (batch_size, seq_len, d_model)
        Returns:
            (batch_size, seq_len, d_model)
        """
        x = self.fc1(x)
        x = F.gelu(x)  # GELU activation (better than ReLU for LLMs)
        x = self.dropout(x)
        x = self.fc2(x)
        return x


class TransformerBlock(nn.Module):
    """
    Single transformer decoder block with pre-layer normalization
    """
    def __init__(self, config: KANUConfig):
        super().__init__()
        
        # Pre-layer norm (more stable than post-layer norm)
        self.ln1 = nn.LayerNorm(config.d_model, eps=config.layer_norm_eps)
        self.attention = MultiHeadAttention(config)
        
        self.ln2 = nn.LayerNorm(config.d_model, eps=config.layer_norm_eps)
        self.feed_forward = FeedForward(config)
        
        self.dropout = nn.Dropout(config.dropout)
    
    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Args:
            x: (batch_size, seq_len, d_model)
            mask: Attention mask
        Returns:
            (batch_size, seq_len, d_model)
        """
        # Self-attention with residual connection
        residual = x
        x = self.ln1(x)
        x = self.attention(x, mask)
        x = self.dropout(x)
        x = residual + x
        
        # Feed-forward with residual connection
        residual = x
        x = self.ln2(x)
        x = self.feed_forward(x)
        x = self.dropout(x)
        x = residual + x
        
        return x


class KANU_LLM(nn.Module):
    """
    KÁNU Language Model
    
    "Born from love. Bound by physics."
    
    A transformer-based language model designed for engineering and scientific reasoning.
    Supports 1-3 billion parameters.
    """
    def __init__(self, config: KANUConfig):
        super().__init__()
        self.config = config
        
        logger.info(f"Initializing KÁNU LLM with {config.total_params/1e9:.2f}B parameters")
        
        # Token embeddings
        self.token_embeddings = nn.Embedding(config.vocab_size, config.d_model)
        
        # Positional embeddings (if not using rotary)
        if not config.use_rotary_embeddings:
            self.position_embeddings = nn.Embedding(config.max_seq_len, config.d_model)
        else:
            self.position_embeddings = None
        
        # Transformer blocks
        self.blocks = nn.ModuleList([
            TransformerBlock(config) for _ in range(config.num_layers)
        ])
        
        # Final layer norm
        self.ln_f = nn.LayerNorm(config.d_model, eps=config.layer_norm_eps)
        
        # Output projection to vocabulary
        self.lm_head = nn.Linear(config.d_model, config.vocab_size, bias=False)
        
        # Tie weights between input and output embeddings (common practice)
        self.lm_head.weight = self.token_embeddings.weight
        
        # Dropout
        self.dropout = nn.Dropout(config.dropout)
        
        # Initialize weights
        self.apply(self._init_weights)
        
        # Count parameters
        total_params = sum(p.numel() for p in self.parameters())
        logger.info(f"KÁNU LLM initialized: {total_params/1e9:.2f}B parameters")
    
    def _init_weights(self, module):
        """Initialize weights with small random values"""
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
        elif isinstance(module, nn.LayerNorm):
            torch.nn.init.ones_(module.weight)
            torch.nn.init.zeros_(module.bias)
    
    def forward(
        self, 
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        Forward pass
        
        Args:
            input_ids: (batch_size, seq_len) Token IDs
            attention_mask: (batch_size, seq_len) Attention mask (1 for real tokens, 0 for padding)
            labels: (batch_size, seq_len) Labels for language modeling loss
        
        Returns:
            logits: (batch_size, seq_len, vocab_size)
            loss: Scalar loss if labels provided, else None
        """
        batch_size, seq_len = input_ids.shape
        device = input_ids.device
        
        # Token embeddings
        x = self.token_embeddings(input_ids)  # (batch, seq_len, d_model)
        
        # Add positional embeddings if not using rotary
        if self.position_embeddings is not None:
            positions = torch.arange(0, seq_len, dtype=torch.long, device=device)
            positions = positions.unsqueeze(0).expand(batch_size, seq_len)
            x = x + self.position_embeddings(positions)
        
        x = self.dropout(x)
        
        # Create causal mask (lower triangular)
        causal_mask = torch.tril(torch.ones(seq_len, seq_len, device=device))
        causal_mask = causal_mask.view(1, 1, seq_len, seq_len)
        
        # Combine with attention mask if provided
        if attention_mask is not None:
            attention_mask = attention_mask.view(batch_size, 1, 1, seq_len)
            causal_mask = causal_mask * attention_mask
        
        # Pass through transformer blocks
        for block in self.blocks:
            x = block(x, causal_mask)
        
        # Final layer norm
        x = self.ln_f(x)
        
        # Project to vocabulary
        logits = self.lm_head(x)  # (batch, seq_len, vocab_size)
        
        # Calculate loss if labels provided
        loss = None
        if labels is not None:
            # Shift logits and labels for next-token prediction
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()
            
            # Flatten for cross-entropy
            loss = F.cross_entropy(
                shift_logits.view(-1, self.config.vocab_size),
                shift_labels.view(-1),
                ignore_index=-100  # Ignore padding tokens
            )
        
        return logits, loss
    
    def generate(
        self,
        input_ids: torch.Tensor,
        max_new_tokens: int = 100,
        temperature: float = 0.8,
        top_k: int = 50,
        top_p: float = 0.9,
        do_sample: bool = True
    ) -> torch.Tensor:
        """
        Generate text autoregressively
        
        Args:
            input_ids: (batch_size, seq_len) Starting tokens
            max_new_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (higher = more random)
            top_k: Keep only top k tokens
            top_p: Nucleus sampling threshold
            do_sample: Whether to sample or use greedy decoding
        
        Returns:
            (batch_size, seq_len + max_new_tokens) Generated tokens
        """
        self.eval()
        
        with torch.no_grad():
            for _ in range(max_new_tokens):
                # Get predictions for current sequence
                logits, _ = self.forward(input_ids)
                
                # Get logits for last token
                logits = logits[:, -1, :]  # (batch_size, vocab_size)
                
                # Apply temperature
                logits = logits / temperature
                
                if do_sample:
                    # Top-k filtering
                    if top_k > 0:
                        indices_to_remove = logits < torch.topk(logits, top_k)[0][..., -1, None]
                        logits[indices_to_remove] = float('-inf')
                    
                    # Top-p (nucleus) filtering
                    if top_p < 1.0:
                        sorted_logits, sorted_indices = torch.sort(logits, descending=True)
                        cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
                        
                        # Remove tokens with cumulative probability above threshold
                        sorted_indices_to_remove = cumulative_probs > top_p
                        sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                        sorted_indices_to_remove[..., 0] = 0
                        
                        indices_to_remove = sorted_indices_to_remove.scatter(1, sorted_indices, sorted_indices_to_remove)
                        logits[indices_to_remove] = float('-inf')
                    
                    # Sample from distribution
                    probs = F.softmax(logits, dim=-1)
                    next_token = torch.multinomial(probs, num_samples=1)
                else:
                    # Greedy decoding
                    next_token = torch.argmax(logits, dim=-1, keepdim=True)
                
                # Append to sequence
                input_ids = torch.cat([input_ids, next_token], dim=1)
                
                # Stop if max length reached
                if input_ids.shape[1] >= self.config.max_seq_len:
                    break
        
        return input_ids
    
    def get_num_params(self) -> int:
        """Get total number of parameters"""
        return sum(p.numel() for p in self.parameters())


def create_kanu_model(size: str = "1b") -> KANU_LLM:
    """
    Factory function to create KÁNU model
    
    Args:
        size: "tiny", "small", "1b", "2b", or "3b"
    
    Returns:
        KANU_LLM instance
    """
    if size == "tiny":
        config = KANUConfig.kanu_tiny()
    elif size == "small":
        config = KANUConfig.kanu_small()
    elif size == "1b":
        config = KANUConfig.kanu_1b()
    elif size == "2b":
        config = KANUConfig.kanu_2b()
    elif size == "3b":
        config = KANUConfig.kanu_3b()
    else:
        raise ValueError(f"Unknown size: {size}. Choose from 'tiny', 'small', '1b', '2b', '3b'")
    
    model = KANU_LLM(config)
    
    logger.info(f"Created KÁNU-{size.upper()} model")
    logger.info(f"Total parameters: {model.get_num_params()/1e9:.2f}B")
    
    return model
