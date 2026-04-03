"""
Lightweight Transformer Architecture for Engineering Reasoning
Built from scratch for KÁNU V2
"""
import numpy as np
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MultiHeadAttention:
    """Multi-head self-attention mechanism"""
    
    def __init__(self, d_model: int, num_heads: int):
        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads
        
        # Initialize weights (simplified - in production use proper initialization)
        self.W_q = np.random.randn(d_model, d_model) * 0.01
        self.W_k = np.random.randn(d_model, d_model) * 0.01
        self.W_v = np.random.randn(d_model, d_model) * 0.01
        self.W_o = np.random.randn(d_model, d_model) * 0.01
    
    def forward(self, x: np.ndarray, mask: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Forward pass of multi-head attention
        x: (batch_size, seq_len, d_model)
        """
        batch_size, seq_len, _ = x.shape
        
        # Linear projections
        Q = np.dot(x, self.W_q)
        K = np.dot(x, self.W_k)
        V = np.dot(x, self.W_v)
        
        # Reshape for multi-head
        Q = Q.reshape(batch_size, seq_len, self.num_heads, self.d_k).transpose(0, 2, 1, 3)
        K = K.reshape(batch_size, seq_len, self.num_heads, self.d_k).transpose(0, 2, 1, 3)
        V = V.reshape(batch_size, seq_len, self.num_heads, self.d_k).transpose(0, 2, 1, 3)
        
        # Scaled dot-product attention
        scores = np.matmul(Q, K.transpose(0, 1, 3, 2)) / np.sqrt(self.d_k)
        
        if mask is not None:
            scores = scores + mask
        
        attention_weights = self._softmax(scores)
        attention_output = np.matmul(attention_weights, V)
        
        # Reshape and project
        attention_output = attention_output.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)
        output = np.dot(attention_output, self.W_o)
        
        return output
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Numerically stable softmax"""
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=-1, keepdims=True)


class FeedForward:
    """Position-wise feed-forward network"""
    
    def __init__(self, d_model: int, d_ff: int):
        self.W1 = np.random.randn(d_model, d_ff) * 0.01
        self.b1 = np.zeros(d_ff)
        self.W2 = np.random.randn(d_ff, d_model) * 0.01
        self.b2 = np.zeros(d_model)
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass with ReLU activation"""
        hidden = np.maximum(0, np.dot(x, self.W1) + self.b1)  # ReLU
        output = np.dot(hidden, self.W2) + self.b2
        return output


class LayerNorm:
    """Layer normalization"""
    
    def __init__(self, d_model: int, eps: float = 1e-6):
        self.gamma = np.ones(d_model)
        self.beta = np.zeros(d_model)
        self.eps = eps
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """Normalize across feature dimension"""
        mean = np.mean(x, axis=-1, keepdims=True)
        std = np.std(x, axis=-1, keepdims=True)
        return self.gamma * (x - mean) / (std + self.eps) + self.beta


class TransformerBlock:
    """Single transformer encoder block"""
    
    def __init__(self, d_model: int, num_heads: int, d_ff: int, dropout: float = 0.1):
        self.attention = MultiHeadAttention(d_model, num_heads)
        self.feed_forward = FeedForward(d_model, d_ff)
        self.norm1 = LayerNorm(d_model)
        self.norm2 = LayerNorm(d_model)
        self.dropout = dropout
    
    def forward(self, x: np.ndarray, mask: Optional[np.ndarray] = None) -> np.ndarray:
        """Forward pass with residual connections"""
        # Self-attention with residual
        attn_output = self.attention.forward(x, mask)
        x = self.norm1.forward(x + attn_output)
        
        # Feed-forward with residual
        ff_output = self.feed_forward.forward(x)
        x = self.norm2.forward(x + ff_output)
        
        return x


class EngineeringTokenizer:
    """
    Specialized tokenizer for engineering concepts
    Vocabulary includes technical terms, units, materials, etc.
    """
    
    def __init__(self):
        # Build engineering-specific vocabulary
        self.vocab = self._build_vocab()
        self.token_to_id = {token: idx for idx, token in enumerate(self.vocab)}
        self.id_to_token = {idx: token for token, idx in self.token_to_id.items()}
        self.vocab_size = len(self.vocab)
    
    def _build_vocab(self) -> List[str]:
        """Build engineering vocabulary"""
        vocab = [
            # Special tokens
            '<PAD>', '<UNK>', '<START>', '<END>',
            
            # Common words
            'design', 'engine', 'rocket', 'chamber', 'nozzle', 'thrust', 'pressure',
            'temperature', 'material', 'stress', 'strain', 'performance', 'efficiency',
            'cost', 'mass', 'optimize', 'simulate', 'test', 'validate', 'analyze',
            
            # Propellants
            'LOX', 'LH2', 'RP-1', 'CH4', 'methane', 'hydrogen', 'kerosene', 'oxygen',
            
            # Materials
            'Inconel', 'steel', 'titanium', 'aluminum', 'copper', 'niobium',
            
            # Units
            'MPa', 'kN', 'kg', 'm', 'mm', 's', 'K', 'Pa',
            
            # Properties
            'high', 'low', 'medium', 'maximum', 'minimum', 'optimal', 'critical',
            
            # Actions
            'increase', 'decrease', 'improve', 'reduce', 'enhance', 'modify',
            
            # Concepts
            'combustion', 'cooling', 'expansion', 'ratio', 'flow', 'rate',
            'thermal', 'structural', 'failure', 'safety', 'reliability',
            
            # Numbers (0-9)
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
            
            # Punctuation
            '.', ',', '?', '!', ':', ';', '(', ')', '[', ']'
        ]
        
        return vocab
    
    def encode(self, text: str) -> List[int]:
        """Convert text to token IDs"""
        # Simple word-level tokenization
        tokens = text.lower().split()
        token_ids = []
        
        for token in tokens:
            if token in self.token_to_id:
                token_ids.append(self.token_to_id[token])
            else:
                token_ids.append(self.token_to_id['<UNK>'])
        
        return token_ids
    
    def decode(self, token_ids: List[int]) -> str:
        """Convert token IDs back to text"""
        tokens = [self.id_to_token.get(tid, '<UNK>') for tid in token_ids]
        return ' '.join(tokens)


class MiniLLM:
    """
    Lightweight transformer-based LLM for engineering reasoning
    Designed specifically for KÁNU V2 internal reasoning
    """
    
    def __init__(self, vocab_size: int = 100, d_model: int = 128, 
                 num_heads: int = 4, num_layers: int = 3, d_ff: int = 512):
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.num_heads = num_heads
        self.num_layers = num_layers
        
        # Token embeddings
        self.token_embeddings = np.random.randn(vocab_size, d_model) * 0.01
        
        # Positional embeddings
        self.max_seq_len = 512
        self.positional_embeddings = self._create_positional_embeddings()
        
        # Transformer blocks
        self.blocks = [
            TransformerBlock(d_model, num_heads, d_ff)
            for _ in range(num_layers)
        ]
        
        # Output projection
        self.output_projection = np.random.randn(d_model, vocab_size) * 0.01
        
        logger.info(f"MiniLLM initialized: {num_layers} layers, {d_model} dim, {num_heads} heads")
    
    def _create_positional_embeddings(self) -> np.ndarray:
        """Create sinusoidal positional embeddings"""
        position = np.arange(self.max_seq_len)[:, np.newaxis]
        div_term = np.exp(np.arange(0, self.d_model, 2) * -(np.log(10000.0) / self.d_model))
        
        pos_embeddings = np.zeros((self.max_seq_len, self.d_model))
        pos_embeddings[:, 0::2] = np.sin(position * div_term)
        pos_embeddings[:, 1::2] = np.cos(position * div_term)
        
        return pos_embeddings
    
    def forward(self, token_ids: np.ndarray, mask: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Forward pass through the model
        token_ids: (batch_size, seq_len)
        Returns: (batch_size, seq_len, vocab_size) logits
        """
        batch_size, seq_len = token_ids.shape
        
        # Embed tokens
        x = self.token_embeddings[token_ids]  # (batch_size, seq_len, d_model)
        
        # Add positional embeddings
        x = x + self.positional_embeddings[:seq_len]
        
        # Pass through transformer blocks
        for block in self.blocks:
            x = block.forward(x, mask)
        
        # Project to vocabulary
        logits = np.dot(x, self.output_projection)
        
        return logits
    
    def generate(self, prompt_ids: List[int], max_length: int = 50, 
                temperature: float = 0.7) -> List[int]:
        """
        Generate tokens autoregressively
        """
        generated = prompt_ids.copy()
        
        for _ in range(max_length):
            # Prepare input
            input_ids = np.array([generated])
            
            # Forward pass
            logits = self.forward(input_ids)
            
            # Get logits for last token
            next_token_logits = logits[0, -1, :] / temperature
            
            # Sample from distribution
            probs = self._softmax(next_token_logits)
            next_token = np.random.choice(len(probs), p=probs)
            
            # Append to sequence
            generated.append(next_token)
            
            # Stop if end token
            if next_token == 3:  # <END> token
                break
        
        return generated
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Numerically stable softmax"""
        exp_x = np.exp(x - np.max(x))
        return exp_x / np.sum(exp_x)
    
    def reason(self, problem: str, tokenizer: EngineeringTokenizer) -> str:
        """
        Internal reasoning about an engineering problem
        """
        # Encode problem
        prompt_ids = [2] + tokenizer.encode(problem)  # Add <START> token
        
        # Generate reasoning
        generated_ids = self.generate(prompt_ids, max_length=100)
        
        # Decode
        reasoning = tokenizer.decode(generated_ids[len(prompt_ids):])
        
        return reasoning
    
    def save_weights(self, filepath: str):
        """Save model weights"""
        weights = {
            'token_embeddings': self.token_embeddings,
            'output_projection': self.output_projection,
            'blocks': [
                {
                    'attention': {
                        'W_q': block.attention.W_q,
                        'W_k': block.attention.W_k,
                        'W_v': block.attention.W_v,
                        'W_o': block.attention.W_o
                    },
                    'feed_forward': {
                        'W1': block.feed_forward.W1,
                        'b1': block.feed_forward.b1,
                        'W2': block.feed_forward.W2,
                        'b2': block.feed_forward.b2
                    }
                }
                for block in self.blocks
            ]
        }
        np.savez(filepath, **weights)
        logger.info(f"Model weights saved to {filepath}")
    
    def load_weights(self, filepath: str):
        """Load model weights"""
        weights = np.load(filepath, allow_pickle=True)
        self.token_embeddings = weights['token_embeddings']
        self.output_projection = weights['output_projection']
        logger.info(f"Model weights loaded from {filepath}")


class EngineeringReasoner:
    """
    High-level reasoning engine using MiniLLM
    Specialized for engineering problem decomposition
    """
    
    def __init__(self):
        self.tokenizer = EngineeringTokenizer()
        self.model = MiniLLM(
            vocab_size=self.tokenizer.vocab_size,
            d_model=128,
            num_heads=4,
            num_layers=3,
            d_ff=512
        )
        
        # Engineering knowledge base (rules and heuristics)
        self.knowledge_base = self._build_knowledge_base()
    
    def _build_knowledge_base(self) -> Dict[str, Any]:
        """Build engineering knowledge base"""
        return {
            'physics_laws': {
                'thermodynamics': [
                    'Energy is conserved',
                    'Entropy always increases',
                    'Heat flows from hot to cold'
                ],
                'mechanics': [
                    'Force equals mass times acceleration',
                    'Action and reaction are equal and opposite',
                    'Stress equals force per unit area'
                ],
                'fluid_dynamics': [
                    'Mass flow is conserved',
                    'Bernoulli equation applies to incompressible flow',
                    'Viscosity causes energy loss'
                ]
            },
            'material_limits': {
                'Inconel 718': {'max_temp_k': 980, 'yield_strength_mpa': 1100},
                'SS 316L': {'max_temp_k': 870, 'yield_strength_mpa': 290},
                'Aluminum': {'max_temp_k': 500, 'yield_strength_mpa': 280}
            },
            'design_heuristics': [
                'Safety factor should be > 1.5 for critical components',
                'Chamber pressure limited by material strength',
                'Expansion ratio optimized for operating altitude',
                'Cooling required above 15 MPa chamber pressure'
            ]
        }
    
    def decompose_problem(self, problem: str) -> List[str]:
        """
        Decompose engineering problem into sub-problems
        Uses internal reasoning
        """
        # Use LLM for initial decomposition
        reasoning = self.model.reason(problem, self.tokenizer)
        
        # Apply engineering heuristics
        sub_problems = []
        
        if 'design' in problem.lower():
            sub_problems.extend([
                'Define requirements and constraints',
                'Select propellant combination',
                'Determine chamber pressure',
                'Calculate nozzle geometry',
                'Select materials',
                'Design cooling system',
                'Estimate performance',
                'Validate against physics'
            ])
        
        elif 'optimize' in problem.lower():
            sub_problems.extend([
                'Identify optimization objectives',
                'Define design variables',
                'Set constraints',
                'Run parametric sweep',
                'Evaluate trade-offs',
                'Select optimal point'
            ])
        
        return sub_problems
    
    def validate_physics(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate design against physics laws
        Returns validation result with violations
        """
        violations = []
        warnings = []
        
        # Check material limits
        chamber_temp = design.get('chamber_temperature_k', 0)
        material = design.get('chamber_material', '')
        
        if material in self.knowledge_base['material_limits']:
            limits = self.knowledge_base['material_limits'][material]
            if chamber_temp > limits['max_temp_k']:
                violations.append(
                    f"Temperature {chamber_temp}K exceeds {material} limit {limits['max_temp_k']}K"
                )
        
        # Check stress limits
        chamber_pressure = design.get('chamber_pressure_pa', 0)
        wall_thickness = design.get('wall_thickness_m', 0)
        chamber_radius = design.get('chamber_radius_m', 0)
        
        if wall_thickness > 0:
            hoop_stress = (chamber_pressure * chamber_radius) / wall_thickness
            
            if material in self.knowledge_base['material_limits']:
                yield_strength = self.knowledge_base['material_limits'][material]['yield_strength_mpa'] * 1e6
                safety_factor = yield_strength / hoop_stress
                
                if safety_factor < 1.0:
                    violations.append(
                        f"Hoop stress {hoop_stress/1e6:.1f} MPa exceeds yield strength"
                    )
                elif safety_factor < 1.5:
                    warnings.append(
                        f"Safety factor {safety_factor:.2f} is below recommended 1.5"
                    )
        
        return {
            'valid': len(violations) == 0,
            'violations': violations,
            'warnings': warnings,
            'safety_factor': safety_factor if 'safety_factor' in locals() else None
        }
    
    def reason_about_trade_offs(self, option_a: Dict[str, Any], 
                                option_b: Dict[str, Any]) -> str:
        """
        Reason about trade-offs between two design options
        """
        reasoning = []
        
        # Compare performance
        if 'isp' in option_a and 'isp' in option_b:
            isp_diff = option_a['isp'] - option_b['isp']
            if abs(isp_diff) > 10:
                reasoning.append(
                    f"Option A has {isp_diff:+.0f}s ISP advantage" if isp_diff > 0
                    else f"Option B has {-isp_diff:+.0f}s ISP advantage"
                )
        
        # Compare cost
        if 'cost' in option_a and 'cost' in option_b:
            cost_diff = option_a['cost'] - option_b['cost']
            if abs(cost_diff) > 100000:
                reasoning.append(
                    f"Option A costs ${cost_diff/1e6:+.2f}M more" if cost_diff > 0
                    else f"Option B costs ${-cost_diff/1e6:+.2f}M more"
                )
        
        # Compare complexity
        if 'complexity' in option_a and 'complexity' in option_b:
            if option_a['complexity'] != option_b['complexity']:
                reasoning.append(
                    f"Option A is more complex" if option_a['complexity'] > option_b['complexity']
                    else f"Option B is more complex"
                )
        
        return '\n'.join(reasoning) if reasoning else "Options are similar"
