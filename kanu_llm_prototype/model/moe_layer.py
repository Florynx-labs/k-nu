import math
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any

import torch
import torch.nn as nn
import torch.nn.functional as F


EXPERT_REGISTRY = {
    0: "PHYSICS",
    1: "CHEMISTRY",
    2: "MATHEMATICS",
    3: "MATERIALS",
    4: "ELECTRICAL",
    5: "SYSTEMS",
    6: "FRENCH_ENG",
    7: "GENERALIST",
}

@dataclass
class MoEConfig:
    d_model: int = 2048
    d_ff_expert: int = 4096
    n_experts: int = 8
    top_k: int = 2
    dropout: float = 0.0
    rms_norm_eps: float = 1e-5
    
    # Switch Transformer / PaLM style load balancing
    load_balance_coef: float = 0.01
    z_loss_coef: float = 0.0001
    capacity_factor: float = 1.25


class RMSNorm(nn.Module):
    def __init__(self, d_model: int, eps: float = 1e-5):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(d_model))

    def forward(self, x):
        variance = x.pow(2).mean(-1, keepdim=True)
        x = x * torch.rsqrt(variance + self.eps)
        return self.weight * x


class ExpertSwiGLU(nn.Module):
    """Expert FFN with SwiGLU activation (Llama/Mistral style)."""
    def __init__(self, cfg: MoEConfig):
        super().__init__()
        self.w1 = nn.Linear(cfg.d_model, cfg.d_ff_expert, bias=False)
        self.w3 = nn.Linear(cfg.d_model, cfg.d_ff_expert, bias=False)
        self.w2 = nn.Linear(cfg.d_ff_expert, cfg.d_model, bias=False)
        self.dropout = nn.Dropout(cfg.dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # SwiGLU: w2( Swish(w1(x)) * w3(x) )
        x = F.silu(self.w1(x)) * self.w3(x)
        x = self.dropout(x)
        return self.w2(x)


class SparseMoELayer(nn.Module):
    """Mixture of Experts sparse top-k layer with Load Balancing and Z-loss."""
    def __init__(self, cfg: MoEConfig):
        super().__init__()
        self.cfg = cfg
        self.router = nn.Linear(cfg.d_model, cfg.n_experts, bias=False)
        self.experts = nn.ModuleList([ExpertSwiGLU(cfg) for _ in range(cfg.n_experts)])
        
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        bsz, seq_len, d_model = x.shape
        x_flat = x.view(-1, d_model)  # (N, D)
        N = x_flat.size(0)
        
        # Router logits
        logits = self.router(x_flat)  # (N, E)
        probs = F.softmax(logits, dim=-1)  # (N, E)
        
        # Top-k routing
        topk_probs, topk_indices = torch.topk(probs, k=self.cfg.top_k, dim=-1) # (N, K), (N, K)
        topk_probs = topk_probs / (topk_probs.sum(dim=-1, keepdim=True) + 1e-9) # Normalize probabilities
        
        # Output buffer
        out_flat = torch.zeros_like(x_flat)
        
        # We dispatch tokens cleanly:
        for e_id in range(self.cfg.n_experts):
            expert_layer = self.experts[e_id]
            # Find tokens assigned to this expert (can be in any of the K slots)
            idx_n, idx_k = torch.where(topk_indices == e_id)
            if idx_n.numel() == 0:
                continue
                
            tokens_e = x_flat[idx_n] # (Tokens_E, D)
            weights_e = topk_probs[idx_n, idx_k].unsqueeze(-1) # (Tokens_E, 1)
            
            out_e = expert_layer(tokens_e) # (Tokens_E, D)
            
            # Accumulate
            out_flat.index_add_(0, idx_n, out_e * weights_e)
            
        out = out_flat.view(bsz, seq_len, d_model)
        
        # ---------------- Auxiliary Losses ----------------
        
        # 1. Load balancing loss (Switch Transformer)
        # importance = sum of probabilities per expert
        # assignment = count of tokens per expert (top-1)
        top1_indices = topk_indices[:, 0]
        assignment = F.one_hot(top1_indices, num_classes=self.cfg.n_experts).float().mean(dim=0) # (E,)
        importance = probs.mean(dim=0) # (E,)
        balance_loss = self.cfg.n_experts * torch.sum(assignment * importance)
        
        # 2. Z-loss (PaLM / Llama-3 MoE style) to prevent router logits from exploding
        z_loss = torch.logsumexp(logits, dim=-1).pow(2).mean()
        
        total_aux_loss = (self.cfg.load_balance_coef * balance_loss) + (self.cfg.z_loss_coef * z_loss)
        
        losses = {
            "balance_loss": balance_loss,
            "z_loss": z_loss,
            "total_aux_loss": total_aux_loss
        }
        
        return out, losses


class MoEWithResidual(nn.Module):
    """MoE Layer with Pre-RMSNorm and Residual connection."""
    def __init__(self, cfg: MoEConfig):
        super().__init__()
        self.norm = RMSNorm(cfg.d_model, eps=cfg.rms_norm_eps)
        self.moe = SparseMoELayer(cfg)
        self.dropout = nn.Dropout(cfg.dropout)
        
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        residual = x
        x = self.norm(x)
        out, aux_losses = self.moe(x)
        out = self.dropout(out)
        return residual + out, aux_losses


def _unit_test_moe_layer():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    cfg = MoEConfig(d_model=32, d_ff_expert=64, n_experts=4, top_k=2)
    block = MoEWithResidual(cfg).to(device)

    x = torch.randn(2, 16, cfg.d_model, device=device, dtype=torch.float32)
    y, aux_losses = block(x)
    
    assert y.shape == x.shape, "Shape mismatch"
    assert "total_aux_loss" in aux_losses, "Missing aux loss"
    
    loss = y.sum() + aux_losses["total_aux_loss"]
    loss.backward()
    print("MoELayer test passed successfully.")


if __name__ == "__main__":
    _unit_test_moe_layer()

