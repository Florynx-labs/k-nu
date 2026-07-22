import dataclasses
from typing import Optional, Tuple, Dict

import torch
import torch.nn as nn
import torch.nn.functional as F

@dataclasses.dataclass
class PhysicsFlags:
    """The 12 physical constraints predicted by the Physics Head."""
    energy_conservation: int = 0
    mass_conservation: int = 1
    thermal_causality: int = 2
    positive_pressure: int = 3
    second_law_thermodynamics: int = 4
    charge_conservation: int = 5
    momentum_conservation: int = 6
    angular_momentum: int = 7
    causality_light: int = 8
    positive_temperature: int = 9
    positive_density: int = 10
    dimensionless_consistency: int = 11

    @classmethod
    def num_flags(cls):
        return 12


class PhysicsValidationHead(nn.Module):
    """
    Predicts physical validity flags from the last hidden state of the LLM.
    Used for hard constraint enforcement during generation.
    """
    def __init__(self, d_model: int, hidden_dim: int = 256):
        super().__init__()
        self.d_model = d_model
        self.num_flags = PhysicsFlags.num_flags()
        
        self.fc1 = nn.Linear(d_model, hidden_dim)
        self.act = nn.GELU()
        self.fc2 = nn.Linear(hidden_dim, self.num_flags)
        
    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """
        Args:
            hidden_states: (B, S, D)
        Returns:
            physics_logits: (B, S, num_flags) - logits before sigmoid
        """
        x = self.fc1(hidden_states)
        x = self.act(x)
        x = self.fc2(x)
        return x


class PhysicsLogitPenalty:
    """Applies a penalty to the main LM logits if a physics violation is detected."""
    def __init__(self, penalty_value: float = -1e4):
        self.penalty_value = penalty_value
        
    def __call__(self, lm_logits: torch.Tensor, physics_probs: torch.Tensor, threshold: float = 0.5) -> torch.Tensor:
        """
        Args:
            lm_logits: (B, S, V) Main language model logits
            physics_probs: (B, S, num_flags) Probabilities of valid physics
            threshold: Probability below which a violation is flagged
        Returns:
            Penalized lm_logits
        """
        # (B, S) - 1 if ANY flag is < threshold (meaning a violation occurred)
        violation_mask = (physics_probs < threshold).any(dim=-1)
        
        # Apply the penalty broadcasted across the vocab.
        penalty = torch.zeros_like(lm_logits)
        penalty[violation_mask] = self.penalty_value
        
        return lm_logits + penalty


class PhysicsLoss(nn.Module):
    """BCE Loss for the Physics Head training."""
    def __init__(self):
        super().__init__()
        self.bce = nn.BCEWithLogitsLoss()
        
    def forward(self, physics_logits: torch.Tensor, target_flags: torch.Tensor) -> torch.Tensor:
        """
        Args:
            physics_logits: (B, S, num_flags)
            target_flags: (B, S, num_flags) float tensor of 0.0 or 1.0
        """
        return self.bce(physics_logits, target_flags)


def _unit_test_physics_head():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    d_model = 128
    head = PhysicsValidationHead(d_model=d_model).to(device)
    
    hidden_states = torch.randn(2, 5, d_model, device=device)
    logits = head(hidden_states)
    probs = torch.sigmoid(logits)
    
    assert logits.shape == (2, 5, 12), "Shape mismatch"
    
    # Test penalty
    lm_logits = torch.randn(2, 5, 100, device=device) # vocab = 100
    penalty_applier = PhysicsLogitPenalty()
    
    # Force a violation on batch 0, seq 2
    probs[0, 2, 0] = 0.1
    
    penalized_logits = penalty_applier(lm_logits, probs, threshold=0.5)
    assert penalized_logits[0, 2].mean() < -1000, "Penalty not applied correctly"
    
    # Test Loss
    targets = torch.ones_like(logits)
    loss_fn = PhysicsLoss()
    loss = loss_fn(logits, targets)
    loss.backward()
    
    print("PhysicsHead test passed successfully.")


if __name__ == "__main__":
    _unit_test_physics_head()
