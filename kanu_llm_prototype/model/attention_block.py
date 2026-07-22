import math
from dataclasses import dataclass
from typing import Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

@dataclass
class GQAAttentionConfig:
    """Configuration for Grouped Query Attention Block."""
    d_model: int = 2048
    n_heads_q: int = 32
    n_kv_groups: int = 8
    max_seq_len: int = 4096
    dropout: float = 0.0
    rms_norm_eps: float = 1e-5
    use_rope: bool = True
    
    def __post_init__(self):
        assert self.d_model % self.n_heads_q == 0, "d_model must be divisible by n_heads_q"
        assert self.n_heads_q % self.n_kv_groups == 0, "n_heads_q must be divisible by n_kv_groups"
        self.d_head = self.d_model // self.n_heads_q


class RMSNorm(nn.Module):
    def __init__(self, d_model: int, eps: float = 1e-5):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(d_model))

    def forward(self, x):
        variance = x.pow(2).mean(-1, keepdim=True)
        x = x * torch.rsqrt(variance + self.eps)
        return self.weight * x


class RotaryEmbedding(nn.Module):
    """Rotary Positional Embeddings (RoPE)."""
    def __init__(self, dim: int, max_seq_len: int = 4096, base: int = 10000):
        super().__init__()
        self.dim = dim
        self.max_seq_len = max_seq_len
        self.base = base
        
        inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer("inv_freq", inv_freq, persistent=False)
        self._set_cos_sin_cache(seq_len=max_seq_len, dtype=torch.float32, device=self.inv_freq.device)

    def _set_cos_sin_cache(self, seq_len: int, dtype: torch.dtype, device: torch.device):
        t = torch.arange(seq_len, device=device, dtype=self.inv_freq.dtype)
        freqs = torch.einsum("i,j->ij", t, self.inv_freq)
        emb = torch.cat((freqs, freqs), dim=-1)
        self.register_buffer("cos_cached", emb.cos()[None, None, :, :].to(dtype), persistent=False)
        self.register_buffer("sin_cached", emb.sin()[None, None, :, :].to(dtype), persistent=False)

    def forward(self, x: torch.Tensor, seq_len: int) -> Tuple[torch.Tensor, torch.Tensor]:
        if seq_len > self.max_seq_len:
            self._set_cos_sin_cache(seq_len, x.dtype, x.device)
        return (
            self.cos_cached[:, :, :seq_len, ...].to(x.dtype),
            self.sin_cached[:, :, :seq_len, ...].to(x.dtype),
        )


def apply_rotary_pos_emb(q: torch.Tensor, k: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
    """Applies RoPE to Q and K tensors."""
    def rotate_half(x):
        x1, x2 = x.chunk(2, dim=-1)
        return torch.cat((-x2, x1), dim=-1)
    
    q_embed = (q * cos) + (rotate_half(q) * sin)
    k_embed = (k * cos) + (rotate_half(k) * sin)
    return q_embed, k_embed


class GroupedQueryAttention(nn.Module):
    """GQA using PyTorch built-in SDPA (FlashAttention backend when available)."""
    def __init__(self, config: GQAAttentionConfig):
        super().__init__()
        self.config = config
        self.d_model = config.d_model
        self.n_heads_q = config.n_heads_q
        self.n_kv_groups = config.n_kv_groups
        self.d_head = config.d_head
        
        self.n_rep = self.n_heads_q // self.n_kv_groups
        
        self.q_proj = nn.Linear(self.d_model, self.n_heads_q * self.d_head, bias=False)
        self.k_proj = nn.Linear(self.d_model, self.n_kv_groups * self.d_head, bias=False)
        self.v_proj = nn.Linear(self.d_model, self.n_kv_groups * self.d_head, bias=False)
        self.o_proj = nn.Linear(self.n_heads_q * self.d_head, self.d_model, bias=False)
        
        if config.use_rope:
            self.rotary_emb = RotaryEmbedding(self.d_head, config.max_seq_len)
        else:
            self.rotary_emb = None

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        bsz, seq_len, _ = x.shape
        
        # Projections
        q = self.q_proj(x)
        k = self.k_proj(x)
        v = self.v_proj(x)
        
        # Reshape to (B, S, H, D)
        q = q.view(bsz, seq_len, self.n_heads_q, self.d_head).transpose(1, 2)
        k = k.view(bsz, seq_len, self.n_kv_groups, self.d_head).transpose(1, 2)
        v = v.view(bsz, seq_len, self.n_kv_groups, self.d_head).transpose(1, 2)
        
        # RoPE
        if self.rotary_emb is not None:
            cos, sin = self.rotary_emb(x, seq_len)
            q, k = apply_rotary_pos_emb(q, k, cos, sin)
            
        # GQA Repeat KV heads to match Q heads
        if self.n_rep > 1:
            k = k[:, :, None, :, :].expand(bsz, self.n_kv_groups, self.n_rep, seq_len, self.d_head)
            k = k.reshape(bsz, self.n_heads_q, seq_len, self.d_head)
            
            v = v[:, :, None, :, :].expand(bsz, self.n_kv_groups, self.n_rep, seq_len, self.d_head)
            v = v.reshape(bsz, self.n_heads_q, seq_len, self.d_head)
            
        # Scaled Dot-Product Attention (handles Causal Mask internally if is_causal=True)
        # We use is_causal=True by default for autoregressive training.
        attn_output = F.scaled_dot_product_attention(
            q, k, v, 
            attn_mask=mask, 
            dropout_p=self.config.dropout if self.training else 0.0,
            is_causal=(mask is None)
        )
        
        # Output projection
        attn_output = attn_output.transpose(1, 2).contiguous().view(bsz, seq_len, self.n_heads_q * self.d_head)
        return self.o_proj(attn_output)


class SparseAttentionBlock(nn.Module):
    """Attention Block (Pre-RMSNorm + GQA + Residual)."""
    def __init__(self, config: GQAAttentionConfig):
        super().__init__()
        self.config = config
        self.norm = RMSNorm(config.d_model, eps=config.rms_norm_eps)
        self.attn = GroupedQueryAttention(config)
        
    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        residual = x
        x = self.norm(x)
        x = self.attn(x, mask)
        return residual + x


def _unit_test_attention_block():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    cfg = GQAAttentionConfig(d_model=128, n_heads_q=4, n_kv_groups=2, max_seq_len=64)
    block = SparseAttentionBlock(cfg).to(device)

    x = torch.randn(2, 16, cfg.d_model, device=device, dtype=torch.float32)
    y = block(x)
    
    assert y.shape == x.shape, "Shape mismatch"
    
    loss = y.sum()
    loss.backward()
    print("AttentionBlock test passed successfully.")


if __name__ == "__main__":
    _unit_test_attention_block()
