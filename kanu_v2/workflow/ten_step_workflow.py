"""
Strict 10-Step User Workflow for KÁNU V2
Ensures systematic, physics-first design process
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import time

logger = logging.getLogger(__name__)


class WorkflowStep(Enum):
    """10 mandatory workflow steps"""
    STEP_1_UNDERSTAND = "understand_request"
    STEP_2_CLARIFY = "ask_clarifying_questions"
    STEP_3_PROPOSE_CONCEPTS = "propose_2_3_concepts"
    STEP_4_USER_VALIDATION = "wait_user_validation"
    STEP_5_GENERATE_DESIGNS = "generate_3_5_designs"
    STEP_6_SIMULATE_TEST = "simulate_and_test"
    STEP_7_RANK_EXPLAIN = "rank_and_explain"
    STEP_8_USER_CHOICE = "let_user_choose"
    STEP_9_DEEP_OPTIMIZE = "deep_optimize_chosen"
    STEP_10_DELIVER_PACKAGE = "deliver_engineering_package"


@dataclass
class WorkflowState:
    """Current state in the workflow"""
    current_step: WorkflowStep
    completed_steps: List[WorkflowStep] = field(default_factory=list)
    user_inputs: Dict[str, Any] = field(default_factory=dict)
    generated_concepts: List[Dict[str, Any]] = field(default_factory=list)
    generated_designs: List[Dict[str, Any]] = field(default_factory=list)
    simulation_results: List[Dict[str, Any]] = field(default_factory=list)
    chosen_design: Optional[Dict[str, Any]] = None
    optimized_design: Optional[Dict[str, Any]] = None
    final_package: Optional[Dict[str, Any]] = None
    
    # Tracking
    start_time: float = field(default_factory=time.time)
    step_times: Dict[str, float] = field(default_factory=dict)


class TenStepWorkflow:
    """
    Strict 10-step workflow manager
    Ensures KÁNU follows systematic process
    """
    
    def __init__(self):
        self.state = WorkflowState(current_step=WorkflowStep.STEP_1_UNDERSTAND)
        self.anti_hallucination_checks = []
    
    # ============================================================
    # STEP 1: Understand Request Deeply
    # ============================================================
    
    def step_1_understand_request(self, user_request: str) -> Dict[str, Any]:
        """
        STEP 1: Understand the request deeply
        Decompose problem, identify key requirements
        """
        logger.info("STEP 1: Understanding request deeply")
        self._mark_step_start(WorkflowStep.STEP_1_UNDERSTAND)
        
        # Decompose request
        decomposition = self._decompose_request(user_request)
        
        # Extract requirements
        requirements = self._extract_requirements(user_request)
        
        # Identify constraints
        constraints = self._identify_constraints(user_request)
        
        # Identify uncertainties
        uncertainties = self._identify_uncertainties(user_request)
        
        # Store in state
        self.state.user_inputs['original_request'] = user_request
        self.state.user_inputs['decomposition'] = decomposition
        self.state.user_inputs['requirements'] = requirements
        self.state.user_inputs['constraints'] = constraints
        self.state.user_inputs['uncertainties'] = uncertainties
        
        # Move to next step
        self._complete_step(WorkflowStep.STEP_1_UNDERSTAND)
        self.state.current_step = WorkflowStep.STEP_2_CLARIFY
        
        return {
            'step': 1,
            'status': 'complete',
            'decomposition': decomposition,
            'requirements': requirements,
            'constraints': constraints,
            'uncertainties': uncertainties,
            'next_step': 'clarify' if uncertainties else 'propose_concepts'
        }
    
    def _decompose_request(self, request: str) -> List[str]:
        """Decompose request into sub-problems"""
        sub_problems = []
        
        request_lower = request.lower()
        
        if 'design' in request_lower:
            sub_problems.extend([
                'Define performance requirements',
                'Select propellant combination',
                'Determine operating conditions',
                'Choose materials',
                'Design geometry',
                'Validate physics'
            ])
        
        if 'optimize' in request_lower:
            sub_problems.extend([
                'Define optimization objectives',
                'Identify design variables',
                'Set constraints'
            ])
        
        return sub_problems
    
    def _extract_requirements(self, request: str) -> Dict[str, Any]:
        """Extract explicit requirements"""
        requirements = {}
        
        # Look for thrust requirements
        if 'kn' in request.lower():
            # Extract number before kN
            import re
            match = re.search(r'(\d+)\s*kn', request.lower())
            if match:
                requirements['thrust_kn'] = float(match.group(1))
        
        # Look for ISP requirements
        if 'isp' in request.lower():
            match = re.search(r'isp.*?(\d+)', request.lower())
            if match:
                requirements['isp_min'] = float(match.group(1))
        
        # Look for propellant
        propellants = ['lox/rp-1', 'lox/lh2', 'lox/ch4', 'lox/methane']
        for prop in propellants:
            if prop in request.lower():
                requirements['propellant'] = prop.upper().replace('METHANE', 'CH4')
        
        # Look for environment
        if 'vacuum' in request.lower():
            requirements['environment'] = 'vacuum'
        elif 'sea level' in request.lower():
            requirements['environment'] = 'sea_level'
        
        return requirements
    
    def _identify_constraints(self, request: str) -> Dict[str, Any]:
        """Identify constraints"""
        constraints = {}
        
        # Cost constraints
        if 'budget' in request.lower() or 'cost' in request.lower():
            import re
            match = re.search(r'\$(\d+)m', request.lower())
            if match:
                constraints['max_cost_usd'] = float(match.group(1)) * 1e6
        
        # Mass constraints
        if 'lightweight' in request.lower():
            constraints['minimize_mass'] = True
        
        return constraints
    
    def _identify_uncertainties(self, request: str) -> List[str]:
        """Identify what's unclear or missing"""
        uncertainties = []
        
        requirements = self.state.user_inputs.get('requirements', {})
        
        if 'thrust_kn' not in requirements:
            uncertainties.append("Target thrust level not specified")
        
        if 'environment' not in requirements:
            uncertainties.append("Operating environment (vacuum/sea level) not specified")
        
        if 'propellant' not in requirements:
            uncertainties.append("Propellant preference not specified")
        
        return uncertainties
    
    # ============================================================
    # STEP 2: Ask Clarifying Questions
    # ============================================================
    
    def step_2_ask_clarifying_questions(self) -> Dict[str, Any]:
        """
        STEP 2: Ask clarifying questions if needed
        """
        logger.info("STEP 2: Asking clarifying questions")
        self._mark_step_start(WorkflowStep.STEP_2_CLARIFY)
        
        uncertainties = self.state.user_inputs.get('uncertainties', [])
        
        if not uncertainties:
            # No questions needed, skip to step 3
            self._complete_step(WorkflowStep.STEP_2_CLARIFY)
            self.state.current_step = WorkflowStep.STEP_3_PROPOSE_CONCEPTS
            return {
                'step': 2,
                'status': 'skipped',
                'reason': 'No clarification needed',
                'next_step': 'propose_concepts'
            }
        
        # Generate questions
        questions = self._generate_questions(uncertainties)
        
        return {
            'step': 2,
            'status': 'waiting_for_user',
            'questions': questions,
            'uncertainties': uncertainties,
            'next_step': 'user_must_answer'
        }
    
    def _generate_questions(self, uncertainties: List[str]) -> List[str]:
        """Generate specific questions"""
        questions = []
        
        for uncertainty in uncertainties:
            if 'thrust' in uncertainty.lower():
                questions.append("What is your target thrust level? (e.g., 50 kN, 100 kN)")
            
            elif 'environment' in uncertainty.lower():
                questions.append("What is the operating environment? (vacuum, sea level, or variable altitude)")
            
            elif 'propellant' in uncertainty.lower():
                questions.append("Do you have a propellant preference? (LOX/RP-1, LOX/LH2, LOX/CH4)")
        
        return questions
    
    def step_2_receive_answers(self, answers: Dict[str, Any]):
        """Receive answers to clarifying questions"""
        self.state.user_inputs.update(answers)
        
        # Update requirements
        if 'requirements' not in self.state.user_inputs:
            self.state.user_inputs['requirements'] = {}
        
        self.state.user_inputs['requirements'].update(answers)
        
        # Clear uncertainties
        self.state.user_inputs['uncertainties'] = []
        
        # Complete step 2
        self._complete_step(WorkflowStep.STEP_2_CLARIFY)
        self.state.current_step = WorkflowStep.STEP_3_PROPOSE_CONCEPTS
    
    # ============================================================
    # STEP 3: Propose 2-3 Realistic Concept Directions
    # ============================================================
    
    def step_3_propose_concepts(self) -> Dict[str, Any]:
        """
        STEP 3: Propose 2-3 realistic concept directions
        ANTI-HALLUCINATION: Only propose physically possible concepts
        """
        logger.info("STEP 3: Proposing concept directions")
        self._mark_step_start(WorkflowStep.STEP_3_PROPOSE_CONCEPTS)
        
        requirements = self.state.user_inputs.get('requirements', {})
        
        # Generate concepts
        concepts = self._generate_concepts(requirements)
        
        # ANTI-HALLUCINATION CHECK: Validate each concept
        validated_concepts = []
        for concept in concepts:
            if self._validate_concept_physics(concept):
                validated_concepts.append(concept)
            else:
                logger.warning(f"Concept {concept['name']} failed physics validation - REJECTED")
        
        self.state.generated_concepts = validated_concepts
        
        # Move to step 4 (wait for user)
        self.state.current_step = WorkflowStep.STEP_4_USER_VALIDATION
        
        return {
            'step': 3,
            'status': 'complete',
            'concepts': validated_concepts,
            'next_step': 'user_validation'
        }
    
    def _generate_concepts(self, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate 2-3 concept directions"""
        concepts = []
        
        # Concept 1: Conservative
        concepts.append({
            'id': 'concept_conservative',
            'name': 'Conservative Approach',
            'description': 'Proven technology, low risk, moderate performance',
            'propellant': 'LOX/RP-1',
            'pressure_range_mpa': (10, 18),
            'complexity': 'low',
            'risk': 'low',
            'performance': 'moderate',
            'rationale': 'Uses flight-proven LOX/RP-1 with conservative pressures for maximum reliability'
        })
        
        # Concept 2: Balanced
        concepts.append({
            'id': 'concept_balanced',
            'name': 'Balanced Modern Approach',
            'description': 'Modern design balancing performance and practicality',
            'propellant': requirements.get('propellant', 'LOX/CH4'),
            'pressure_range_mpa': (18, 25),
            'complexity': 'medium',
            'risk': 'medium',
            'performance': 'good',
            'rationale': 'Modern propellant with good performance and reasonable complexity'
        })
        
        # Concept 3: High Performance (only if requirements demand it)
        if requirements.get('isp_min', 0) > 400 or requirements.get('environment') == 'vacuum':
            concepts.append({
                'id': 'concept_high_performance',
                'name': 'High Performance Approach',
                'description': 'Maximum efficiency, higher complexity',
                'propellant': 'LOX/LH2',
                'pressure_range_mpa': (20, 28),
                'complexity': 'high',
                'risk': 'medium-high',
                'performance': 'excellent',
                'rationale': 'LOX/LH2 for maximum ISP, suitable for vacuum applications'
            })
        
        return concepts
    
    def _validate_concept_physics(self, concept: Dict[str, Any]) -> bool:
        """
        ANTI-HALLUCINATION: Validate concept is physically possible
        """
        # Check pressure range is realistic
        pressure_range = concept.get('pressure_range_mpa', (0, 0))
        if pressure_range[1] > 35:
            logger.error(f"Pressure {pressure_range[1]} MPa exceeds practical limits")
            return False
        
        # Check propellant is real
        valid_propellants = ['LOX/RP-1', 'LOX/LH2', 'LOX/CH4']
        if concept.get('propellant') not in valid_propellants:
            logger.error(f"Invalid propellant: {concept.get('propellant')}")
            return False
        
        # All checks passed
        return True
    
    # ============================================================
    # STEP 4: Wait for User Validation
    # ============================================================
    
    def step_4_wait_user_validation(self) -> Dict[str, Any]:
        """
        STEP 4: Wait for user to select a concept
        """
        logger.info("STEP 4: Waiting for user validation")
        
        return {
            'step': 4,
            'status': 'waiting_for_user',
            'message': 'Please select one of the proposed concepts to proceed',
            'concepts': self.state.generated_concepts,
            'next_step': 'user_must_select'
        }
    
    def step_4_receive_selection(self, selected_concept_id: str):
        """Receive user's concept selection"""
        selected = next((c for c in self.state.generated_concepts 
                        if c['id'] == selected_concept_id), None)
        
        if not selected:
            raise ValueError(f"Invalid concept ID: {selected_concept_id}")
        
        self.state.user_inputs['selected_concept'] = selected
        
        # Complete step 4
        self._complete_step(WorkflowStep.STEP_4_USER_VALIDATION)
        self.state.current_step = WorkflowStep.STEP_5_GENERATE_DESIGNS
    
    # ============================================================
    # STEP 5: Generate Multiple Engineering Designs (3-5)
    # ============================================================
    
    def step_5_generate_designs(self, design_generator) -> Dict[str, Any]:
        """
        STEP 5: Generate 3-5 detailed engineering designs
        Uses multi-design system
        """
        logger.info("STEP 5: Generating 3-5 detailed designs")
        self._mark_step_start(WorkflowStep.STEP_5_GENERATE_DESIGNS)
        
        selected_concept = self.state.user_inputs.get('selected_concept', {})
        requirements = self.state.user_inputs.get('requirements', {})
        
        # Generate designs using design generator
        designs = design_generator.generate_design_portfolio(
            requirements=requirements,
            constraints={'concept': selected_concept},
            count=3
        )
        
        # ANTI-HALLUCINATION: Validate each design
        validated_designs = []
        for design in designs:
            validation = self._validate_design_physics(design)
            if validation['valid']:
                validated_designs.append(design)
            else:
                logger.warning(f"Design {design.design_id} REJECTED: {validation['violations']}")
        
        self.state.generated_designs = validated_designs
        
        # Move to step 6
        self._complete_step(WorkflowStep.STEP_5_GENERATE_DESIGNS)
        self.state.current_step = WorkflowStep.STEP_6_SIMULATE_TEST
        
        return {
            'step': 5,
            'status': 'complete',
            'designs_generated': len(validated_designs),
            'designs': validated_designs,
            'next_step': 'simulate_and_test'
        }
    
    def _validate_design_physics(self, design) -> Dict[str, Any]:
        """Validate design against physics"""
        violations = []
        
        params = design.parameters
        
        # Check material temperature limits
        material = params.get('chamber_material', '')
        material_limits = {
            'Inconel 718': 980,
            'SS 316L': 870,
            'Niobium C-103': 1370
        }
        
        chamber_temp = 3500  # Typical combustion temp
        if material in material_limits and chamber_temp > material_limits[material]:
            if not params.get('regenerative_cooling'):
                violations.append(f"Temperature exceeds {material} limit without cooling")
        
        # Check structural integrity
        pressure = params.get('chamber_pressure_pa', 0)
        radius = params.get('chamber_radius_m', 0)
        thickness = params.get('wall_thickness_m', 0)
        
        if thickness > 0:
            hoop_stress = (pressure * radius) / thickness
            yield_strengths = {
                'Inconel 718': 1100e6,
                'SS 316L': 290e6,
                'Niobium C-103': 345e6
            }
            
            if material in yield_strengths:
                if hoop_stress > yield_strengths[material]:
                    violations.append("Hoop stress exceeds yield strength")
        
        return {
            'valid': len(violations) == 0,
            'violations': violations
        }
    
    # ============================================================
    # STEP 6: Simulate and Test Each Design
    # ============================================================
    
    def step_6_simulate_and_test(self, world_model) -> Dict[str, Any]:
        """
        STEP 6: Run comprehensive simulations on each design
        """
        logger.info("STEP 6: Simulating and testing designs")
        self._mark_step_start(WorkflowStep.STEP_6_SIMULATE_TEST)
        
        simulation_results = []
        
        for design in self.state.generated_designs:
            # Multi-scenario simulation
            scenarios = world_model.simulate_multi_scenario(design.parameters)
            
            # Monte Carlo analysis
            monte_carlo = world_model.monte_carlo_analysis(design.parameters, num_runs=500)
            
            # Failure-first testing
            failure_points = world_model.failure_first_testing(design.parameters)
            
            result = {
                'design_id': design.design_id,
                'scenarios': scenarios,
                'monte_carlo': monte_carlo,
                'failure_points': failure_points,
                'overall_success_rate': monte_carlo.success_rate
            }
            
            simulation_results.append(result)
        
        self.state.simulation_results = simulation_results
        
        # Move to step 7
        self._complete_step(WorkflowStep.STEP_6_SIMULATE_TEST)
        self.state.current_step = WorkflowStep.STEP_7_RANK_EXPLAIN
        
        return {
            'step': 6,
            'status': 'complete',
            'simulation_results': simulation_results,
            'next_step': 'rank_and_explain'
        }
    
    # ============================================================
    # STEP 7: Rank and Explain Results
    # ============================================================
    
    def step_7_rank_and_explain(self) -> Dict[str, Any]:
        """
        STEP 7: Rank designs and explain results clearly
        """
        logger.info("STEP 7: Ranking and explaining results")
        self._mark_step_start(WorkflowStep.STEP_7_RANK_EXPLAIN)
        
        # Rank designs
        ranked_designs = self._rank_designs()
        
        # Generate explanations
        explanations = self._generate_explanations(ranked_designs)
        
        # Move to step 8
        self._complete_step(WorkflowStep.STEP_7_RANK_EXPLAIN)
        self.state.current_step = WorkflowStep.STEP_8_USER_CHOICE
        
        return {
            'step': 7,
            'status': 'complete',
            'ranked_designs': ranked_designs,
            'explanations': explanations,
            'next_step': 'user_choice'
        }
    
    def _rank_designs(self) -> List[Dict[str, Any]]:
        """Rank designs by overall score"""
        scored_designs = []
        
        for i, design in enumerate(self.state.generated_designs):
            sim_result = self.state.simulation_results[i]
            
            # Calculate overall score
            score = self._calculate_overall_score(design, sim_result)
            
            scored_designs.append({
                'design': design,
                'simulation': sim_result,
                'overall_score': score
            })
        
        # Sort by score
        scored_designs.sort(key=lambda x: x['overall_score'], reverse=True)
        
        return scored_designs
    
    def _calculate_overall_score(self, design, sim_result) -> float:
        """Calculate overall design score"""
        score = 0.0
        
        # Success rate (40 points)
        score += sim_result['overall_success_rate'] * 40
        
        # Performance (30 points)
        mc = sim_result['monte_carlo']
        isp = mc.mean_performance.get('isp_s', 0)
        score += min((isp / 450) * 30, 30)
        
        # Cost (20 points)
        cost = design.estimated_cost_usd
        score += max(0, 20 - (cost / 1e6) * 4)
        
        # Manufacturing (10 points)
        complexity_scores = {'low': 10, 'medium': 7, 'high': 4}
        score += complexity_scores.get(design.manufacturing_complexity, 5)
        
        return min(100, score)
    
    def _generate_explanations(self, ranked_designs: List[Dict[str, Any]]) -> List[str]:
        """Generate clear explanations"""
        explanations = []
        
        for i, item in enumerate(ranked_designs, 1):
            design = item['design']
            sim = item['simulation']
            score = item['overall_score']
            
            exp = f"**Design {i}: {design.name}** (Score: {score:.1f}/100)\n\n"
            exp += f"Success Rate: {sim['overall_success_rate']*100:.1f}%\n"
            exp += f"Performance: ISP {sim['monte_carlo'].mean_performance.get('isp_s', 0):.0f}s\n"
            exp += f"Cost: ${design.estimated_cost_usd/1e6:.2f}M\n"
            exp += f"Manufacturing: {design.manufacturing_complexity}\n\n"
            exp += f"Rationale: {design.design_rationale}\n"
            
            explanations.append(exp)
        
        return explanations
    
    # ============================================================
    # STEP 8: Let User Choose One
    # ============================================================
    
    def step_8_let_user_choose(self) -> Dict[str, Any]:
        """
        STEP 8: Present ranked designs and let user choose
        """
        logger.info("STEP 8: Waiting for user to choose design")
        
        return {
            'step': 8,
            'status': 'waiting_for_user',
            'message': 'Please select one design to optimize',
            'next_step': 'user_must_choose'
        }
    
    def step_8_receive_choice(self, chosen_design_id: str):
        """Receive user's design choice"""
        ranked = self._rank_designs()
        
        chosen = next((item for item in ranked 
                      if item['design'].design_id == chosen_design_id), None)
        
        if not chosen:
            raise ValueError(f"Invalid design ID: {chosen_design_id}")
        
        self.state.chosen_design = chosen
        
        # Complete step 8
        self._complete_step(WorkflowStep.STEP_8_USER_CHOICE)
        self.state.current_step = WorkflowStep.STEP_9_DEEP_OPTIMIZE
    
    # ============================================================
    # STEP 9: Deep Optimize Chosen Design
    # ============================================================
    
    def step_9_deep_optimize(self, optimizer) -> Dict[str, Any]:
        """
        STEP 9: Deep optimization of chosen design
        """
        logger.info("STEP 9: Deep optimizing chosen design")
        self._mark_step_start(WorkflowStep.STEP_9_DEEP_OPTIMIZE)
        
        chosen = self.state.chosen_design
        
        # Run optimization
        optimized = optimizer.optimize(
            initial_design=chosen['design'].parameters,
            objectives=['maximize_isp', 'minimize_cost', 'maximize_reliability'],
            max_iterations=50
        )
        
        self.state.optimized_design = optimized
        
        # Move to step 10
        self._complete_step(WorkflowStep.STEP_9_DEEP_OPTIMIZE)
        self.state.current_step = WorkflowStep.STEP_10_DELIVER_PACKAGE
        
        return {
            'step': 9,
            'status': 'complete',
            'optimized_design': optimized,
            'improvements': optimized.get('improvements', {}),
            'next_step': 'deliver_package'
        }
    
    # ============================================================
    # STEP 10: Deliver Full Engineering Package
    # ============================================================
    
    def step_10_deliver_package(self) -> Dict[str, Any]:
        """
        STEP 10: Deliver complete engineering-ready package
        """
        logger.info("STEP 10: Delivering full engineering package")
        self._mark_step_start(WorkflowStep.STEP_10_DELIVER_PACKAGE)
        
        optimized = self.state.optimized_design
        
        # Generate complete package
        package = {
            'concept_explanation': self._generate_concept_explanation(),
            'technical_architecture': self._generate_technical_architecture(optimized),
            'performance_estimates': self._generate_performance_estimates(optimized),
            'trade_offs': self._generate_trade_offs(),
            'failure_risks': self._generate_failure_risks(optimized),
            'cost_estimation': self._generate_cost_estimation(optimized),
            'manufacturing_constraints': self._generate_manufacturing_constraints(optimized),
            'materials_suggestions': self._generate_materials_suggestions(optimized),
            'assembly_guidelines': self._generate_assembly_guidelines(optimized),
            'simulation_summaries': self._generate_simulation_summaries(),
            'test_plan': self._generate_test_plan(optimized)
        }
        
        self.state.final_package = package
        
        # Complete workflow
        self._complete_step(WorkflowStep.STEP_10_DELIVER_PACKAGE)
        
        total_time = time.time() - self.state.start_time
        
        return {
            'step': 10,
            'status': 'complete',
            'package': package,
            'workflow_complete': True,
            'total_time_seconds': total_time
        }
    
    def _generate_concept_explanation(self) -> str:
        """Generate concept explanation"""
        concept = self.state.user_inputs.get('selected_concept', {})
        return f"# Concept: {concept.get('name', 'Unknown')}\n\n{concept.get('rationale', '')}"
    
    def _generate_technical_architecture(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """Generate technical architecture"""
        return {
            'propulsion_system': 'Liquid rocket engine',
            'propellant': design.get('propellant_name', 'Unknown'),
            'chamber_pressure_mpa': design.get('chamber_pressure_pa', 0) / 1e6,
            'expansion_ratio': design.get('expansion_ratio', 0),
            'cooling_system': 'Regenerative' if design.get('regenerative_cooling') else 'Film',
            'materials': {
                'chamber': design.get('chamber_material', 'Unknown'),
                'nozzle': design.get('nozzle_material', 'Unknown')
            }
        }
    
    def _generate_performance_estimates(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance estimates"""
        sim_results = self.state.simulation_results
        if sim_results:
            mc = sim_results[0]['monte_carlo']
            return {
                'isp_mean_s': mc.mean_performance.get('isp_s', 0),
                'isp_std_s': mc.std_performance.get('isp_s', 0),
                'thrust_mean_kn': mc.mean_performance.get('thrust_n', 0) / 1000,
                'success_rate': mc.success_rate
            }
        return {}
    
    def _generate_trade_offs(self) -> List[str]:
        """Generate trade-offs"""
        return [
            "Higher ISP requires more complex propellant handling",
            "Higher chamber pressure increases performance but reduces safety margin",
            "Lighter materials reduce mass but may limit temperature capability"
        ]
    
    def _generate_failure_risks(self, design: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate failure risks"""
        return [
            {'mode': 'Combustion instability', 'severity': 'high', 'likelihood': 'low'},
            {'mode': 'Thermal fatigue', 'severity': 'medium', 'likelihood': 'medium'},
            {'mode': 'Cooling failure', 'severity': 'high', 'likelihood': 'low'}
        ]
    
    def _generate_cost_estimation(self, design: Dict[str, Any]) -> Dict[str, float]:
        """Generate cost estimation"""
        return {
            'development_cost_usd': 3_500_000,
            'unit_cost_usd': 1_200_000,
            'testing_cost_usd': 800_000,
            'total_program_cost_usd': 5_500_000
        }
    
    def _generate_manufacturing_constraints(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """Generate manufacturing constraints"""
        return {
            'min_wall_thickness_mm': 2.0,
            'tolerance_class': 'Aerospace grade (±0.05mm)',
            'surface_finish': 'Ra < 1.6 μm',
            'methods': ['5-axis CNC machining', 'Precision boring', 'Heat treatment']
        }
    
    def _generate_materials_suggestions(self, design: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate materials suggestions"""
        return [
            {'component': 'Chamber', 'material': 'Inconel 718', 'reason': 'High temperature strength'},
            {'component': 'Nozzle', 'material': 'Niobium C-103', 'reason': 'Extreme temperature capability'},
            {'component': 'Injector', 'material': 'SS 316L', 'reason': 'Corrosion resistance'}
        ]
    
    def _generate_assembly_guidelines(self, design: Dict[str, Any]) -> List[str]:
        """Generate assembly guidelines"""
        return [
            "1. Inspect all components per QC plan",
            "2. Clean all surfaces with isopropyl alcohol",
            "3. Install chamber-nozzle interface with torque spec 150 Nm",
            "4. Install injector with alignment pins",
            "5. Pressure test to 1.5x design pressure",
            "6. Leak test at operating pressure"
        ]
    
    def _generate_simulation_summaries(self) -> str:
        """Generate simulation summaries"""
        summary = "# Simulation Summary\n\n"
        
        for result in self.state.simulation_results:
            summary += f"## Design {result['design_id']}\n"
            summary += f"Success Rate: {result['overall_success_rate']*100:.1f}%\n"
            summary += f"Scenarios Tested: {len(result['scenarios'])}\n"
            summary += f"Monte Carlo Runs: {result['monte_carlo'].num_runs}\n\n"
        
        return summary
    
    def _generate_test_plan(self, design: Dict[str, Any]) -> List[str]:
        """Generate test plan"""
        return [
            "Phase 1: Component testing (injector, chamber, nozzle)",
            "Phase 2: Cold flow testing",
            "Phase 3: Short-duration hot-fire (5s)",
            "Phase 4: Nominal duration hot-fire (30s)",
            "Phase 5: Extended duration (60s)",
            "Phase 6: Thermal cycling (10 cycles)",
            "Phase 7: Qualification testing"
        ]
    
    # ============================================================
    # Helper Methods
    # ============================================================
    
    def _mark_step_start(self, step: WorkflowStep):
        """Mark step start time"""
        self.state.step_times[step.value] = time.time()
    
    def _complete_step(self, step: WorkflowStep):
        """Mark step as complete"""
        self.state.completed_steps.append(step)
        
        if step.value in self.state.step_times:
            elapsed = time.time() - self.state.step_times[step.value]
            logger.info(f"Step {step.value} completed in {elapsed:.2f}s")
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status"""
        return {
            'current_step': self.state.current_step.value,
            'completed_steps': [s.value for s in self.state.completed_steps],
            'progress_percent': (len(self.state.completed_steps) / 10) * 100,
            'elapsed_time': time.time() - self.state.start_time
        }
