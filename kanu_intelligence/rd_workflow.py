"""
R&D Workflow System
User-driven iterative design and refinement workflow
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
import time

logger = logging.getLogger(__name__)


class WorkflowStage(Enum):
    """Stages in the R&D workflow"""
    REQUIREMENTS = "requirements"
    CONCEPT = "concept"
    PRELIMINARY_DESIGN = "preliminary_design"
    DETAILED_DESIGN = "detailed_design"
    ANALYSIS = "analysis"
    OPTIMIZATION = "optimization"
    VALIDATION = "validation"
    MANUFACTURING_PREP = "manufacturing_prep"
    DELIVERY = "delivery"


class DecisionPoint(Enum):
    """Key decision points requiring user input"""
    APPROVE_REQUIREMENTS = "approve_requirements"
    SELECT_CONCEPT = "select_concept"
    APPROVE_DESIGN = "approve_design"
    PROCEED_TO_OPTIMIZATION = "proceed_to_optimization"
    ACCEPT_FINAL_DESIGN = "accept_final_design"


@dataclass
class WorkflowState:
    """Current state of the R&D workflow"""
    current_stage: WorkflowStage
    completed_stages: List[WorkflowStage] = field(default_factory=list)
    pending_decisions: List[DecisionPoint] = field(default_factory=list)
    iteration_count: int = 0
    user_feedback: List[str] = field(default_factory=list)
    design_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class IterationResult:
    """Result of a design iteration"""
    iteration_number: int
    designs_generated: int
    improvements: Dict[str, float]
    convergence_metric: float
    user_feedback_incorporated: List[str]
    next_actions: List[str]


class RDWorkflow:
    """
    User-driven R&D workflow manager
    Guides through iterative design process with user collaboration
    """
    
    def __init__(self):
        self.state = WorkflowState(current_stage=WorkflowStage.REQUIREMENTS)
        self.max_iterations = 10
        self.convergence_threshold = 0.95
        
        # Manufacturing constraints
        self.manufacturing_constraints = {
            'min_wall_thickness_mm': 2.0,
            'max_chamber_pressure_mpa': 35.0,
            'available_materials': ['Inconel 718', 'SS 316L', 'Niobium C-103'],
            'manufacturing_methods': ['CNC machining', 'Additive manufacturing', 'Casting'],
            'tolerance_class': 'aerospace_grade',
            'surface_finish_ra_um': 1.6
        }
        
        # Cost constraints
        self.cost_constraints = {
            'max_development_cost_usd': 10_000_000,
            'max_unit_cost_usd': 2_000_000,
            'target_production_volume': 10,
            'cost_optimization_priority': 0.3  # 0-1 scale
        }
    
    def start_workflow(self, user_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Start the R&D workflow"""
        logger.info("Starting R&D workflow")
        
        self.state.current_stage = WorkflowStage.REQUIREMENTS
        
        # Parse and validate requirements
        validated_requirements = self._validate_requirements(user_requirements)
        
        # Check for missing information
        missing_info = self._identify_missing_requirements(validated_requirements)
        
        if missing_info:
            return {
                'stage': 'requirements',
                'status': 'incomplete',
                'validated_requirements': validated_requirements,
                'missing_information': missing_info,
                'questions': self._generate_clarifying_questions(missing_info),
                'next_action': 'provide_missing_requirements'
            }
        
        # Requirements complete, move to concept
        self.state.completed_stages.append(WorkflowStage.REQUIREMENTS)
        self.state.current_stage = WorkflowStage.CONCEPT
        
        return {
            'stage': 'requirements',
            'status': 'complete',
            'validated_requirements': validated_requirements,
            'next_stage': 'concept',
            'next_action': 'generate_concepts'
        }
    
    def generate_concepts(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate multiple design concepts"""
        logger.info("Generating design concepts")
        
        self.state.current_stage = WorkflowStage.CONCEPT
        
        # This would integrate with MultiDesignSystem
        concepts = {
            'concept_count': 3,
            'concepts': [
                {
                    'id': 'concept_1',
                    'name': 'Conservative Approach',
                    'description': 'Proven technology, low risk',
                    'key_features': ['LOX/RP-1', 'Moderate pressure', 'Simple geometry']
                },
                {
                    'id': 'concept_2',
                    'name': 'Balanced Approach',
                    'description': 'Modern design, good performance',
                    'key_features': ['LOX/CH4', 'High pressure', 'Optimized nozzle']
                },
                {
                    'id': 'concept_3',
                    'name': 'High Performance',
                    'description': 'Maximum efficiency, higher complexity',
                    'key_features': ['LOX/LH2', 'Very high pressure', 'Advanced cooling']
                }
            ],
            'decision_point': DecisionPoint.SELECT_CONCEPT,
            'next_action': 'user_selects_concept'
        }
        
        self.state.pending_decisions.append(DecisionPoint.SELECT_CONCEPT)
        
        return concepts
    
    def develop_preliminary_design(self, selected_concept: str,
                                   user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Develop preliminary design from selected concept"""
        logger.info(f"Developing preliminary design from {selected_concept}")
        
        self.state.current_stage = WorkflowStage.PRELIMINARY_DESIGN
        self.state.completed_stages.append(WorkflowStage.CONCEPT)
        
        # Generate preliminary design
        preliminary_design = {
            'design_id': f"prelim_{selected_concept}",
            'based_on_concept': selected_concept,
            'parameters': {},  # Would be filled by design generation
            'performance_estimates': {},
            'manufacturing_assessment': self._assess_manufacturability({}),
            'cost_estimate': self._estimate_costs({}),
            'risk_assessment': 'preliminary',
            'next_action': 'run_analysis'
        }
        
        return preliminary_design
    
    def run_detailed_analysis(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """Run comprehensive analysis on design"""
        logger.info("Running detailed analysis")
        
        self.state.current_stage = WorkflowStage.ANALYSIS
        
        analysis_results = {
            'physics_validation': {},  # Would integrate with Physics Agent
            'stress_analysis': {},     # Would integrate with simulation
            'thermal_analysis': {},
            'failure_analysis': {},    # Would integrate with Failure Analysis Engine
            'manufacturing_analysis': self._detailed_manufacturing_analysis(design),
            'cost_analysis': self._detailed_cost_analysis(design),
            'performance_predictions': {},
            'recommendations': [],
            'decision_point': DecisionPoint.APPROVE_DESIGN,
            'next_action': 'user_reviews_analysis'
        }
        
        self.state.pending_decisions.append(DecisionPoint.APPROVE_DESIGN)
        
        return analysis_results
    
    def optimize_design(self, design: Dict[str, Any],
                       optimization_goals: Dict[str, float]) -> IterationResult:
        """Run optimization iteration"""
        logger.info(f"Running optimization iteration {self.state.iteration_count + 1}")
        
        self.state.current_stage = WorkflowStage.OPTIMIZATION
        self.state.iteration_count += 1
        
        # This would integrate with optimization agents
        improvements = {
            'isp_improvement_percent': 2.5,
            'mass_reduction_percent': 3.0,
            'cost_reduction_percent': 1.5
        }
        
        convergence = self._calculate_convergence(improvements)
        
        result = IterationResult(
            iteration_number=self.state.iteration_count,
            designs_generated=5,
            improvements=improvements,
            convergence_metric=convergence,
            user_feedback_incorporated=self.state.user_feedback[-3:],
            next_actions=self._determine_next_actions(convergence)
        )
        
        # Store in history
        self.state.design_history.append({
            'iteration': self.state.iteration_count,
            'design': design,
            'improvements': improvements,
            'timestamp': time.time()
        })
        
        return result
    
    def refine_design(self, design: Dict[str, Any],
                     user_feedback: str) -> Dict[str, Any]:
        """Refine design based on user feedback"""
        logger.info("Refining design based on user feedback")
        
        self.state.user_feedback.append(user_feedback)
        
        # Parse feedback and adjust design
        refinements = self._parse_user_feedback(user_feedback)
        
        refined_design = design.copy()
        # Apply refinements
        
        return {
            'refined_design': refined_design,
            'changes_made': refinements,
            'next_action': 'run_analysis'
        }
    
    def prepare_for_manufacturing(self, final_design: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare design for manufacturing"""
        logger.info("Preparing design for manufacturing")
        
        self.state.current_stage = WorkflowStage.MANUFACTURING_PREP
        
        manufacturing_package = {
            'design_drawings': 'generated',
            'material_specifications': self._generate_material_specs(final_design),
            'manufacturing_instructions': self._generate_manufacturing_instructions(final_design),
            'quality_control_plan': self._generate_qc_plan(final_design),
            'test_plan': self._generate_test_plan(final_design),
            'bill_of_materials': self._generate_bom(final_design),
            'cost_breakdown': self._detailed_cost_breakdown(final_design),
            'timeline': self._estimate_timeline(final_design),
            'next_action': 'deliver_package'
        }
        
        return manufacturing_package
    
    def deliver_final_package(self, manufacturing_package: Dict[str, Any]) -> Dict[str, Any]:
        """Deliver final engineering package"""
        logger.info("Delivering final engineering package")
        
        self.state.current_stage = WorkflowStage.DELIVERY
        self.state.completed_stages.append(WorkflowStage.MANUFACTURING_PREP)
        
        final_package = {
            'status': 'complete',
            'design_documentation': manufacturing_package,
            'performance_summary': {},
            'risk_summary': {},
            'cost_summary': {},
            'timeline_summary': {},
            'recommendations': [
                'Proceed with prototype manufacturing',
                'Conduct design review with manufacturing team',
                'Begin test planning and facility preparation'
            ],
            'next_steps': [
                'Manufacture prototype',
                'Conduct qualification testing',
                'Iterate based on test results'
            ]
        }
        
        return final_package
    
    def _validate_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and structure requirements"""
        validated = {
            'mission_profile': requirements.get('mission_profile', 'general'),
            'performance_targets': requirements.get('performance_targets', {}),
            'constraints': requirements.get('constraints', {}),
            'priorities': requirements.get('priorities', {}),
            'manufacturing_constraints': self.manufacturing_constraints,
            'cost_constraints': self.cost_constraints
        }
        
        return validated
    
    def _identify_missing_requirements(self, requirements: Dict[str, Any]) -> List[str]:
        """Identify missing critical requirements"""
        missing = []
        
        if not requirements.get('performance_targets'):
            missing.append('performance_targets')
        
        if not requirements.get('priorities'):
            missing.append('optimization_priorities')
        
        return missing
    
    def _generate_clarifying_questions(self, missing_info: List[str]) -> List[str]:
        """Generate questions to gather missing information"""
        questions = []
        
        if 'performance_targets' in missing_info:
            questions.extend([
                "What is your target thrust level?",
                "Do you have a minimum ISP requirement?",
                "What is the operating environment (sea level, vacuum, variable)?"
            ])
        
        if 'optimization_priorities' in missing_info:
            questions.append(
                "What are your priorities? (e.g., performance, cost, reliability, schedule)"
            )
        
        return questions
    
    def _assess_manufacturability(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """Assess manufacturing feasibility"""
        return {
            'feasibility': 'high',
            'recommended_method': 'Additive manufacturing + CNC finishing',
            'complexity_score': 6.5,  # 1-10
            'lead_time_weeks': 12,
            'special_requirements': ['Vacuum heat treatment', 'Precision boring']
        }
    
    def _estimate_costs(self, design: Dict[str, Any]) -> Dict[str, float]:
        """Estimate development and production costs"""
        return {
            'development_cost_usd': 3_500_000,
            'unit_cost_usd': 1_200_000,
            'tooling_cost_usd': 500_000,
            'testing_cost_usd': 800_000
        }
    
    def _detailed_manufacturing_analysis(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """Detailed manufacturing analysis"""
        return {
            'critical_dimensions': ['Chamber throat diameter', 'Nozzle contour'],
            'tight_tolerances': ['±0.05mm on throat', '±0.1mm on chamber'],
            'surface_finish_requirements': {
                'chamber_inner': 'Ra 0.8 μm',
                'nozzle_throat': 'Ra 0.4 μm'
            },
            'heat_treatment': 'Solution anneal + age hardening',
            'inspection_requirements': ['CMM measurement', 'X-ray inspection', 'Pressure test'],
            'manufacturing_risks': [
                'Throat erosion during machining',
                'Distortion during heat treatment'
            ]
        }
    
    def _detailed_cost_analysis(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """Detailed cost breakdown"""
        return {
            'material_cost': 150_000,
            'machining_cost': 400_000,
            'heat_treatment_cost': 50_000,
            'coating_cost': 80_000,
            'inspection_cost': 60_000,
            'assembly_cost': 100_000,
            'testing_cost': 200_000,
            'overhead': 160_000,
            'total_unit_cost': 1_200_000,
            'cost_drivers': [
                'Precision machining of nozzle contour',
                'Inconel 718 material cost',
                'Extensive testing requirements'
            ]
        }
    
    def _calculate_convergence(self, improvements: Dict[str, float]) -> float:
        """Calculate convergence metric"""
        # If improvements are small, we're converging
        avg_improvement = sum(improvements.values()) / len(improvements)
        
        # Convergence increases as improvements decrease
        convergence = 1.0 - (avg_improvement / 10.0)
        
        return max(0.0, min(1.0, convergence))
    
    def _determine_next_actions(self, convergence: float) -> List[str]:
        """Determine next actions based on convergence"""
        if convergence > self.convergence_threshold:
            return [
                'Design has converged',
                'Proceed to final validation',
                'Prepare manufacturing package'
            ]
        elif self.state.iteration_count >= self.max_iterations:
            return [
                'Maximum iterations reached',
                'Review current best design',
                'Decide: continue optimization or proceed with current design'
            ]
        else:
            return [
                'Continue optimization',
                f'Run iteration {self.state.iteration_count + 1}',
                'Incorporate latest improvements'
            ]
    
    def _parse_user_feedback(self, feedback: str) -> List[str]:
        """Parse user feedback into actionable refinements"""
        refinements = []
        
        feedback_lower = feedback.lower()
        
        if 'increase' in feedback_lower and 'thrust' in feedback_lower:
            refinements.append('Increase chamber pressure by 10%')
        
        if 'reduce' in feedback_lower and 'cost' in feedback_lower:
            refinements.append('Simplify geometry to reduce manufacturing cost')
        
        if 'improve' in feedback_lower and 'isp' in feedback_lower:
            refinements.append('Increase expansion ratio')
        
        return refinements
    
    def _generate_material_specs(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """Generate material specifications"""
        return {
            'chamber_material': {
                'specification': 'Inconel 718 per AMS 5662',
                'condition': 'Solution treated and aged',
                'properties': {
                    'yield_strength_mpa': 1100,
                    'ultimate_strength_mpa': 1300,
                    'elongation_percent': 12
                }
            },
            'nozzle_material': {
                'specification': 'Niobium C-103 per AMS 7872',
                'condition': 'Stress relieved',
                'coating': 'Silicide coating for oxidation protection'
            }
        }
    
    def _generate_manufacturing_instructions(self, design: Dict[str, Any]) -> List[str]:
        """Generate manufacturing instructions"""
        return [
            "1. Machine chamber from solid billet using 5-axis CNC",
            "2. Precision bore throat to final dimension",
            "3. Solution anneal at 980°C, water quench",
            "4. Age harden at 720°C for 8 hours",
            "5. Final grind and polish internal surfaces",
            "6. Apply thermal barrier coating if specified",
            "7. Inspect per quality control plan",
            "8. Hydrostatic pressure test to 1.5x design pressure"
        ]
    
    def _generate_qc_plan(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """Generate quality control plan"""
        return {
            'incoming_inspection': ['Material certification', 'Chemical analysis'],
            'in_process_inspection': ['Dimensional checks at key stages', 'Surface finish measurement'],
            'final_inspection': [
                'CMM measurement of critical dimensions',
                'Surface finish verification',
                'X-ray inspection for internal defects',
                'Pressure test to 1.5x design pressure',
                'Leak test at operating pressure'
            ],
            'acceptance_criteria': {
                'dimensional_tolerance': '±0.1mm on non-critical, ±0.05mm on critical',
                'surface_finish': 'Ra < 1.6 μm',
                'pressure_test': 'Hold 1.5x design pressure for 5 minutes, no leaks',
                'leak_rate': '< 1e-6 mbar·L/s'
            }
        }
    
    def _generate_test_plan(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test plan"""
        return {
            'development_tests': [
                'Cold flow testing',
                'Ignition sequence testing',
                'Short-duration hot-fire (5s)',
                'Nominal duration hot-fire (30s)',
                'Extended duration hot-fire (60s)'
            ],
            'qualification_tests': [
                'Performance mapping',
                'Thermal cycling (10 cycles)',
                'Vibration testing',
                'Long-duration endurance (300s)',
                'Off-nominal conditions testing'
            ],
            'instrumentation': [
                'Chamber pressure (multiple locations)',
                'Thrust measurement',
                'Temperature (chamber, nozzle, coolant)',
                'Flow rates (oxidizer, fuel)',
                'High-speed video',
                'Acoustic sensors'
            ]
        }
    
    def _generate_bom(self, design: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate bill of materials"""
        return [
            {'part': 'Chamber assembly', 'material': 'Inconel 718', 'qty': 1, 'cost_usd': 80000},
            {'part': 'Nozzle assembly', 'material': 'Niobium C-103', 'qty': 1, 'cost_usd': 120000},
            {'part': 'Injector', 'material': 'SS 316L', 'qty': 1, 'cost_usd': 45000},
            {'part': 'Cooling channels', 'material': 'Copper', 'qty': 1, 'cost_usd': 25000},
            {'part': 'Fasteners', 'material': 'Titanium', 'qty': 24, 'cost_usd': 5000},
            {'part': 'Seals', 'material': 'Graphite', 'qty': 6, 'cost_usd': 3000}
        ]
    
    def _detailed_cost_breakdown(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """Detailed cost breakdown"""
        return self._detailed_cost_analysis(design)
    
    def _estimate_timeline(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate development timeline"""
        return {
            'design_finalization': '4 weeks',
            'material_procurement': '8 weeks',
            'manufacturing': '12 weeks',
            'assembly': '2 weeks',
            'inspection_and_test': '6 weeks',
            'total_lead_time': '32 weeks',
            'critical_path': ['Material procurement', 'Precision machining', 'Heat treatment'],
            'parallel_activities': ['Test stand preparation', 'Instrumentation setup']
        }
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status"""
        return {
            'current_stage': self.state.current_stage.value,
            'completed_stages': [s.value for s in self.state.completed_stages],
            'pending_decisions': [d.value for d in self.state.pending_decisions],
            'iteration_count': self.state.iteration_count,
            'progress_percent': (len(self.state.completed_stages) / len(WorkflowStage)) * 100
        }
