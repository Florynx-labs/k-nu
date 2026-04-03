"""
Multi-Design Proposal System
Generates and compares top 3-5 design candidates
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import logging
import uuid

logger = logging.getLogger(__name__)


@dataclass
class DesignProposal:
    """A complete design proposal with full analysis"""
    design_id: str
    name: str
    description: str
    parameters: Dict[str, Any]
    
    # Performance predictions
    predicted_performance: Dict[str, float] = field(default_factory=dict)
    
    # Simulation results
    simulation_results: Optional[Dict[str, Any]] = None
    stress_test_results: Optional[Dict[str, Any]] = None
    
    # Analysis
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    risks: List[Dict[str, Any]] = field(default_factory=list)
    
    # Manufacturing & Cost
    manufacturing_complexity: str = "medium"  # low, medium, high
    estimated_cost_usd: float = 0.0
    lead_time_months: float = 0.0
    
    # Scoring
    overall_score: float = 0.0
    confidence: float = 0.0
    
    # Rationale
    design_rationale: str = ""
    recommendation: str = ""


@dataclass
class DesignComparison:
    """Comparison between multiple designs"""
    designs: List[DesignProposal]
    comparison_matrix: Dict[str, List[float]] = field(default_factory=dict)
    trade_offs: List[str] = field(default_factory=list)
    recommendation: str = ""
    winner_id: Optional[str] = None


class MultiDesignSystem:
    """
    Generates and manages multiple design proposals
    Provides comparative analysis and recommendations
    """
    
    def __init__(self, target_count: int = 3):
        self.target_count = target_count
        self.proposals: List[DesignProposal] = []
        
        # Design archetypes
        self.archetypes = {
            'conservative': {
                'description': 'Proven technology, low risk, moderate performance',
                'risk_tolerance': 'low',
                'innovation_level': 'low',
                'cost_multiplier': 1.0
            },
            'balanced': {
                'description': 'Modern approach, balanced risk/reward',
                'risk_tolerance': 'medium',
                'innovation_level': 'medium',
                'cost_multiplier': 1.3
            },
            'aggressive': {
                'description': 'Cutting-edge, high performance, higher risk',
                'risk_tolerance': 'high',
                'innovation_level': 'high',
                'cost_multiplier': 1.8
            }
        }
    
    def generate_design_portfolio(self, requirements: Dict[str, Any],
                                  constraints: Dict[str, Any]) -> List[DesignProposal]:
        """
        Generate a portfolio of diverse design proposals
        """
        logger.info(f"Generating {self.target_count} design proposals")
        
        proposals = []
        
        # Generate different archetypes
        archetypes_to_use = list(self.archetypes.keys())[:self.target_count]
        
        for i, archetype_name in enumerate(archetypes_to_use):
            archetype = self.archetypes[archetype_name]
            
            proposal = self._generate_design_from_archetype(
                archetype_name,
                archetype,
                requirements,
                constraints,
                index=i+1
            )
            
            proposals.append(proposal)
        
        self.proposals = proposals
        return proposals
    
    def _generate_design_from_archetype(self, archetype_name: str,
                                       archetype: Dict[str, Any],
                                       requirements: Dict[str, Any],
                                       constraints: Dict[str, Any],
                                       index: int) -> DesignProposal:
        """Generate a design based on archetype"""
        
        # Select propellant based on archetype
        if archetype_name == 'conservative':
            propellant = 'LOX/RP-1'
            chamber_pressure_mpa = 15.0
            expansion_ratio = 25
            material = 'Inconel 718'
        elif archetype_name == 'balanced':
            propellant = 'LOX/CH4'
            chamber_pressure_mpa = 22.0
            expansion_ratio = 60
            material = 'Inconel 718'
        else:  # aggressive
            propellant = 'LOX/LH2'
            chamber_pressure_mpa = 28.0
            expansion_ratio = 120
            material = 'Inconel 718'
        
        # Adjust for environment
        environment = constraints.get('environment', 'general')
        if environment == 'vacuum':
            expansion_ratio *= 1.5
        elif environment == 'sea_level':
            expansion_ratio *= 0.6
        
        # Build parameters
        parameters = {
            'design_id': f"design_{archetype_name}_{uuid.uuid4().hex[:6]}",
            'propellant_name': propellant,
            'chamber_pressure_pa': chamber_pressure_mpa * 1e6,
            'chamber_radius_m': 0.15,
            'chamber_length_m': 0.8,
            'wall_thickness_m': 0.005,
            'throat_radius_m': 0.08,
            'expansion_ratio': expansion_ratio,
            'of_ratio': self._get_optimal_of_ratio(propellant),
            'chamber_material': material,
            'nozzle_material': material,
            'nozzle_bell_factor': 0.8,
            'environment': environment
        }
        
        # Create proposal
        proposal = DesignProposal(
            design_id=parameters['design_id'],
            name=f"Design {index}: {archetype_name.title()} Approach",
            description=archetype['description'],
            parameters=parameters,
            design_rationale=self._generate_rationale(archetype_name, propellant, requirements),
            manufacturing_complexity=archetype['innovation_level'],
            estimated_cost_usd=self._estimate_cost(parameters, archetype['cost_multiplier'])
        )
        
        # Add strengths and weaknesses
        proposal.strengths = self._identify_strengths(archetype_name, propellant)
        proposal.weaknesses = self._identify_weaknesses(archetype_name, propellant)
        
        return proposal
    
    def _get_optimal_of_ratio(self, propellant: str) -> float:
        """Get optimal O/F ratio for propellant"""
        ratios = {
            'LOX/RP-1': 2.56,
            'LOX/LH2': 6.0,
            'LOX/CH4': 3.4
        }
        return ratios.get(propellant, 3.0)
    
    def _generate_rationale(self, archetype: str, propellant: str,
                           requirements: Dict[str, Any]) -> str:
        """Generate design rationale"""
        rationales = {
            'conservative': (
                f"This design uses proven {propellant} technology with conservative "
                f"chamber pressures and expansion ratios. Prioritizes reliability and "
                f"manufacturability over peak performance. Suitable for missions where "
                f"risk reduction is paramount."
            ),
            'balanced': (
                f"Modern {propellant} design balancing performance and practicality. "
                f"Uses current best practices with moderate innovation. Good choice "
                f"for most applications requiring solid performance without excessive risk."
            ),
            'aggressive': (
                f"High-performance {propellant} design pushing state-of-the-art. "
                f"Maximizes ISP and thrust through advanced techniques. Requires "
                f"sophisticated manufacturing and testing. Best for missions where "
                f"performance justifies higher development cost and risk."
            )
        }
        return rationales.get(archetype, "Standard design approach")
    
    def _identify_strengths(self, archetype: str, propellant: str) -> List[str]:
        """Identify design strengths"""
        strengths = []
        
        if archetype == 'conservative':
            strengths.extend([
                "Proven, flight-tested technology",
                "Lower development risk",
                "Easier to manufacture",
                "Shorter qualification timeline",
                "Lower cost"
            ])
        elif archetype == 'balanced':
            strengths.extend([
                "Good performance-to-cost ratio",
                "Moderate risk profile",
                "Modern, efficient design",
                "Reasonable manufacturing complexity"
            ])
        else:  # aggressive
            strengths.extend([
                "Highest performance potential",
                "Best mass efficiency",
                "State-of-the-art technology",
                "Competitive advantage"
            ])
        
        # Propellant-specific strengths
        if propellant == 'LOX/RP-1':
            strengths.append("Dense propellant, compact tanks")
        elif propellant == 'LOX/LH2':
            strengths.append("Highest specific impulse")
        elif propellant == 'LOX/CH4':
            strengths.append("Clean combustion, reusability-friendly")
        
        return strengths
    
    def _identify_weaknesses(self, archetype: str, propellant: str) -> List[str]:
        """Identify design weaknesses"""
        weaknesses = []
        
        if archetype == 'conservative':
            weaknesses.extend([
                "Lower performance than alternatives",
                "May not meet aggressive mission requirements",
                "Less competitive long-term"
            ])
        elif archetype == 'balanced':
            weaknesses.extend([
                "Not optimal for any single metric",
                "Moderate in all aspects"
            ])
        else:  # aggressive
            weaknesses.extend([
                "Higher development cost",
                "Longer qualification timeline",
                "Greater technical risk",
                "Complex manufacturing requirements",
                "Requires advanced testing facilities"
            ])
        
        # Propellant-specific weaknesses
        if propellant == 'LOX/RP-1':
            weaknesses.append("Lower ISP than hydrogen")
        elif propellant == 'LOX/LH2':
            weaknesses.extend([
                "Low density, large tanks required",
                "Cryogenic handling complexity",
                "Higher cost"
            ])
        elif propellant == 'LOX/CH4':
            weaknesses.append("Less flight heritage than RP-1 or LH2")
        
        return weaknesses
    
    def _estimate_cost(self, parameters: Dict[str, Any], multiplier: float) -> float:
        """Estimate development and unit cost"""
        # Base cost model (simplified)
        base_cost = 2_000_000  # $2M baseline
        
        # Adjust for chamber pressure
        pressure_mpa = parameters.get('chamber_pressure_pa', 0) / 1e6
        if pressure_mpa > 20:
            base_cost *= 1.3
        
        # Adjust for expansion ratio (nozzle complexity)
        expansion_ratio = parameters.get('expansion_ratio', 0)
        if expansion_ratio > 80:
            base_cost *= 1.4
        
        # Adjust for propellant
        propellant = parameters.get('propellant_name', '')
        if 'LH2' in propellant:
            base_cost *= 1.5  # Hydrogen systems more expensive
        
        return base_cost * multiplier
    
    def compare_designs(self, simulation_results: Optional[Dict[str, Any]] = None) -> DesignComparison:
        """
        Compare all design proposals and generate recommendation
        """
        if not self.proposals:
            raise ValueError("No proposals to compare")
        
        # Build comparison matrix
        comparison_matrix = {
            'ISP (predicted)': [],
            'Thrust (predicted)': [],
            'Cost': [],
            'Risk': [],
            'Manufacturing': [],
            'Overall Score': []
        }
        
        trade_offs = []
        
        for proposal in self.proposals:
            # Predict performance (simplified - would use surrogate model)
            predicted_isp = self._predict_isp(proposal.parameters)
            predicted_thrust = self._predict_thrust(proposal.parameters)
            
            proposal.predicted_performance = {
                'isp': predicted_isp,
                'thrust': predicted_thrust
            }
            
            comparison_matrix['ISP (predicted)'].append(predicted_isp)
            comparison_matrix['Thrust (predicted)'].append(predicted_thrust)
            comparison_matrix['Cost'].append(proposal.estimated_cost_usd)
            
            # Risk score (1-10)
            risk_score = self._calculate_risk_score(proposal)
            comparison_matrix['Risk'].append(risk_score)
            
            # Manufacturing score (1-10)
            mfg_scores = {'low': 8, 'medium': 5, 'high': 3}
            comparison_matrix['Manufacturing'].append(
                mfg_scores.get(proposal.manufacturing_complexity, 5)
            )
            
            # Overall score
            overall = self._calculate_overall_score(proposal, predicted_isp, predicted_thrust, risk_score)
            proposal.overall_score = overall
            comparison_matrix['Overall Score'].append(overall)
        
        # Identify trade-offs
        trade_offs = self._identify_trade_offs(comparison_matrix)
        
        # Determine winner
        winner = max(self.proposals, key=lambda p: p.overall_score)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(winner, self.proposals, trade_offs)
        
        return DesignComparison(
            designs=self.proposals,
            comparison_matrix=comparison_matrix,
            trade_offs=trade_offs,
            recommendation=recommendation,
            winner_id=winner.design_id
        )
    
    def _predict_isp(self, parameters: Dict[str, Any]) -> float:
        """Predict ISP (simplified)"""
        propellant = parameters.get('propellant_name', '')
        expansion_ratio = parameters.get('expansion_ratio', 30)
        
        # Base ISP by propellant
        base_isp = {
            'LOX/RP-1': 300,
            'LOX/LH2': 450,
            'LOX/CH4': 370
        }.get(propellant, 320)
        
        # Adjust for expansion ratio (vacuum performance)
        if expansion_ratio > 50:
            base_isp *= 1.1
        
        return base_isp
    
    def _predict_thrust(self, parameters: Dict[str, Any]) -> float:
        """Predict thrust (simplified)"""
        chamber_pressure = parameters.get('chamber_pressure_pa', 15e6)
        throat_area = 3.14159 * parameters.get('throat_radius_m', 0.08) ** 2
        
        # Simplified thrust calculation
        thrust = chamber_pressure * throat_area * 1.8  # Approximate thrust coefficient
        
        return thrust
    
    def _calculate_risk_score(self, proposal: DesignProposal) -> float:
        """Calculate risk score (1-10, lower is better)"""
        risk = 5.0  # Baseline
        
        if proposal.manufacturing_complexity == 'high':
            risk += 2
        elif proposal.manufacturing_complexity == 'low':
            risk -= 2
        
        # High chamber pressure increases risk
        pressure_mpa = proposal.parameters.get('chamber_pressure_pa', 0) / 1e6
        if pressure_mpa > 25:
            risk += 1.5
        
        # LH2 adds complexity
        if 'LH2' in proposal.parameters.get('propellant_name', ''):
            risk += 1
        
        return max(1, min(10, risk))
    
    def _calculate_overall_score(self, proposal: DesignProposal,
                                 isp: float, thrust: float, risk: float) -> float:
        """Calculate overall score (0-100)"""
        # Normalize metrics
        isp_score = (isp / 450) * 30  # Max 30 points
        thrust_score = min((thrust / 1e6) * 20, 20)  # Max 20 points
        cost_score = max(0, 20 - (proposal.estimated_cost_usd / 1e6) * 5)  # Max 20 points
        risk_score = (10 - risk) * 2  # Max 20 points (lower risk = higher score)
        mfg_score = {'low': 10, 'medium': 7, 'high': 4}.get(proposal.manufacturing_complexity, 7)
        
        total = isp_score + thrust_score + cost_score + risk_score + mfg_score
        
        return min(100, total)
    
    def _identify_trade_offs(self, comparison_matrix: Dict[str, List[float]]) -> List[str]:
        """Identify key trade-offs between designs"""
        trade_offs = []
        
        # ISP vs Cost
        isp_values = comparison_matrix['ISP (predicted)']
        cost_values = comparison_matrix['Cost']
        
        if max(isp_values) - min(isp_values) > 50:
            trade_offs.append(
                f"ISP ranges from {min(isp_values):.0f}s to {max(isp_values):.0f}s, "
                f"with higher ISP designs costing ${max(cost_values)/1e6:.1f}M vs ${min(cost_values)/1e6:.1f}M"
            )
        
        # Performance vs Risk
        risk_values = comparison_matrix['Risk']
        trade_offs.append(
            f"Higher performance designs carry elevated risk (risk scores: {min(risk_values):.1f} to {max(risk_values):.1f})"
        )
        
        # Manufacturing complexity
        mfg_values = comparison_matrix['Manufacturing']
        if max(mfg_values) - min(mfg_values) > 3:
            trade_offs.append(
                "Manufacturing complexity varies significantly - simpler designs faster to produce"
            )
        
        return trade_offs
    
    def _generate_recommendation(self, winner: DesignProposal,
                                 all_proposals: List[DesignProposal],
                                 trade_offs: List[str]) -> str:
        """Generate final recommendation"""
        recommendation = f"**Recommended Design: {winner.name}**\n\n"
        recommendation += f"{winner.design_rationale}\n\n"
        recommendation += f"**Key Strengths:**\n"
        for strength in winner.strengths[:3]:
            recommendation += f"• {strength}\n"
        
        recommendation += f"\n**Predicted Performance:**\n"
        recommendation += f"• ISP: {winner.predicted_performance.get('isp', 0):.0f} s\n"
        recommendation += f"• Thrust: {winner.predicted_performance.get('thrust', 0)/1000:.0f} kN\n"
        recommendation += f"• Estimated Cost: ${winner.estimated_cost_usd/1e6:.1f}M\n"
        
        recommendation += f"\n**Trade-offs:**\n"
        for trade_off in trade_offs[:2]:
            recommendation += f"• {trade_off}\n"
        
        recommendation += f"\n**Next Steps:**\n"
        recommendation += f"1. Run detailed stress tests and simulations\n"
        recommendation += f"2. Validate manufacturing feasibility\n"
        recommendation += f"3. Refine design through optimization\n"
        
        return recommendation
    
    def get_design_by_id(self, design_id: str) -> Optional[DesignProposal]:
        """Get a specific design proposal"""
        for proposal in self.proposals:
            if proposal.design_id == design_id:
                return proposal
        return None
