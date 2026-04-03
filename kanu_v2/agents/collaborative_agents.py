"""
Collaborative Multi-Agent System for KÁNU V2
Agents debate, iterate, and refine outputs collaboratively
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import time

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Specialized agent roles"""
    ARCHITECT = "architect"
    PHYSICS = "physics"
    SIMULATION = "simulation"
    FAILURE = "failure"
    COST = "cost"
    MANUFACTURING = "manufacturing"
    CRITIC = "critic"
    EXPLANATION = "explanation"


class DebateStance(Enum):
    """Agent's stance in debate"""
    SUPPORT = "support"
    OPPOSE = "oppose"
    NEUTRAL = "neutral"
    CONDITIONAL = "conditional"


@dataclass
class AgentArgument:
    """An argument made by an agent in debate"""
    agent_role: AgentRole
    stance: DebateStance
    argument: str
    evidence: List[str] = field(default_factory=list)
    confidence: float = 0.8
    counter_arguments: List[str] = field(default_factory=list)


@dataclass
class DebateRound:
    """A round of multi-agent debate"""
    round_number: int
    topic: str
    arguments: List[AgentArgument] = field(default_factory=list)
    consensus_reached: bool = False
    consensus_decision: Optional[str] = None
    dissenting_opinions: List[str] = field(default_factory=list)


class CollaborativeAgent:
    """
    Base class for collaborative agents
    All agents can debate, challenge, and refine ideas
    """
    
    def __init__(self, role: AgentRole, expertise_areas: List[str]):
        self.role = role
        self.expertise_areas = expertise_areas
        self.confidence_threshold = 0.7
        self.debate_history: List[DebateRound] = []
    
    def evaluate_proposal(self, proposal: Dict[str, Any]) -> AgentArgument:
        """
        Evaluate a design proposal from this agent's perspective
        Must be implemented by subclasses
        """
        raise NotImplementedError
    
    def challenge_argument(self, argument: AgentArgument) -> Optional[str]:
        """
        Challenge another agent's argument if it conflicts with expertise
        """
        # Base implementation - subclasses override with specific logic
        if argument.confidence < self.confidence_threshold:
            return f"Confidence level {argument.confidence:.2f} is below threshold"
        return None
    
    def propose_refinement(self, current_design: Dict[str, Any]) -> Dict[str, Any]:
        """
        Propose refinements to current design
        """
        raise NotImplementedError


class ArchitectAgent(CollaborativeAgent):
    """
    Defines system concepts and high-level architecture
    Focuses on requirements, interfaces, and system integration
    """
    
    def __init__(self):
        super().__init__(
            role=AgentRole.ARCHITECT,
            expertise_areas=['system_design', 'requirements', 'integration', 'interfaces']
        )
    
    def evaluate_proposal(self, proposal: Dict[str, Any]) -> AgentArgument:
        """Evaluate from system architecture perspective"""
        issues = []
        strengths = []
        
        # Check if requirements are met
        if 'requirements' in proposal:
            req = proposal['requirements']
            if req.get('thrust_target'):
                predicted_thrust = proposal.get('predicted_thrust', 0)
                if predicted_thrust < req['thrust_target'] * 0.9:
                    issues.append(f"Thrust {predicted_thrust/1000:.0f} kN below target")
                else:
                    strengths.append("Meets thrust requirements")
        
        # Check system integration
        if 'propellant' in proposal and 'tank_interface' not in proposal:
            issues.append("Missing tank interface definition")
        
        # Check modularity
        if proposal.get('modular_design', False):
            strengths.append("Modular design enables easier maintenance")
        
        # Determine stance
        if len(issues) > 3:
            stance = DebateStance.OPPOSE
        elif len(issues) > 0:
            stance = DebateStance.CONDITIONAL
        else:
            stance = DebateStance.SUPPORT
        
        argument_text = self._format_argument(strengths, issues)
        
        return AgentArgument(
            agent_role=self.role,
            stance=stance,
            argument=argument_text,
            evidence=strengths + issues,
            confidence=0.85
        )
    
    def _format_argument(self, strengths: List[str], issues: List[str]) -> str:
        """Format argument text"""
        arg = "**System Architecture Perspective:**\n\n"
        
        if strengths:
            arg += "**Strengths:**\n"
            for s in strengths[:3]:
                arg += f"• {s}\n"
            arg += "\n"
        
        if issues:
            arg += "**Concerns:**\n"
            for i in issues[:3]:
                arg += f"• {i}\n"
        
        return arg
    
    def propose_refinement(self, current_design: Dict[str, Any]) -> Dict[str, Any]:
        """Propose system-level refinements"""
        refinements = current_design.copy()
        
        # Add interface definitions if missing
        if 'interfaces' not in refinements:
            refinements['interfaces'] = {
                'propellant_inlet': 'Standard flange connection',
                'thrust_mount': 'Four-point gimbal mount',
                'electrical': 'MIL-STD-1553 data bus'
            }
        
        # Add modularity if beneficial
        if refinements.get('chamber_pressure_pa', 0) > 20e6:
            refinements['modular_cooling'] = True
            refinements['modular_injector'] = True
        
        return refinements


class PhysicsValidationAgent(CollaborativeAgent):
    """
    Validates all designs against physical laws
    NEVER allows physically impossible designs
    """
    
    def __init__(self):
        super().__init__(
            role=AgentRole.PHYSICS,
            expertise_areas=['thermodynamics', 'fluid_dynamics', 'structural_mechanics', 'materials']
        )
        
        # Physics constants and limits
        self.material_limits = {
            'Inconel 718': {'max_temp_k': 980, 'yield_strength_mpa': 1100},
            'SS 316L': {'max_temp_k': 870, 'yield_strength_mpa': 290},
            'Niobium C-103': {'max_temp_k': 1370, 'yield_strength_mpa': 345}
        }
    
    def evaluate_proposal(self, proposal: Dict[str, Any]) -> AgentArgument:
        """Strict physics validation"""
        violations = []
        warnings = []
        
        # Validate material temperature limits
        chamber_temp = proposal.get('chamber_temperature_k', 3500)  # Typical combustion temp
        material = proposal.get('chamber_material', '')
        
        if material in self.material_limits:
            max_temp = self.material_limits[material]['max_temp_k']
            if chamber_temp > max_temp:
                violations.append(
                    f"PHYSICS VIOLATION: Chamber temperature {chamber_temp}K exceeds "
                    f"{material} limit {max_temp}K. Design is IMPOSSIBLE."
                )
        
        # Validate structural integrity
        pressure = proposal.get('chamber_pressure_pa', 0)
        radius = proposal.get('chamber_radius_m', 0)
        thickness = proposal.get('wall_thickness_m', 0)
        
        if thickness > 0 and radius > 0:
            hoop_stress = (pressure * radius) / thickness
            
            if material in self.material_limits:
                yield_strength = self.material_limits[material]['yield_strength_mpa'] * 1e6
                safety_factor = yield_strength / hoop_stress
                
                if safety_factor < 1.0:
                    violations.append(
                        f"PHYSICS VIOLATION: Hoop stress {hoop_stress/1e6:.1f} MPa exceeds "
                        f"yield strength {yield_strength/1e6:.0f} MPa. WILL FAIL."
                    )
                elif safety_factor < 1.5:
                    warnings.append(
                        f"WARNING: Safety factor {safety_factor:.2f} below recommended 1.5"
                    )
        
        # Validate thermodynamics
        if 'expansion_ratio' in proposal:
            er = proposal['expansion_ratio']
            if er < 1:
                violations.append("PHYSICS VIOLATION: Expansion ratio < 1 is impossible")
            elif er > 300:
                warnings.append(f"Expansion ratio {er:.0f} is extremely high and impractical")
        
        # Determine stance - OPPOSE if any violations
        if violations:
            stance = DebateStance.OPPOSE
            confidence = 1.0  # Absolute certainty on physics violations
        elif warnings:
            stance = DebateStance.CONDITIONAL
            confidence = 0.9
        else:
            stance = DebateStance.SUPPORT
            confidence = 0.85
        
        argument = "**Physics Validation:**\n\n"
        
        if violations:
            argument += "**CRITICAL VIOLATIONS (Design is IMPOSSIBLE):**\n"
            for v in violations:
                argument += f"• {v}\n"
            argument += "\n**This design CANNOT be built. It violates fundamental physics.**\n"
        
        if warnings:
            argument += "**Warnings:**\n"
            for w in warnings:
                argument += f"• {w}\n"
        
        if not violations and not warnings:
            argument += "✓ All physics checks passed\n"
            argument += "✓ Design is physically realizable\n"
        
        return AgentArgument(
            agent_role=self.role,
            stance=stance,
            argument=argument,
            evidence=violations + warnings,
            confidence=confidence
        )
    
    def propose_refinement(self, current_design: Dict[str, Any]) -> Dict[str, Any]:
        """Propose physics-compliant refinements"""
        refinements = current_design.copy()
        
        # Fix material temperature violations
        chamber_temp = refinements.get('chamber_temperature_k', 3500)
        material = refinements.get('chamber_material', '')
        
        if material in self.material_limits:
            if chamber_temp > self.material_limits[material]['max_temp_k']:
                # Suggest better material
                for mat, limits in self.material_limits.items():
                    if chamber_temp <= limits['max_temp_k']:
                        refinements['chamber_material'] = mat
                        refinements['material_change_reason'] = f"Temperature compliance"
                        break
                
                # If no material works, add cooling
                if refinements.get('chamber_material') == material:
                    refinements['regenerative_cooling'] = True
                    refinements['cooling_reason'] = "Required for temperature management"
        
        # Fix structural violations
        pressure = refinements.get('chamber_pressure_pa', 0)
        radius = refinements.get('chamber_radius_m', 0)
        thickness = refinements.get('wall_thickness_m', 0)
        
        if thickness > 0 and radius > 0:
            material = refinements.get('chamber_material', '')
            if material in self.material_limits:
                yield_strength = self.material_limits[material]['yield_strength_mpa'] * 1e6
                
                # Calculate required thickness for SF=1.5
                required_thickness = (pressure * radius * 1.5) / yield_strength
                
                if thickness < required_thickness:
                    refinements['wall_thickness_m'] = required_thickness
                    refinements['thickness_change_reason'] = "Structural safety (SF=1.5)"
        
        return refinements


class CostAnalysisAgent(CollaborativeAgent):
    """
    Estimates costs and ensures economic feasibility
    Challenges designs that are prohibitively expensive
    """
    
    def __init__(self):
        super().__init__(
            role=AgentRole.COST,
            expertise_areas=['cost_estimation', 'economics', 'manufacturing_cost', 'lifecycle_cost']
        )
        
        # Cost models
        self.material_costs_per_kg = {
            'Inconel 718': 80,
            'SS 316L': 15,
            'Niobium C-103': 500,
            'Titanium': 35,
            'Aluminum': 5
        }
    
    def evaluate_proposal(self, proposal: Dict[str, Any]) -> AgentArgument:
        """Evaluate cost implications"""
        cost_estimate = self._estimate_cost(proposal)
        concerns = []
        notes = []
        
        # Check if cost is reasonable
        if cost_estimate > 10_000_000:
            concerns.append(f"Very high cost ${cost_estimate/1e6:.1f}M may not be economically viable")
        elif cost_estimate > 5_000_000:
            notes.append(f"Moderate-high cost ${cost_estimate/1e6:.1f}M")
        else:
            notes.append(f"Reasonable cost ${cost_estimate/1e6:.1f}M")
        
        # Check material costs
        material = proposal.get('chamber_material', '')
        if material == 'Niobium C-103':
            concerns.append("Niobium C-103 is very expensive - consider alternatives")
        
        # Check complexity cost drivers
        if proposal.get('regenerative_cooling'):
            notes.append("Regenerative cooling adds ~$800k to development")
        
        stance = DebateStance.CONDITIONAL if concerns else DebateStance.SUPPORT
        
        argument = f"**Cost Analysis:**\n\n"
        argument += f"**Estimated Cost:** ${cost_estimate/1e6:.2f}M\n\n"
        
        if concerns:
            argument += "**Cost Concerns:**\n"
            for c in concerns:
                argument += f"• {c}\n"
            argument += "\n"
        
        if notes:
            argument += "**Notes:**\n"
            for n in notes:
                argument += f"• {n}\n"
        
        return AgentArgument(
            agent_role=self.role,
            stance=stance,
            argument=argument,
            evidence=[f"Cost: ${cost_estimate/1e6:.2f}M"] + concerns,
            confidence=0.75
        )
    
    def _estimate_cost(self, design: Dict[str, Any]) -> float:
        """Estimate total cost"""
        base_cost = 2_000_000
        
        # Material cost
        material = design.get('chamber_material', 'Inconel 718')
        mass_kg = design.get('mass_kg', 50)
        material_cost = self.material_costs_per_kg.get(material, 50) * mass_kg
        
        # Pressure multiplier
        pressure_mpa = design.get('chamber_pressure_pa', 15e6) / 1e6
        if pressure_mpa > 25:
            base_cost *= 1.5
        elif pressure_mpa > 20:
            base_cost *= 1.3
        
        # Complexity multipliers
        if design.get('regenerative_cooling'):
            base_cost += 800_000
        
        if design.get('expansion_ratio', 30) > 100:
            base_cost += 400_000
        
        return base_cost + material_cost
    
    def propose_refinement(self, current_design: Dict[str, Any]) -> Dict[str, Any]:
        """Propose cost-reducing refinements"""
        refinements = current_design.copy()
        
        # Suggest cheaper materials if possible
        if refinements.get('chamber_material') == 'Niobium C-103':
            chamber_temp = refinements.get('chamber_temperature_k', 3500)
            if chamber_temp <= 980:
                refinements['chamber_material'] = 'Inconel 718'
                refinements['cost_optimization'] = 'Material substitution saves ~$400k'
        
        # Simplify if over-designed
        pressure = refinements.get('chamber_pressure_pa', 0) / 1e6
        if pressure > 25:
            refinements['pressure_reduction_suggestion'] = "Consider 22 MPa for cost savings"
        
        return refinements


class ManufacturingAgent(CollaborativeAgent):
    """
    Ensures designs are actually buildable
    Challenges designs with manufacturing impossibilities
    """
    
    def __init__(self):
        super().__init__(
            role=AgentRole.MANUFACTURING,
            expertise_areas=['manufacturing', 'machining', 'assembly', 'tolerances', 'processes']
        )
    
    def evaluate_proposal(self, proposal: Dict[str, Any]) -> AgentArgument:
        """Evaluate manufacturability"""
        issues = []
        notes = []
        
        # Check wall thickness
        thickness_mm = proposal.get('wall_thickness_m', 0.005) * 1000
        if thickness_mm < 2.0:
            issues.append(f"Wall thickness {thickness_mm:.1f}mm is below minimum machinable (2mm)")
        elif thickness_mm < 3.0:
            notes.append(f"Thin walls {thickness_mm:.1f}mm require precision machining")
        
        # Check throat radius
        throat_radius_mm = proposal.get('throat_radius_m', 0.08) * 1000
        if throat_radius_mm < 20:
            notes.append("Small throat requires precision boring")
        
        # Check expansion ratio (affects nozzle length)
        er = proposal.get('expansion_ratio', 30)
        if er > 150:
            issues.append(f"Expansion ratio {er:.0f} creates very long nozzle - difficult to manufacture")
        
        # Check material machinability
        material = proposal.get('chamber_material', '')
        if material == 'Niobium C-103':
            notes.append("Niobium requires specialized machining and inert atmosphere")
        
        stance = DebateStance.OPPOSE if len(issues) > 2 else (
            DebateStance.CONDITIONAL if issues else DebateStance.SUPPORT
        )
        
        argument = "**Manufacturing Assessment:**\n\n"
        
        if issues:
            argument += "**Manufacturability Issues:**\n"
            for i in issues:
                argument += f"• {i}\n"
            argument += "\n"
        
        if notes:
            argument += "**Manufacturing Notes:**\n"
            for n in notes:
                argument += f"• {n}\n"
        
        if not issues:
            argument += "✓ Design is manufacturable with standard processes\n"
        
        return AgentArgument(
            agent_role=self.role,
            stance=stance,
            argument=argument,
            evidence=issues + notes,
            confidence=0.8
        )
    
    def propose_refinement(self, current_design: Dict[str, Any]) -> Dict[str, Any]:
        """Propose manufacturing-friendly refinements"""
        refinements = current_design.copy()
        
        # Fix wall thickness
        thickness_m = refinements.get('wall_thickness_m', 0.005)
        if thickness_m < 0.002:
            refinements['wall_thickness_m'] = 0.003
            refinements['manufacturing_adjustment'] = "Increased to minimum machinable thickness"
        
        # Simplify expansion ratio if too high
        er = refinements.get('expansion_ratio', 30)
        if er > 150:
            refinements['expansion_ratio'] = 120
            refinements['er_adjustment'] = "Reduced for manufacturability"
        
        return refinements


class CriticAgent(CollaborativeAgent):
    """
    Challenges ALL designs and finds weaknesses
    Acts as red team to ensure robustness
    """
    
    def __init__(self):
        super().__init__(
            role=AgentRole.CRITIC,
            expertise_areas=['risk_analysis', 'failure_modes', 'assumptions', 'edge_cases']
        )
    
    def evaluate_proposal(self, proposal: Dict[str, Any]) -> AgentArgument:
        """Challenge and find weaknesses"""
        challenges = []
        assumptions = []
        
        # Challenge assumptions
        if 'propellant' in proposal:
            assumptions.append(f"Assumes {proposal['propellant']} is available and cost-effective")
        
        # Find potential failure modes
        if not proposal.get('regenerative_cooling') and proposal.get('chamber_pressure_pa', 0) > 20e6:
            challenges.append("High pressure without explicit cooling - thermal failure risk")
        
        # Challenge performance claims
        if 'predicted_isp' in proposal:
            isp = proposal['predicted_isp']
            propellant = proposal.get('propellant', '')
            if 'LH2' in propellant and isp > 470:
                challenges.append(f"ISP {isp:.0f}s seems optimistic for {propellant}")
        
        # Challenge cost estimates
        if 'estimated_cost' in proposal and proposal['estimated_cost'] < 1_000_000:
            challenges.append("Cost estimate seems low for rocket engine development")
        
        # Always find something to challenge (red team mindset)
        if not challenges:
            challenges.append("Design needs stress testing under off-nominal conditions")
        
        stance = DebateStance.CONDITIONAL  # Critic is always skeptical
        
        argument = "**Critical Review:**\n\n"
        argument += "**Challenges:**\n"
        for c in challenges:
            argument += f"• {c}\n"
        argument += "\n"
        
        if assumptions:
            argument += "**Assumptions to Validate:**\n"
            for a in assumptions:
                argument += f"• {a}\n"
        
        return AgentArgument(
            agent_role=self.role,
            stance=stance,
            argument=argument,
            evidence=challenges + assumptions,
            confidence=0.9
        )
    
    def propose_refinement(self, current_design: Dict[str, Any]) -> Dict[str, Any]:
        """Propose risk-reducing refinements"""
        refinements = current_design.copy()
        
        # Add safety margins
        if 'safety_factor' not in refinements:
            refinements['safety_factor'] = 1.8
            refinements['safety_rationale'] = "Conservative margin for unknown unknowns"
        
        # Add redundancy where critical
        if refinements.get('chamber_pressure_pa', 0) > 25e6:
            refinements['pressure_relief_valve'] = True
            refinements['redundant_sensors'] = True
        
        return refinements


class AgentDebateSystem:
    """
    Manages multi-agent debates and consensus building
    """
    
    def __init__(self):
        self.agents = {
            AgentRole.ARCHITECT: ArchitectAgent(),
            AgentRole.PHYSICS: PhysicsValidationAgent(),
            AgentRole.COST: CostAnalysisAgent(),
            AgentRole.MANUFACTURING: ManufacturingAgent(),
            AgentRole.CRITIC: CriticAgent()
        }
        
        self.debate_history: List[DebateRound] = []
        self.max_debate_rounds = 3
    
    def debate_proposal(self, proposal: Dict[str, Any], topic: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Run multi-agent debate on a proposal
        Returns (consensus_reached, refined_proposal)
        """
        logger.info(f"Starting debate on: {topic}")
        
        current_proposal = proposal.copy()
        
        for round_num in range(1, self.max_debate_rounds + 1):
            logger.info(f"Debate round {round_num}/{self.max_debate_rounds}")
            
            debate_round = DebateRound(
                round_number=round_num,
                topic=topic
            )
            
            # Each agent evaluates current proposal
            for role, agent in self.agents.items():
                argument = agent.evaluate_proposal(current_proposal)
                debate_round.arguments.append(argument)
                
                logger.info(f"{role.value}: {argument.stance.value} (confidence: {argument.confidence:.2f})")
            
            # Check for consensus
            consensus, decision = self._check_consensus(debate_round)
            
            if consensus:
                debate_round.consensus_reached = True
                debate_round.consensus_decision = decision
                self.debate_history.append(debate_round)
                logger.info(f"Consensus reached: {decision}")
                return True, current_proposal
            
            # If no consensus, apply refinements
            current_proposal = self._apply_refinements(current_proposal, debate_round)
            
            self.debate_history.append(debate_round)
        
        # Max rounds reached without full consensus
        logger.warning("Max debate rounds reached without full consensus")
        return False, current_proposal
    
    def _check_consensus(self, debate_round: DebateRound) -> Tuple[bool, str]:
        """Check if consensus is reached"""
        stances = [arg.stance for arg in debate_round.arguments]
        
        # Count stances
        support_count = sum(1 for s in stances if s == DebateStance.SUPPORT)
        oppose_count = sum(1 for s in stances if s == DebateStance.OPPOSE)
        
        # Physics agent has veto power on violations
        physics_arg = next((arg for arg in debate_round.arguments 
                           if arg.agent_role == AgentRole.PHYSICS), None)
        
        if physics_arg and physics_arg.stance == DebateStance.OPPOSE:
            return False, "REJECTED: Physics violations detected"
        
        # Majority support = consensus
        if support_count >= len(self.agents) * 0.6:
            return True, "APPROVED: Majority support"
        
        # Strong opposition = reject
        if oppose_count >= len(self.agents) * 0.4:
            return False, "REJECTED: Significant opposition"
        
        # Otherwise, needs refinement
        return False, "REFINE: Mixed opinions, needs improvement"
    
    def _apply_refinements(self, proposal: Dict[str, Any], 
                          debate_round: DebateRound) -> Dict[str, Any]:
        """Apply refinements suggested by agents"""
        refined = proposal.copy()
        
        # Prioritize physics refinements
        physics_agent = self.agents[AgentRole.PHYSICS]
        refined = physics_agent.propose_refinement(refined)
        
        # Apply other refinements
        for role in [AgentRole.MANUFACTURING, AgentRole.COST]:
            agent = self.agents[role]
            refined = agent.propose_refinement(refined)
        
        return refined
    
    def get_debate_summary(self) -> str:
        """Get summary of all debates"""
        summary = "# Multi-Agent Debate Summary\n\n"
        
        for debate in self.debate_history:
            summary += f"## Round {debate.round_number}: {debate.topic}\n\n"
            
            for arg in debate.arguments:
                summary += f"**{arg.agent_role.value.upper()}** ({arg.stance.value}):\n"
                summary += f"{arg.argument}\n\n"
            
            if debate.consensus_reached:
                summary += f"**Consensus:** {debate.consensus_decision}\n\n"
            else:
                summary += "**Status:** Refinement needed\n\n"
            
            summary += "---\n\n"
        
        return summary
