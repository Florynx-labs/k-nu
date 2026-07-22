import math
from dataclasses import dataclass
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F

@dataclass
class KANUMambaConfig:
    """Configuration for a KÁNU Mamba-1 block."""
    d_model: int = 2048
    d_state: int = 16
    d_conv: int = 4
    expand: int = 2
    dropout: float = 0.0
    rms_norm_eps: float = 1e-5
    dt_rank: str = "auto"
    d_inner: int = 0

    def __post_init__(self):
        self.d_inner = int(self.expand * self.d_model)
        if self.dt_rank == "auto":
            self.dt_rank = math.ceil(self.d_model / 16)


class RMSNorm(nn.Module):
    def __init__(self, d_model: int, eps: float = 1e-5):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(d_model))

    def forward(self, x):
        variance = x.pow(2).mean(-1, keepdim=True)
        x = x * torch.rsqrt(variance + self.eps)
        return self.weight * x


class _FallbackMambaSSM(nn.Module):
    """Fallback PyTorch SSM implementation for environments without mamba-ssm."""
    def __init__(self, config: KANUMambaConfig):
        super().__init__()
        self.config = config
        self.d_model = config.d_model
        self.d_inner = config.d_inner
        self.d_state = config.d_state
        self.dt_rank = config.dt_rank

        self.in_proj = nn.Linear(self.d_model, self.d_inner * 2, bias=False)
        self.conv1d = nn.Conv1d(
            in_channels=self.d_inner,
            out_channels=self.d_inner,
            bias=True,
            kernel_size=config.d_conv,
            groups=self.d_inner,
            padding=config.d_conv - 1,
        )
        self.activation = nn.SiLU()

        # SSM parameters
        self.x_proj = nn.Linear(self.d_inner, self.dt_rank + self.d_state * 2, bias=False)
        self.dt_proj = nn.Linear(self.dt_rank, self.d_inner, bias=True)
        
        A = torch.arange(1, self.d_state + 1, dtype=torch.float32).repeat(self.d_inner, 1)
        self.A_log = nn.Parameter(torch.log(A))
        self.D = nn.Parameter(torch.ones(self.d_inner))

        self.out_proj = nn.Linear(self.d_inner, self.d_model, bias=False)
        self.dropout = nn.Dropout(config.dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, seq_len, d_model = x.shape
        
        xz = self.in_proj(x)
        x_proj, z = xz.chunk(2, dim=-1)

        x_proj = x_proj.transpose(1, 2)
        x_proj = self.conv1d(x_proj)[:, :, :seq_len]
        x_proj = x_proj.transpose(1, 2)
        x_proj = self.activation(x_proj)

        x_dbl = self.x_proj(x_proj)
        dt, B, C = torch.split(x_dbl, [self.dt_rank, self.d_state, self.d_state], dim=-1)
        dt = F.softplus(self.dt_proj(dt))

        A = -torch.exp(self.A_log.float())
        
        # Discretize A and B
        dA = torch.exp(torch.einsum("b l d, d n -> b l d n", dt, A))
        dB = torch.einsum("b l d, b l n -> b l d n", dt, B)
        
        # Sequential scan (fallback)
        h = torch.zeros(b, self.d_inner, self.d_state, device=x.device, dtype=x.dtype)
        y = []
        for i in range(seq_len):
            h = dA[:, i] * h + dB[:, i] * x_proj[:, i].unsqueeze(-1)
            y.append(torch.einsum("b d n, b n -> b d", h, C[:, i]))
            
        y = torch.stack(y, dim=1)
        y = y + x_proj * self.D
        
        y = y * self.activation(z)
        out = self.out_proj(y)
        return self.dropout(out)


class MambaBlock(nn.Module):
    """KÁNU-Hybrid Mamba Block (with RMSNorm and Residual)."""
    def __init__(self, config: KANUMambaConfig):
        super().__init__()
        self.config = config
        self.norm = RMSNorm(config.d_model, eps=config.rms_norm_eps)

        self._use_official = False
        try:
            import mamba_ssm
            from mamba_ssm.modules.mamba_simple import Mamba
            self.mixer = Mamba(
                d_model=config.d_model,
                d_state=config.d_state,
                d_conv=config.d_conv,
                expand=config.expand,
            )
            self._use_official = True
        except ImportError:
            self.mixer = _FallbackMambaSSM(config)
            self._use_official = False

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass for Mamba Block.
        Args:
            x: (B, S, D) input tensor
        Returns:
            (B, S, D) output tensor
        """
        residual = x
        x = self.norm(x)
        x = self.mixer(x)
        return residual + x


def _shape_assert(x: torch.Tensor, expected_last_dim: int):
    if x.dim() != 3:
        raise AssertionError(f"Expected 3D tensor (B,S,D), got shape={tuple(x.shape)}")
    if x.size(-1) != expected_last_dim:
        raise AssertionError(f"Expected last dim {expected_last_dim}, got {x.size(-1)}")


def _unit_test_mamba_block():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    cfg = KANUMambaConfig(d_model=32, d_state=8, d_conv=3, expand=2, dropout=0.0)
    block = MambaBlock(cfg).to(device)

    x = torch.randn(2, 16, cfg.d_model, device=device, dtype=torch.float32)
    y = block(x)
    _shape_assert(y, cfg.d_model)

    loss = y.pow(2).mean()
    loss.backward()
    print("MambaBlock test passed successfully.")


if __name__ == "__main__":
    _unit_test_mamba_block()

