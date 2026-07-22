import math
import logging
from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, Any

import torch
import torch.nn as nn
import torch.nn.functional as F

from .mamba_block import KANUMambaConfig, MambaBlock, RMSNorm
from .attention_block import GQAAttentionConfig, SparseAttentionBlock
from .moe_layer import MoEConfig, MoEWithResidual
from .physics_head import PhysicsValidationHead, PhysicsLogitPenalty

logger = logging.getLogger(__name__)


@dataclass
class KANUHybridConfig:
    """Master configuration for KÁNU-Hybrid LLM."""
    vocab_size: int = 32768
    d_model: int = 2048
    
    # Architecture pattern: n_cycles * (n_mamba_per_cycle + 1 attention)
    n_cycles: int = 4
    n_mamba_per_cycle: int = 7
    
    # Mamba
    d_state: int = 16
    d_conv: int = 4
    expand: int = 2
    
    # Attention
    n_heads_q: int = 32
    n_kv_groups: int = 8
    max_seq_len: int = 4096
    use_rope: bool = True
    
    # MoE
    n_experts: int = 8
    top_k: int = 2
    d_ff_expert: int = 4096
    load_balance_coef: float = 0.01
    z_loss_coef: float = 0.0001
    
    # General
    dropout: float = 0.0
    rms_norm_eps: float = 1e-5
    
    @property
    def total_blocks(self):
        return self.n_cycles * (self.n_mamba_per_cycle + 1)
        
    def get_mamba_config(self) -> KANUMambaConfig:
        return KANUMambaConfig(
            d_model=self.d_model,
            d_state=self.d_state,
            d_conv=self.d_conv,
            expand=self.expand,
            dropout=self.dropout,
            rms_norm_eps=self.rms_norm_eps
        )
        
    def get_attention_config(self) -> GQAAttentionConfig:
        return GQAAttentionConfig(
            d_model=self.d_model,
            n_heads_q=self.n_heads_q,
            n_kv_groups=self.n_kv_groups,
            max_seq_len=self.max_seq_len,
            dropout=self.dropout,
            rms_norm_eps=self.rms_norm_eps,
            use_rope=self.use_rope
        )
        
    def get_moe_config(self) -> MoEConfig:
        return MoEConfig(
            d_model=self.d_model,
            d_ff_expert=self.d_ff_expert,
            n_experts=self.n_experts,
            top_k=self.top_k,
            dropout=self.dropout,
            rms_norm_eps=self.rms_norm_eps,
            load_balance_coef=self.load_balance_coef,
            z_loss_coef=self.z_loss_coef
        )

    @classmethod
    def kanu_8b(cls):
        """Standard ~8B config as specified."""
        return cls(
            d_model=2048,
            n_cycles=4,
            n_mamba_per_cycle=7,
            d_ff_expert=4096
        )

    @classmethod
    def kanu_tiny(cls):
        """Tiny config for fast testing."""
        return cls(
            vocab_size=1024,
            d_model=128,
            n_cycles=2,
            n_mamba_per_cycle=3,
            n_heads_q=4,
            n_kv_groups=2,
            max_seq_len=128,
            n_experts=4,
            d_ff_expert=256
        )


class HybridBlock(nn.Module):
    """A single layer containing (Mamba OR Attention) followed by MoE."""
    def __init__(self, config: KANUHybridConfig, is_attention: bool):
        super().__init__()
        self.is_attention = is_attention
        
        if is_attention:
            self.mixer = SparseAttentionBlock(config.get_attention_config())
        else:
            self.mixer = MambaBlock(config.get_mamba_config())
            
        self.moe = MoEWithResidual(config.get_moe_config())
        
    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        if self.is_attention:
            x = self.mixer(x, mask=mask)
        else:
            x = self.mixer(x) # Mamba is naturally causal, no mask needed
            
        x, aux_losses = self.moe(x)
        return x, aux_losses


class KANUHybridModel(nn.Module):
    """
    KÁNU-Hybrid LLM Architecture.
    Combines Mamba-1, GQA Sparse Attention, MoE and Physics Head.
    """
    def __init__(self, config: KANUHybridConfig):
        super().__init__()
        self.config = config
        
        self.embed_tokens = nn.Embedding(config.vocab_size, config.d_model)
        self.dropout = nn.Dropout(config.dropout)
        
        self.blocks = nn.ModuleList()
        for cycle in range(config.n_cycles):
            for _ in range(config.n_mamba_per_cycle):
                self.blocks.append(HybridBlock(config, is_attention=False))
            # 1 Attention block per cycle
            self.blocks.append(HybridBlock(config, is_attention=True))
            
        self.norm_f = RMSNorm(config.d_model, eps=config.rms_norm_eps)
        self.lm_head = nn.Linear(config.d_model, config.vocab_size, bias=False)
        
        # Tie weights
        self.lm_head.weight = self.embed_tokens.weight
        
        # Physics validation head
        self.physics_head = PhysicsValidationHead(d_model=config.d_model)
        self.physics_penalty = PhysicsLogitPenalty()
        
        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(
        self, 
        input_ids: torch.Tensor, 
        attention_mask: Optional[torch.Tensor] = None,
        physics_flags_target: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor, Dict[str, torch.Tensor]]:
        """
        Returns:
            lm_logits: (B, S, V)
            physics_logits: (B, S, 12)
            aux_losses: Dict with accumulated MoE losses
        """
        x = self.embed_tokens(input_ids)
        x = self.dropout(x)
        
        # Build causal mask for attention blocks
        causal_mask = None
        if attention_mask is not None:
            # We don't implement full padding mask logic here for simplicity, 
            # but SDPA expects either a boolean mask or causal flag.
            pass 
            
        total_balance_loss = 0.0
        total_z_loss = 0.0
        
        for block in self.blocks:
            x, aux_losses = block(x, mask=causal_mask)
            total_balance_loss += aux_losses.get("balance_loss", 0.0)
            total_z_loss += aux_losses.get("z_loss", 0.0)
            
        x = self.norm_f(x)
        
        lm_logits = self.lm_head(x)
        physics_logits = self.physics_head(x)
        
        losses = {
            "balance_loss": total_balance_loss / len(self.blocks),
            "z_loss": total_z_loss / len(self.blocks),
        }
        losses["total_aux_loss"] = (
            self.config.load_balance_coef * losses["balance_loss"] + 
            self.config.z_loss_coef * losses["z_loss"]
        )
        
        return lm_logits, physics_logits, losses

    def generate_with_physics(self, input_ids: torch.Tensor, max_new_tokens: int = 50, temperature: float = 0.8):
        """Basic autoregressive generation loop with hard physics constraint."""
        self.eval()
        with torch.no_grad():
            for _ in range(max_new_tokens):
                lm_logits, physics_logits, _ = self(input_ids)
                
                next_token_logits = lm_logits[:, -1, :]
                physics_probs = torch.sigmoid(physics_logits[:, -1, :])
                
                # Apply penalty
                next_token_logits = self.physics_penalty(
                    next_token_logits.unsqueeze(1), 
                    physics_probs.unsqueeze(1), 
                    threshold=0.5
                ).squeeze(1)
                
                next_token_logits = next_token_logits / temperature
                probs = F.softmax(next_token_logits, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1)
                
                input_ids = torch.cat([input_ids, next_token], dim=1)
                
        return input_ids

    def count_parameters(self) -> Dict[str, int]:
        total = sum(p.numel() for p in self.parameters())
        
        # Calculate active parameters per token approximately
        # Mamba or Attention + 2 Experts out of N
        active_embed = self.embed_tokens.weight.numel() + self.norm_f.weight.numel()
        
        # Average block active params
        # This is a rough estimation for the console.
        active = active_embed
        return {"total": total, "active_approx": active}


def _unit_test_kanu_hybrid():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    config = KANUHybridConfig.kanu_tiny()
    model = KANUHybridModel(config).to(device)
    
    input_ids = torch.randint(0, config.vocab_size, (2, 32), device=device)
    
    lm_logits, physics_logits, aux_losses = model(input_ids)
    
    assert lm_logits.shape == (2, 32, config.vocab_size)
    assert physics_logits.shape == (2, 32, 12)
    assert "total_aux_loss" in aux_losses
    
    loss = lm_logits.sum() + physics_logits.sum() + aux_losses["total_aux_loss"]
    loss.backward()
    
    print("KANUHybridModel test passed successfully.")


if __name__ == "__main__":
    _unit_test_kanu_hybrid()
