"""
Conversational Reasoning Layer
Enables KÁNU to discuss ideas like a senior engineer
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ConversationPhase(Enum):
    """Phases of engineering conversation"""
    EXPLORATION = "exploration"          # Understanding the problem
    IDEATION = "ideation"                # Brainstorming solutions
    ANALYSIS = "analysis"                # Deep technical analysis
    PROPOSAL = "proposal"                # Presenting designs
    REFINEMENT = "refinement"            # Iterative improvement
    VALIDATION = "validation"            # Final checks
    DELIVERY = "delivery"                # Engineering-ready outputs


class EngineerPersona(Enum):
    """Different engineering perspectives"""
    SYSTEMS_ENGINEER = "systems"         # Big picture, requirements
    PROPULSION_SPECIALIST = "propulsion" # Deep technical expertise
    MANUFACTURING_ENGINEER = "manufacturing" # Buildability focus
    COST_ANALYST = "cost"                # Budget and economics
    RELIABILITY_ENGINEER = "reliability" # Safety and robustness
    PROJECT_MANAGER = "project"          # Timeline and coordination


@dataclass
class ConversationContext:
    """Context for engineering conversation"""
    phase: ConversationPhase
    user_expertise_level: str = "intermediate"  # beginner, intermediate, expert
    discussion_history: List[Dict[str, Any]] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    constraints_clarified: Dict[str, Any] = field(default_factory=dict)
    trade_offs_discussed: List[Dict[str, Any]] = field(default_factory=list)
    current_focus: Optional[str] = None


@dataclass
class EngineeringDialogue:
    """A single dialogue turn in the conversation"""
    speaker: str  # "user", "kanu", or agent name
    persona: Optional[EngineerPersona] = None
    content: str = ""
    technical_depth: int = 5  # 1-10 scale
    questions_asked: List[str] = field(default_factory=list)
    insights_shared: List[str] = field(default_factory=list)
    concerns_raised: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class ConversationalReasoning:
    """
    Senior engineer-like conversational reasoning
    Discusses ideas, asks clarifying questions, proposes alternatives
    """
    
    def __init__(self):
        self.context = ConversationContext(phase=ConversationPhase.EXPLORATION)
        self.dialogue_history: List[EngineeringDialogue] = []
        
        # Engineering knowledge base
        self.design_patterns = self._load_design_patterns()
        self.common_pitfalls = self._load_common_pitfalls()
        self.trade_off_frameworks = self._load_trade_off_frameworks()
    
    def process_user_input(self, user_message: str, 
                          context: Optional[Dict[str, Any]] = None) -> EngineeringDialogue:
        """
        Process user input and generate senior engineer response
        """
        # Analyze user intent and technical depth
        intent = self._analyze_intent(user_message)
        
        # Determine appropriate phase
        self._update_conversation_phase(intent, user_message)
        
        # Generate response based on phase
        response = self._generate_phase_appropriate_response(
            user_message, intent, context
        )
        
        # Record dialogue
        dialogue = EngineeringDialogue(
            speaker="kanu",
            persona=self._select_persona(intent),
            content=response['content'],
            technical_depth=response['technical_depth'],
            questions_asked=response.get('questions', []),
            insights_shared=response.get('insights', []),
            concerns_raised=response.get('concerns', []),
            recommendations=response.get('recommendations', [])
        )
        
        self.dialogue_history.append(dialogue)
        
        return dialogue
    
    def _analyze_intent(self, message: str) -> Dict[str, Any]:
        """Analyze what the user is trying to accomplish"""
        message_lower = message.lower()
        
        intent = {
            'type': 'general',
            'specificity': 'vague',
            'technical_level': 'intermediate',
            'requires_clarification': False
        }
        
        # Check for specific intents
        if any(word in message_lower for word in ['design', 'create', 'build', 'develop']):
            intent['type'] = 'design_request'
            intent['specificity'] = 'specific' if any(
                word in message_lower for word in ['mpa', 'kn', 'isp', 'lox', 'rp-1']
            ) else 'vague'
        
        elif any(word in message_lower for word in ['why', 'how', 'explain', 'what if']):
            intent['type'] = 'question'
            intent['technical_level'] = 'expert' if 'thermodynamic' in message_lower else 'intermediate'
        
        elif any(word in message_lower for word in ['compare', 'versus', 'vs', 'difference']):
            intent['type'] = 'comparison'
        
        elif any(word in message_lower for word in ['problem', 'issue', 'failure', 'not working']):
            intent['type'] = 'troubleshooting'
        
        elif any(word in message_lower for word in ['optimize', 'improve', 'better', 'enhance']):
            intent['type'] = 'optimization'
        
        # Check if clarification needed
        if intent['specificity'] == 'vague' and intent['type'] == 'design_request':
            intent['requires_clarification'] = True
        
        return intent
    
    def _update_conversation_phase(self, intent: Dict[str, Any], message: str):
        """Update conversation phase based on intent"""
        current_phase = self.context.phase
        
        # Phase transitions
        if intent['type'] == 'design_request' and current_phase == ConversationPhase.EXPLORATION:
            if intent['requires_clarification']:
                # Stay in exploration to gather requirements
                pass
            else:
                self.context.phase = ConversationPhase.IDEATION
        
        elif intent['type'] == 'question' and current_phase == ConversationPhase.IDEATION:
            self.context.phase = ConversationPhase.ANALYSIS
        
        elif 'ready' in message.lower() or 'proceed' in message.lower():
            if current_phase == ConversationPhase.ANALYSIS:
                self.context.phase = ConversationPhase.PROPOSAL
            elif current_phase == ConversationPhase.PROPOSAL:
                self.context.phase = ConversationPhase.REFINEMENT
        
        logger.info(f"Conversation phase: {current_phase.value} → {self.context.phase.value}")
    
    def _generate_phase_appropriate_response(self, message: str, 
                                            intent: Dict[str, Any],
                                            context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate response appropriate for current conversation phase"""
        phase = self.context.phase
        
        if phase == ConversationPhase.EXPLORATION:
            return self._exploration_response(message, intent)
        
        elif phase == ConversationPhase.IDEATION:
            return self._ideation_response(message, intent)
        
        elif phase == ConversationPhase.ANALYSIS:
            return self._analysis_response(message, intent, context)
        
        elif phase == ConversationPhase.PROPOSAL:
            return self._proposal_response(message, intent, context)
        
        elif phase == ConversationPhase.REFINEMENT:
            return self._refinement_response(message, intent, context)
        
        else:
            return self._general_response(message, intent)
    
    def _exploration_response(self, message: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Response during exploration phase - gather requirements"""
        questions = []
        insights = []
        
        if intent['requires_clarification']:
            questions.extend([
                "What's the primary mission profile? (e.g., LEO launch, deep space, upper stage)",
                "Do you have target performance metrics? (thrust, ISP, T/W ratio)",
                "Are there specific constraints? (cost, mass, propellant availability)",
                "What's the operating environment? (sea level, vacuum, variable altitude)"
            ])
            
            content = (
                "I'd like to understand your requirements better before proposing designs. "
                "A few clarifying questions:\n\n" +
                "\n".join(f"• {q}" for q in questions) +
                "\n\nThis will help me propose the most suitable solutions."
            )
        else:
            # Extract what we know
            insights.append("I understand you're looking for a rocket engine design.")
            content = (
                "Got it. Let me think through this systematically.\n\n"
                "Based on your requirements, I'm considering several approaches. "
                "Before I dive into specific designs, let me share some initial thoughts..."
            )
        
        return {
            'content': content,
            'technical_depth': 5,
            'questions': questions,
            'insights': insights,
            'concerns': [],
            'recommendations': []
        }
    
    def _ideation_response(self, message: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Response during ideation - brainstorm solutions"""
        insights = [
            "Multiple design approaches could work here",
            "Each has different trade-offs we should consider"
        ]
        
        recommendations = [
            "Approach 1: High-pressure LOX/RP-1 for robust, proven performance",
            "Approach 2: LOX/LH2 for maximum efficiency (higher complexity)",
            "Approach 3: LOX/CH4 as a balanced middle ground"
        ]
        
        content = (
            "Let me walk through a few conceptual approaches:\n\n"
            "**Option 1: LOX/RP-1 (Kerosene)**\n"
            "• Proven, reliable, dense propellant\n"
            "• Good thrust density, moderate ISP (~300s vacuum)\n"
            "• Lower cost, easier to handle\n"
            "• Trade-off: Heavier than hydrogen\n\n"
            
            "**Option 2: LOX/LH2 (Hydrogen)**\n"
            "• Highest ISP (~450s vacuum)\n"
            "• Excellent for upper stages\n"
            "• Trade-off: Low density, cryogenic challenges, higher cost\n\n"
            
            "**Option 3: LOX/CH4 (Methane)**\n"
            "• Modern choice, good ISP (~370s vacuum)\n"
            "• Cleaner combustion than RP-1\n"
            "• Easier than LH2, denser than LH2\n"
            "• Trade-off: Less flight heritage\n\n"
            
            "Which direction resonates with your mission requirements?"
        )
        
        return {
            'content': content,
            'technical_depth': 6,
            'questions': ["Which approach aligns best with your priorities?"],
            'insights': insights,
            'concerns': [],
            'recommendations': recommendations
        }
    
    def _analysis_response(self, message: str, intent: Dict[str, Any],
                          context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Response during analysis - deep technical discussion"""
        insights = []
        concerns = []
        
        # Deep technical analysis
        content = (
            "Let me dive into the technical details:\n\n"
            "**Thermodynamic Considerations:**\n"
            "• Chamber pressure drives performance but increases structural loads\n"
            "• Optimal O/F ratio depends on propellant combination\n"
            "• Expansion ratio must match operating altitude\n\n"
            
            "**Structural Challenges:**\n"
            "• High chamber pressure → need Inconel 718 or similar\n"
            "• Regenerative cooling essential above ~15 MPa\n"
            "• Nozzle throat experiences peak thermal/mechanical stress\n\n"
            
            "**Manufacturing Reality:**\n"
            "• Complex geometries require additive manufacturing or precision machining\n"
            "• Material selection impacts both performance and cost\n"
            "• Testing and qualification add significant schedule\n\n"
            
            "Key question: What's your risk tolerance vs. performance requirements?"
        )
        
        insights.extend([
            "Higher performance usually means higher complexity and cost",
            "Material selection is critical for both performance and manufacturability",
            "Testing requirements scale with design novelty"
        ])
        
        concerns.append("Need to balance performance targets with practical constraints")
        
        return {
            'content': content,
            'technical_depth': 8,
            'questions': ["What's your risk tolerance vs. performance requirements?"],
            'insights': insights,
            'concerns': concerns,
            'recommendations': []
        }
    
    def _proposal_response(self, message: str, intent: Dict[str, Any],
                          context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Response during proposal - present concrete designs"""
        content = (
            "Based on our discussion, I'm proposing **3 design candidates** "
            "that balance your requirements:\n\n"
            "I'll run full simulations and stress tests on each, then we can "
            "compare them in detail. Sound good?"
        )
        
        return {
            'content': content,
            'technical_depth': 7,
            'questions': ["Ready for me to generate and simulate these designs?"],
            'insights': ["Multiple candidates allow us to explore the trade space"],
            'concerns': [],
            'recommendations': ["Let's simulate all three and compare results"]
        }
    
    def _refinement_response(self, message: str, intent: Dict[str, Any],
                            context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Response during refinement - iterative improvement"""
        content = (
            "Looking at the simulation results, I see opportunities to improve:\n\n"
            "• Design 1 shows good ISP but marginal structural margins\n"
            "• Design 2 is robust but heavier than optimal\n"
            "• Design 3 has the best balance\n\n"
            "I can refine Design 3 by:\n"
            "1. Optimizing chamber geometry for mass reduction\n"
            "2. Adjusting expansion ratio for your specific altitude\n"
            "3. Fine-tuning O/F ratio for peak performance\n\n"
            "Want me to run an optimization iteration?"
        )
        
        return {
            'content': content,
            'technical_depth': 7,
            'questions': ["Should I optimize Design 3 further?"],
            'insights': ["Iterative refinement often yields 5-10% improvements"],
            'concerns': [],
            'recommendations': ["Focus optimization on Design 3 (best baseline)"]
        }
    
    def _general_response(self, message: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        """General response for other cases"""
        content = "I'm here to help with your rocket engine design. What would you like to explore?"
        
        return {
            'content': content,
            'technical_depth': 5,
            'questions': [],
            'insights': [],
            'concerns': [],
            'recommendations': []
        }
    
    def _select_persona(self, intent: Dict[str, Any]) -> EngineerPersona:
        """Select appropriate engineering persona"""
        if intent['type'] == 'design_request':
            return EngineerPersona.PROPULSION_SPECIALIST
        elif 'cost' in str(intent).lower():
            return EngineerPersona.COST_ANALYST
        elif 'manufacturing' in str(intent).lower() or 'build' in str(intent).lower():
            return EngineerPersona.MANUFACTURING_ENGINEER
        else:
            return EngineerPersona.SYSTEMS_ENGINEER
    
    def _load_design_patterns(self) -> Dict[str, Any]:
        """Load common design patterns"""
        return {
            'high_performance_vacuum': {
                'propellant': 'LOX/LH2',
                'chamber_pressure_range': (15e6, 25e6),
                'expansion_ratio_range': (80, 150),
                'typical_isp': 450
            },
            'robust_booster': {
                'propellant': 'LOX/RP-1',
                'chamber_pressure_range': (10e6, 20e6),
                'expansion_ratio_range': (15, 40),
                'typical_isp': 300
            },
            'modern_reusable': {
                'propellant': 'LOX/CH4',
                'chamber_pressure_range': (20e6, 30e6),
                'expansion_ratio_range': (40, 80),
                'typical_isp': 370
            }
        }
    
    def _load_common_pitfalls(self) -> List[Dict[str, str]]:
        """Load common design pitfalls"""
        return [
            {
                'pitfall': 'Over-optimization for single metric',
                'consequence': 'Fragile design that fails in off-nominal conditions',
                'mitigation': 'Multi-objective optimization with robustness constraints'
            },
            {
                'pitfall': 'Ignoring manufacturing constraints',
                'consequence': 'Unbuildable or extremely expensive design',
                'mitigation': 'Early consultation with manufacturing engineers'
            },
            {
                'pitfall': 'Underestimating thermal loads',
                'consequence': 'Material failure, reduced life',
                'mitigation': 'Conservative thermal analysis with safety factors'
            }
        ]
    
    def _load_trade_off_frameworks(self) -> Dict[str, Any]:
        """Load trade-off analysis frameworks"""
        return {
            'performance_vs_cost': {
                'axes': ['ISP', 'Cost'],
                'typical_trade': 'Each 10s ISP improvement costs ~$500k in development'
            },
            'performance_vs_complexity': {
                'axes': ['ISP', 'System Complexity'],
                'typical_trade': 'LH2 gives +50% ISP but 3x system complexity'
            },
            'mass_vs_robustness': {
                'axes': ['Dry Mass', 'Reliability'],
                'typical_trade': 'Each 10% mass reduction reduces safety margin'
            }
        }
    
    def get_conversation_summary(self) -> str:
        """Generate summary of conversation so far"""
        summary = f"**Conversation Phase:** {self.context.phase.value}\n\n"
        
        if self.context.assumptions:
            summary += "**Assumptions Made:**\n"
            for assumption in self.context.assumptions:
                summary += f"• {assumption}\n"
            summary += "\n"
        
        if self.context.open_questions:
            summary += "**Open Questions:**\n"
            for question in self.context.open_questions:
                summary += f"• {question}\n"
            summary += "\n"
        
        if self.context.constraints_clarified:
            summary += "**Clarified Constraints:**\n"
            for key, value in self.context.constraints_clarified.items():
                summary += f"• {key}: {value}\n"
        
        return summary
