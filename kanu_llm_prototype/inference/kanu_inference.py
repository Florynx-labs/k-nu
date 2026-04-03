"""
KÁNU Inference Engine
Step-by-step reasoning and generation
Supports French and English
"""
import torch
from transformers import AutoTokenizer
from typing import List, Dict, Any, Optional
import logging
import re

logger = logging.getLogger(__name__)


class KANUInference:
    """
    Inference engine for KÁNU LLM
    Provides step-by-step reasoning for engineering problems
    """
    
    def __init__(self, model, tokenizer, device: str = "cuda"):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        
        self.model.eval()
        self.model.to(device)
        
        # Physics validation rules
        self.physics_rules = self._load_physics_rules()
        
        logger.info("KÁNU Inference Engine initialized")
        logger.info(f"Device: {device}")
        logger.info(f"Model parameters: {model.get_num_params()/1e9:.2f}B")
    
    def _load_physics_rules(self) -> Dict[str, Any]:
        """Load physics validation rules"""
        return {
            'material_limits': {
                'Inconel 718': {'max_temp_k': 980, 'yield_strength_mpa': 1100},
                'SS 316L': {'max_temp_k': 870, 'yield_strength_mpa': 290},
                'Aluminum': {'max_temp_k': 500, 'yield_strength_mpa': 280},
                'Niobium C-103': {'max_temp_k': 1370, 'yield_strength_mpa': 345}
            },
            'propellant_isp_limits': {
                'LOX/RP-1': {'max_isp_vacuum': 360, 'max_isp_sea_level': 310},
                'LOX/LH2': {'max_isp_vacuum': 465, 'max_isp_sea_level': 390},
                'LOX/CH4': {'max_isp_vacuum': 380, 'max_isp_sea_level': 330}
            },
            'max_chamber_pressure_mpa': 35,  # Practical limit
            'min_wall_thickness_mm': 2.0,
        }
    
    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_k: int = 50,
        top_p: float = 0.9,
        do_sample: bool = True,
        language: str = "auto"  # "en", "fr", or "auto"
    ) -> str:
        """
        Generate response to prompt
        
        Args:
            prompt: Input prompt
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_k: Top-k sampling
            top_p: Nucleus sampling
            do_sample: Whether to sample or use greedy
            language: Language ("en", "fr", or "auto")
        
        Returns:
            Generated text
        """
        # Detect language if auto
        if language == "auto":
            language = self._detect_language(prompt)
        
        # Format prompt
        formatted_prompt = self._format_prompt(prompt, language)
        
        # Tokenize
        inputs = self.tokenizer(
            formatted_prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.model.config.max_seq_len - max_new_tokens
        )
        
        input_ids = inputs['input_ids'].to(self.device)
        attention_mask = inputs.get('attention_mask', None)
        if attention_mask is not None:
            attention_mask = attention_mask.to(self.device)
        
        # Generate
        with torch.no_grad():
            output_ids = self.model.generate(
                input_ids,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
                do_sample=do_sample
            )
        
        # Decode
        generated_text = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        
        # Extract response (remove prompt)
        response = generated_text[len(formatted_prompt):].strip()
        
        # Validate physics if response contains technical claims
        if self._contains_technical_claims(response):
            response = self._validate_and_annotate(response)
        
        return response
    
    def step_by_step_reasoning(
        self,
        problem: str,
        language: str = "auto"
    ) -> Dict[str, Any]:
        """
        Generate step-by-step reasoning for a problem
        
        Returns:
            {
                'problem': str,
                'language': str,
                'steps': List[str],
                'final_answer': str,
                'physics_validated': bool,
                'warnings': List[str]
            }
        """
        # Detect language
        if language == "auto":
            language = self._detect_language(problem)
        
        # Create step-by-step prompt
        if language == "fr":
            step_prompt = f"""Problème: {problem}

Résolvons ce problème étape par étape:

Étape 1:"""
        else:
            step_prompt = f"""Problem: {problem}

Let's solve this step-by-step:

Step 1:"""
        
        # Generate reasoning
        reasoning = self.generate(
            step_prompt,
            max_new_tokens=800,
            temperature=0.5,  # Lower temperature for more focused reasoning
            do_sample=True,
            language=language
        )
        
        # Parse steps
        steps = self._parse_steps(reasoning, language)
        
        # Extract final answer
        final_answer = self._extract_final_answer(reasoning, language)
        
        # Validate physics
        physics_valid, warnings = self._validate_physics(reasoning)
        
        return {
            'problem': problem,
            'language': language,
            'steps': steps,
            'reasoning': reasoning,
            'final_answer': final_answer,
            'physics_validated': physics_valid,
            'warnings': warnings
        }
    
    def _detect_language(self, text: str) -> str:
        """Detect if text is French or English"""
        french_indicators = ['est', 'sont', 'pour', 'avec', 'dans', 'une', 'des', 'les', 'qu']
        english_indicators = ['is', 'are', 'for', 'with', 'in', 'a', 'the', 'what', 'how']
        
        text_lower = text.lower()
        
        french_count = sum(1 for word in french_indicators if word in text_lower)
        english_count = sum(1 for word in english_indicators if word in text_lower)
        
        return "fr" if french_count > english_count else "en"
    
    def _format_prompt(self, prompt: str, language: str) -> str:
        """Format prompt for the model"""
        if language == "fr":
            return f"Question: {prompt}\nRéponse:"
        else:
            return f"Question: {prompt}\nAnswer:"
    
    def _contains_technical_claims(self, text: str) -> bool:
        """Check if text contains technical claims that need validation"""
        technical_keywords = [
            'mpa', 'temperature', 'pressure', 'isp', 'thrust', 'material',
            'inconel', 'aluminum', 'steel', 'strength', 'yield'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in technical_keywords)
    
    def _validate_and_annotate(self, text: str) -> str:
        """Validate physics claims and annotate if violations found"""
        violations = []
        
        # Check for impossible ISP claims
        isp_matches = re.findall(r'(\d+)\s*s\s+isp', text.lower())
        for isp_str in isp_matches:
            isp = int(isp_str)
            if isp > 500:
                violations.append(f"⚠️ ISP of {isp}s exceeds chemical propellant limits (~465s max)")
        
        # Check for impossible pressure claims
        pressure_matches = re.findall(r'(\d+)\s*mpa', text.lower())
        for pressure_str in pressure_matches:
            pressure = int(pressure_str)
            if pressure > self.physics_rules['max_chamber_pressure_mpa']:
                violations.append(f"⚠️ Pressure of {pressure} MPa exceeds practical limits (35 MPa max)")
        
        # Annotate if violations found
        if violations:
            annotation = "\n\n**PHYSICS VALIDATION WARNINGS:**\n"
            for violation in violations:
                annotation += f"- {violation}\n"
            annotation += "\n*KÁNU: These values may violate physical constraints. Please verify.*"
            
            return text + annotation
        
        return text
    
    def _parse_steps(self, reasoning: str, language: str) -> List[str]:
        """Parse reasoning into steps"""
        if language == "fr":
            step_pattern = r'Étape \d+:(.+?)(?=Étape \d+:|$)'
        else:
            step_pattern = r'Step \d+:(.+?)(?=Step \d+:|$)'
        
        steps = re.findall(step_pattern, reasoning, re.DOTALL)
        return [step.strip() for step in steps]
    
    def _extract_final_answer(self, reasoning: str, language: str) -> str:
        """Extract final answer from reasoning"""
        if language == "fr":
            answer_patterns = [
                r'Réponse finale:(.+?)$',
                r'Conclusion:(.+?)$',
                r'Donc,(.+?)$'
            ]
        else:
            answer_patterns = [
                r'Final answer:(.+?)$',
                r'Conclusion:(.+?)$',
                r'Therefore,(.+?)$'
            ]
        
        for pattern in answer_patterns:
            match = re.search(pattern, reasoning, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # If no explicit answer, return last sentence
        sentences = reasoning.split('.')
        return sentences[-1].strip() if sentences else ""
    
    def _validate_physics(self, text: str) -> tuple[bool, List[str]]:
        """Validate physics claims in text"""
        warnings = []
        
        # Check ISP limits
        isp_matches = re.findall(r'(\d+)\s*s', text.lower())
        for isp_str in isp_matches:
            isp = int(isp_str)
            if isp > 500:
                warnings.append(f"ISP {isp}s exceeds chemical limits")
        
        # Check pressure limits
        pressure_matches = re.findall(r'(\d+)\s*mpa', text.lower())
        for pressure_str in pressure_matches:
            pressure = int(pressure_str)
            if pressure > 35:
                warnings.append(f"Pressure {pressure} MPa exceeds practical limits")
        
        # Check temperature limits
        temp_matches = re.findall(r'(\d+)\s*k', text.lower())
        for temp_str in temp_matches:
            temp = int(temp_str)
            if temp > 4000:
                warnings.append(f"Temperature {temp}K is extremely high")
        
        physics_valid = len(warnings) == 0
        
        return physics_valid, warnings
    
    def chat(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        language: str = "auto"
    ) -> Dict[str, Any]:
        """
        Chat interface with conversation history
        
        Args:
            message: User message
            conversation_history: List of {'role': 'user'/'assistant', 'content': str}
            language: Language preference
        
        Returns:
            {
                'response': str,
                'language': str,
                'physics_validated': bool,
                'warnings': List[str]
            }
        """
        if conversation_history is None:
            conversation_history = []
        
        # Detect language
        if language == "auto":
            language = self._detect_language(message)
        
        # Build context from history
        context = ""
        for turn in conversation_history[-5:]:  # Last 5 turns
            role = turn['role']
            content = turn['content']
            
            if language == "fr":
                prefix = "Utilisateur:" if role == "user" else "KÁNU:"
            else:
                prefix = "User:" if role == "user" else "KÁNU:"
            
            context += f"{prefix} {content}\n"
        
        # Add current message
        if language == "fr":
            context += f"Utilisateur: {message}\nKÁNU:"
        else:
            context += f"User: {message}\nKÁNU:"
        
        # Generate response
        response = self.generate(
            context,
            max_new_tokens=512,
            temperature=0.7,
            language=language
        )
        
        # Validate physics
        physics_valid, warnings = self._validate_physics(response)
        
        return {
            'response': response,
            'language': language,
            'physics_validated': physics_valid,
            'warnings': warnings
        }


def load_kanu_for_inference(
    checkpoint_path: str,
    model_size: str = "1b",
    device: str = "cuda"
) -> KANUInference:
    """
    Load KÁNU model for inference
    
    Args:
        checkpoint_path: Path to model checkpoint
        model_size: "1b", "2b", or "3b"
        device: "cuda" or "cpu"
    
    Returns:
        KANUInference instance
    """
    from ..model.kanu_architecture import create_kanu_model
    
    # Create model
    model = create_kanu_model(model_size)
    
    # Load checkpoint
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    
    # Load tokenizer (using GPT-2 tokenizer as base)
    tokenizer = AutoTokenizer.from_pretrained("gpt2")
    tokenizer.pad_token = tokenizer.eos_token
    
    # Create inference engine
    inference = KANUInference(model, tokenizer, device)
    
    logger.info(f"KÁNU model loaded from {checkpoint_path}")
    
    return inference
