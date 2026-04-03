"""
KÁNU Intelligence Orchestrator
Full R&D Department accessible through chat
Integrates all components into a cohesive engineering intelligence system
"""
from typing import Dict, Any, List, Optional
import logging
import time

from .conversational_layer import ConversationalReasoning, ConversationPhase, EngineeringDialogue
from .multi_design_system import MultiDesignSystem, DesignProposal, DesignComparison
from .failure_analysis import FailureAnalysisEngine, FMEAReport
from .rd_workflow import RDWorkflow, WorkflowStage

# Import from kanu-llm if available
try:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / 'kanu-llm'))
    from memory.memory_system import MemorySystem
    from agents.intent_agent import IntentAgent
    from agents.physics_agent import PhysicsAgent
    from agents.design_agent import DesignAgent
    from agents.critic_agent import CriticAgent
    from core.message import MessageBus
except ImportError:
    logging.warning("KÁNU-LLM components not available, using simplified mode")
    MemorySystem = None
    MessageBus = None

logger = logging.getLogger(__name__)


class KANUIntelligence:
    """
    Full Engineering Intelligence System
    Behaves like a complete R&D department accessible through chat
    """
    
    def __init__(self, enable_advanced_agents: bool = True):
        # Core components
        self.conversational = ConversationalReasoning()
        self.multi_design = MultiDesignSystem(target_count=3)
        self.failure_analysis = FailureAnalysisEngine()
        self.workflow = RDWorkflow()
        
        # Advanced components (if available)
        self.enable_advanced_agents = enable_advanced_agents and MessageBus is not None
        
        if self.enable_advanced_agents:
            self.message_bus = MessageBus()
            self.memory = MemorySystem()
            self._initialize_agents()
        else:
            self.message_bus = None
            self.memory = None
            self.agents = {}
        
        # Session state
        self.current_designs: List[DesignProposal] = []
        self.current_comparison: Optional[DesignComparison] = None
        self.current_fmea: Optional[FMEAReport] = None
        self.conversation_history: List[EngineeringDialogue] = []
        
        logger.info("KÁNU Intelligence System initialized")
    
    def _initialize_agents(self):
        """Initialize multi-agent system"""
        self.agents = {
            'intent': IntentAgent('intent', self.message_bus),
            'physics': PhysicsAgent('physics', self.message_bus, rust_bridge=None),
            'design': DesignAgent('design', self.message_bus, self.memory),
            'critic': CriticAgent('critic', self.message_bus)
        }
        logger.info("Multi-agent system initialized")
    
    def chat(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main chat interface - process user message and generate response
        This is the primary entry point for conversational interaction
        """
        logger.info(f"Processing user message: {user_message[:100]}...")
        
        start_time = time.time()
        
        # Step 1: Process through conversational layer
        dialogue = self.conversational.process_user_input(user_message, context)
        self.conversation_history.append(dialogue)
        
        # Step 2: Determine what action to take based on conversation phase
        phase = self.conversational.context.phase
        
        response = {
            'message': dialogue.content,
            'phase': phase.value,
            'technical_depth': dialogue.technical_depth,
            'questions': dialogue.questions_asked,
            'insights': dialogue.insights_shared,
            'concerns': dialogue.concerns_raised,
            'recommendations': dialogue.recommendations,
            'elapsed_time': time.time() - start_time
        }
        
        # Step 3: Execute appropriate actions based on phase
        if phase == ConversationPhase.PROPOSAL:
            # User is ready for design proposals
            if 'ready' in user_message.lower() or 'yes' in user_message.lower():
                design_result = self._generate_and_present_designs(context or {})
                response['designs'] = design_result
                response['action'] = 'designs_generated'
        
        elif phase == ConversationPhase.REFINEMENT:
            # User wants to refine a design
            if self.current_designs:
                refinement_result = self._refine_designs(user_message)
                response['refinement'] = refinement_result
                response['action'] = 'design_refined'
        
        elif phase == ConversationPhase.VALIDATION:
            # User wants validation and analysis
            if self.current_designs:
                validation_result = self._validate_and_analyze()
                response['validation'] = validation_result
                response['action'] = 'validation_complete'
        
        # Step 4: Add workflow status
        response['workflow_status'] = self.workflow.get_workflow_status()
        
        # Step 5: Add conversation summary
        response['conversation_summary'] = self.conversational.get_conversation_summary()
        
        return response
    
    def _generate_and_present_designs(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate multiple design proposals and present them"""
        logger.info("Generating design portfolio")
        
        # Extract constraints from conversation context
        constraints = self.conversational.context.constraints_clarified
        
        # Generate designs
        proposals = self.multi_design.generate_design_portfolio(
            requirements=requirements,
            constraints=constraints
        )
        
        self.current_designs = proposals
        
        # Run initial analysis on each
        for proposal in proposals:
            # Predict performance
            proposal.predicted_performance = {
                'isp': self.multi_design._predict_isp(proposal.parameters),
                'thrust': self.multi_design._predict_thrust(proposal.parameters)
            }
        
        # Compare designs
        comparison = self.multi_design.compare_designs()
        self.current_comparison = comparison
        
        return {
            'proposals': [self._format_proposal(p) for p in proposals],
            'comparison': self._format_comparison(comparison),
            'recommendation': comparison.recommendation
        }
    
    def _refine_designs(self, user_feedback: str) -> Dict[str, Any]:
        """Refine designs based on user feedback"""
        logger.info("Refining designs based on feedback")
        
        if not self.current_designs:
            return {'error': 'No designs to refine'}
        
        # Use workflow to refine
        best_design = max(self.current_designs, key=lambda d: d.overall_score)
        
        refinement = self.workflow.refine_design(
            design=best_design.parameters,
            user_feedback=user_feedback
        )
        
        # Re-run analysis
        self._validate_and_analyze()
        
        return refinement
    
    def _validate_and_analyze(self) -> Dict[str, Any]:
        """Run comprehensive validation and analysis"""
        logger.info("Running comprehensive validation and analysis")
        
        if not self.current_designs:
            return {'error': 'No designs to validate'}
        
        results = []
        
        for proposal in self.current_designs:
            # Run failure analysis
            fmea = self.failure_analysis.analyze_design(
                design_parameters=proposal.parameters,
                simulation_results=proposal.simulation_results
            )
            
            # Store FMEA
            if proposal.overall_score == max(d.overall_score for d in self.current_designs):
                self.current_fmea = fmea
            
            results.append({
                'design_id': proposal.design_id,
                'design_name': proposal.name,
                'fmea_summary': {
                    'overall_risk_score': fmea.overall_risk_score,
                    'critical_failures': len(fmea.critical_failures),
                    'top_risks': [f.failure_mode.value for f in fmea.failure_analyses[:3]]
                },
                'recommendations': fmea.recommendations[:3]
            })
        
        return {
            'validation_results': results,
            'detailed_fmea': self.failure_analysis.generate_fmea_report(self.current_fmea) if self.current_fmea else None
        }
    
    def _format_proposal(self, proposal: DesignProposal) -> Dict[str, Any]:
        """Format design proposal for presentation"""
        return {
            'id': proposal.design_id,
            'name': proposal.name,
            'description': proposal.description,
            'key_parameters': {
                'propellant': proposal.parameters.get('propellant_name'),
                'chamber_pressure_mpa': proposal.parameters.get('chamber_pressure_pa', 0) / 1e6,
                'expansion_ratio': proposal.parameters.get('expansion_ratio'),
            },
            'predicted_performance': {
                'isp_s': proposal.predicted_performance.get('isp', 0),
                'thrust_kn': proposal.predicted_performance.get('thrust', 0) / 1000
            },
            'strengths': proposal.strengths[:3],
            'weaknesses': proposal.weaknesses[:2],
            'cost_estimate_usd': proposal.estimated_cost_usd,
            'manufacturing_complexity': proposal.manufacturing_complexity,
            'overall_score': proposal.overall_score,
            'rationale': proposal.design_rationale
        }
    
    def _format_comparison(self, comparison: DesignComparison) -> Dict[str, Any]:
        """Format design comparison for presentation"""
        return {
            'comparison_matrix': comparison.comparison_matrix,
            'trade_offs': comparison.trade_offs,
            'winner_id': comparison.winner_id
        }
    
    def start_rd_project(self, project_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Start a full R&D project workflow"""
        logger.info("Starting R&D project workflow")
        
        # Initialize workflow
        workflow_result = self.workflow.start_workflow(project_requirements)
        
        # Update conversation context
        self.conversational.context.constraints_clarified = workflow_result.get('validated_requirements', {})
        
        return workflow_result
    
    def iterate_design(self, optimization_goals: Dict[str, float]) -> Dict[str, Any]:
        """Run a design iteration with optimization"""
        logger.info("Running design iteration")
        
        if not self.current_designs:
            return {'error': 'No designs to iterate on'}
        
        best_design = max(self.current_designs, key=lambda d: d.overall_score)
        
        iteration_result = self.workflow.optimize_design(
            design=best_design.parameters,
            optimization_goals=optimization_goals
        )
        
        return {
            'iteration': iteration_result.iteration_number,
            'improvements': iteration_result.improvements,
            'convergence': iteration_result.convergence_metric,
            'next_actions': iteration_result.next_actions
        }
    
    def prepare_manufacturing_package(self) -> Dict[str, Any]:
        """Prepare final manufacturing package"""
        logger.info("Preparing manufacturing package")
        
        if not self.current_designs:
            return {'error': 'No designs available'}
        
        best_design = max(self.current_designs, key=lambda d: d.overall_score)
        
        manufacturing_package = self.workflow.prepare_for_manufacturing(
            final_design=best_design.parameters
        )
        
        return manufacturing_package
    
    def deliver_final_package(self) -> Dict[str, Any]:
        """Deliver complete engineering package"""
        logger.info("Delivering final engineering package")
        
        manufacturing_package = self.prepare_manufacturing_package()
        
        final_package = self.workflow.deliver_final_package(manufacturing_package)
        
        # Add design summary
        if self.current_designs:
            best_design = max(self.current_designs, key=lambda d: d.overall_score)
            final_package['selected_design'] = self._format_proposal(best_design)
        
        # Add FMEA summary
        if self.current_fmea:
            final_package['risk_analysis'] = {
                'overall_risk_score': self.current_fmea.overall_risk_score,
                'critical_failures': len(self.current_fmea.critical_failures),
                'recommendations': self.current_fmea.recommendations
            }
        
        return final_package
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            'conversation_phase': self.conversational.context.phase.value,
            'workflow_stage': self.workflow.state.current_stage.value,
            'designs_generated': len(self.current_designs),
            'iterations_completed': self.workflow.state.iteration_count,
            'conversation_turns': len(self.conversation_history)
        }
        
        if self.enable_advanced_agents:
            status['agent_performance'] = {
                agent_id: agent.get_performance_stats()
                for agent_id, agent in self.agents.items()
            }
        
        if self.current_comparison:
            status['best_design_score'] = max(
                self.current_comparison.comparison_matrix.get('Overall Score', [0])
            )
        
        if self.current_fmea:
            status['risk_score'] = self.current_fmea.overall_risk_score
        
        return status
    
    def export_conversation_log(self) -> str:
        """Export full conversation log"""
        log = "# KÁNU Engineering Conversation Log\n\n"
        
        for i, dialogue in enumerate(self.conversation_history, 1):
            log += f"## Turn {i}\n"
            log += f"**Speaker:** {dialogue.speaker}\n"
            if dialogue.persona:
                log += f"**Persona:** {dialogue.persona.value}\n"
            log += f"**Technical Depth:** {dialogue.technical_depth}/10\n\n"
            log += f"{dialogue.content}\n\n"
            
            if dialogue.questions_asked:
                log += "**Questions:**\n"
                for q in dialogue.questions_asked:
                    log += f"- {q}\n"
                log += "\n"
            
            if dialogue.insights_shared:
                log += "**Insights:**\n"
                for insight in dialogue.insights_shared:
                    log += f"- {insight}\n"
                log += "\n"
            
            log += "---\n\n"
        
        return log
    
    def export_engineering_report(self) -> str:
        """Export comprehensive engineering report"""
        report = "# KÁNU Engineering Report\n\n"
        report += f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Executive Summary
        report += "## Executive Summary\n\n"
        if self.current_designs:
            best = max(self.current_designs, key=lambda d: d.overall_score)
            report += f"**Recommended Design:** {best.name}\n"
            report += f"**Overall Score:** {best.overall_score:.1f}/100\n"
            report += f"**Estimated Cost:** ${best.estimated_cost_usd/1e6:.2f}M\n\n"
        
        # Design Proposals
        report += "## Design Proposals\n\n"
        for i, design in enumerate(self.current_designs, 1):
            report += f"### Design {i}: {design.name}\n"
            report += f"{design.description}\n\n"
            report += f"**Rationale:** {design.design_rationale}\n\n"
            
            report += "**Strengths:**\n"
            for strength in design.strengths[:3]:
                report += f"- {strength}\n"
            report += "\n"
            
            report += "**Predicted Performance:**\n"
            report += f"- ISP: {design.predicted_performance.get('isp', 0):.0f} s\n"
            report += f"- Thrust: {design.predicted_performance.get('thrust', 0)/1000:.0f} kN\n\n"
        
        # Comparison
        if self.current_comparison:
            report += "## Design Comparison\n\n"
            report += self.current_comparison.recommendation
            report += "\n\n"
        
        # Risk Analysis
        if self.current_fmea:
            report += "## Risk Analysis\n\n"
            report += self.failure_analysis.generate_fmea_report(self.current_fmea)
            report += "\n"
        
        # Workflow Status
        report += "## Project Status\n\n"
        workflow_status = self.workflow.get_workflow_status()
        report += f"**Current Stage:** {workflow_status['current_stage']}\n"
        report += f"**Progress:** {workflow_status['progress_percent']:.0f}%\n"
        report += f"**Iterations:** {workflow_status['iteration_count']}\n\n"
        
        # Next Steps
        report += "## Next Steps\n\n"
        if self.current_comparison:
            report += "1. Review and approve recommended design\n"
            report += "2. Run detailed stress tests and simulations\n"
            report += "3. Address critical failure modes\n"
            report += "4. Proceed to manufacturing preparation\n"
        
        return report


def create_intelligence_system(enable_advanced: bool = True) -> KANUIntelligence:
    """Factory function to create KÁNU Intelligence System"""
    return KANUIntelligence(enable_advanced_agents=enable_advanced)
