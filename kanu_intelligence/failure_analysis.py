"""
Failure Analysis Engine
Identifies potential failure modes and provides mitigation strategies
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class FailureMode(Enum):
    """Common rocket engine failure modes"""
    COMBUSTION_INSTABILITY = "combustion_instability"
    THERMAL_FATIGUE = "thermal_fatigue"
    MATERIAL_CREEP = "material_creep"
    COOLING_FAILURE = "cooling_failure"
    STRUCTURAL_FAILURE = "structural_failure"
    IGNITION_FAILURE = "ignition_failure"
    TURBOPUMP_FAILURE = "turbopump_failure"
    INJECTOR_CLOGGING = "injector_clogging"
    NOZZLE_EROSION = "nozzle_erosion"
    SEAL_FAILURE = "seal_failure"


class Severity(Enum):
    """Failure severity levels"""
    CATASTROPHIC = 5  # Loss of mission/vehicle
    CRITICAL = 4      # Major performance degradation
    MAJOR = 3         # Significant impact
    MINOR = 2         # Marginal impact
    NEGLIGIBLE = 1    # Minimal impact


class Likelihood(Enum):
    """Failure likelihood"""
    FREQUENT = 5      # Expected to occur
    PROBABLE = 4      # Will occur several times
    OCCASIONAL = 3    # Likely to occur sometime
    REMOTE = 2        # Unlikely but possible
    IMPROBABLE = 1    # So unlikely, can be assumed not to occur


@dataclass
class FailureAnalysis:
    """Analysis of a specific failure mode"""
    failure_mode: FailureMode
    description: str
    severity: Severity
    likelihood: Likelihood
    risk_priority_number: int  # Severity * Likelihood
    
    # Root causes
    root_causes: List[str] = field(default_factory=list)
    
    # Effects
    effects: List[str] = field(default_factory=list)
    
    # Detection methods
    detection_methods: List[str] = field(default_factory=list)
    
    # Mitigation strategies
    mitigation_strategies: List[str] = field(default_factory=list)
    
    # Design recommendations
    design_recommendations: List[str] = field(default_factory=list)
    
    # Testing requirements
    testing_requirements: List[str] = field(default_factory=list)


@dataclass
class FMEAReport:
    """Failure Modes and Effects Analysis Report"""
    design_id: str
    design_parameters: Dict[str, Any]
    failure_analyses: List[FailureAnalysis]
    overall_risk_score: float
    critical_failures: List[FailureAnalysis]
    recommendations: List[str]


class FailureAnalysisEngine:
    """
    Comprehensive failure analysis engine
    Performs FMEA (Failure Modes and Effects Analysis)
    """
    
    def __init__(self):
        self.failure_database = self._build_failure_database()
        self.mitigation_library = self._build_mitigation_library()
    
    def analyze_design(self, design_parameters: Dict[str, Any],
                      simulation_results: Optional[Dict[str, Any]] = None) -> FMEAReport:
        """
        Perform comprehensive failure analysis on a design
        """
        design_id = design_parameters.get('design_id', 'unknown')
        logger.info(f"Performing FMEA on design {design_id}")
        
        failure_analyses = []
        
        # Analyze each potential failure mode
        for failure_mode in FailureMode:
            analysis = self._analyze_failure_mode(
                failure_mode,
                design_parameters,
                simulation_results
            )
            
            if analysis:
                failure_analyses.append(analysis)
        
        # Sort by risk priority
        failure_analyses.sort(key=lambda x: x.risk_priority_number, reverse=True)
        
        # Identify critical failures (RPN > 12)
        critical_failures = [f for f in failure_analyses if f.risk_priority_number > 12]
        
        # Calculate overall risk score
        overall_risk = self._calculate_overall_risk(failure_analyses)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(failure_analyses, design_parameters)
        
        return FMEAReport(
            design_id=design_id,
            design_parameters=design_parameters,
            failure_analyses=failure_analyses,
            overall_risk_score=overall_risk,
            critical_failures=critical_failures,
            recommendations=recommendations
        )
    
    def _analyze_failure_mode(self, failure_mode: FailureMode,
                             design_parameters: Dict[str, Any],
                             simulation_results: Optional[Dict[str, Any]]) -> Optional[FailureAnalysis]:
        """Analyze a specific failure mode"""
        
        # Get failure mode template
        template = self.failure_database.get(failure_mode)
        if not template:
            return None
        
        # Assess severity and likelihood based on design
        severity = self._assess_severity(failure_mode, design_parameters)
        likelihood = self._assess_likelihood(failure_mode, design_parameters, simulation_results)
        
        # Calculate RPN
        rpn = severity.value * likelihood.value
        
        # Get applicable mitigations
        mitigations = self._get_applicable_mitigations(failure_mode, design_parameters)
        
        # Get design recommendations
        recommendations = self._get_design_recommendations(failure_mode, design_parameters)
        
        # Get testing requirements
        testing = self._get_testing_requirements(failure_mode, design_parameters)
        
        return FailureAnalysis(
            failure_mode=failure_mode,
            description=template['description'],
            severity=severity,
            likelihood=likelihood,
            risk_priority_number=rpn,
            root_causes=template['root_causes'],
            effects=template['effects'],
            detection_methods=template['detection_methods'],
            mitigation_strategies=mitigations,
            design_recommendations=recommendations,
            testing_requirements=testing
        )
    
    def _assess_severity(self, failure_mode: FailureMode,
                        design_parameters: Dict[str, Any]) -> Severity:
        """Assess failure severity"""
        
        # Catastrophic failures
        if failure_mode in [FailureMode.COMBUSTION_INSTABILITY,
                           FailureMode.STRUCTURAL_FAILURE,
                           FailureMode.COOLING_FAILURE]:
            return Severity.CATASTROPHIC
        
        # Critical failures
        elif failure_mode in [FailureMode.TURBOPUMP_FAILURE,
                             FailureMode.IGNITION_FAILURE]:
            return Severity.CRITICAL
        
        # Major failures
        elif failure_mode in [FailureMode.THERMAL_FATIGUE,
                             FailureMode.MATERIAL_CREEP,
                             FailureMode.NOZZLE_EROSION]:
            return Severity.MAJOR
        
        # Minor failures
        else:
            return Severity.MINOR
    
    def _assess_likelihood(self, failure_mode: FailureMode,
                          design_parameters: Dict[str, Any],
                          simulation_results: Optional[Dict[str, Any]]) -> Likelihood:
        """Assess failure likelihood based on design characteristics"""
        
        chamber_pressure_mpa = design_parameters.get('chamber_pressure_pa', 0) / 1e6
        material = design_parameters.get('chamber_material', '')
        propellant = design_parameters.get('propellant_name', '')
        
        # Combustion instability
        if failure_mode == FailureMode.COMBUSTION_INSTABILITY:
            chamber_length = design_parameters.get('chamber_length_m', 1.0)
            if chamber_length < 0.5:
                return Likelihood.PROBABLE
            elif chamber_pressure_mpa > 25:
                return Likelihood.OCCASIONAL
            else:
                return Likelihood.REMOTE
        
        # Thermal fatigue
        elif failure_mode == FailureMode.THERMAL_FATIGUE:
            if chamber_pressure_mpa > 20:
                return Likelihood.PROBABLE
            elif chamber_pressure_mpa > 15:
                return Likelihood.OCCASIONAL
            else:
                return Likelihood.REMOTE
        
        # Material creep
        elif failure_mode == FailureMode.MATERIAL_CREEP:
            if material in ['Copper', 'Aluminum']:
                return Likelihood.OCCASIONAL
            else:
                return Likelihood.REMOTE
        
        # Cooling failure
        elif failure_mode == FailureMode.COOLING_FAILURE:
            if chamber_pressure_mpa > 20 and 'cooling' not in str(design_parameters).lower():
                return Likelihood.PROBABLE
            elif chamber_pressure_mpa > 15:
                return Likelihood.OCCASIONAL
            else:
                return Likelihood.REMOTE
        
        # Structural failure
        elif failure_mode == FailureMode.STRUCTURAL_FAILURE:
            wall_thickness = design_parameters.get('wall_thickness_m', 0.005)
            if wall_thickness < 0.003:
                return Likelihood.OCCASIONAL
            else:
                return Likelihood.REMOTE
        
        # Nozzle erosion
        elif failure_mode == FailureMode.NOZZLE_EROSION:
            if 'RP-1' in propellant:
                return Likelihood.OCCASIONAL
            else:
                return Likelihood.REMOTE
        
        # Default
        else:
            return Likelihood.REMOTE
    
    def _get_applicable_mitigations(self, failure_mode: FailureMode,
                                   design_parameters: Dict[str, Any]) -> List[str]:
        """Get applicable mitigation strategies"""
        mitigations = self.mitigation_library.get(failure_mode, [])
        
        # Filter based on design
        applicable = []
        for mitigation in mitigations:
            if self._is_mitigation_applicable(mitigation, design_parameters):
                applicable.append(mitigation['strategy'])
        
        return applicable
    
    def _is_mitigation_applicable(self, mitigation: Dict[str, Any],
                                 design_parameters: Dict[str, Any]) -> bool:
        """Check if mitigation is applicable to this design"""
        # Simplified - in production would have more sophisticated logic
        return True
    
    def _get_design_recommendations(self, failure_mode: FailureMode,
                                   design_parameters: Dict[str, Any]) -> List[str]:
        """Get design recommendations to reduce failure risk"""
        recommendations = []
        
        chamber_pressure_mpa = design_parameters.get('chamber_pressure_pa', 0) / 1e6
        
        if failure_mode == FailureMode.COMBUSTION_INSTABILITY:
            recommendations.extend([
                "Increase chamber length to L/D > 3 for stable combustion",
                "Use acoustic dampers or baffles if pressure > 20 MPa",
                "Implement multi-element injector design"
            ])
        
        elif failure_mode == FailureMode.THERMAL_FATIGUE:
            recommendations.extend([
                "Implement regenerative cooling with propellant",
                "Use thermal barrier coatings on hot surfaces",
                "Design for thermal expansion with flexible joints"
            ])
        
        elif failure_mode == FailureMode.COOLING_FAILURE:
            recommendations.extend([
                "Add redundant cooling channels",
                "Use film cooling at critical hot spots",
                "Monitor coolant flow and temperature in real-time"
            ])
        
        elif failure_mode == FailureMode.STRUCTURAL_FAILURE:
            recommendations.extend([
                f"Increase wall thickness to minimum 4mm for {chamber_pressure_mpa:.0f} MPa",
                "Add structural ribs or stiffeners",
                "Use higher-strength materials (Inconel 718 or better)"
            ])
        
        return recommendations
    
    def _get_testing_requirements(self, failure_mode: FailureMode,
                                  design_parameters: Dict[str, Any]) -> List[str]:
        """Get testing requirements for this failure mode"""
        testing = []
        
        if failure_mode == FailureMode.COMBUSTION_INSTABILITY:
            testing.extend([
                "Hot-fire testing with instrumented chamber pressure",
                "High-frequency pressure transducers (>10 kHz)",
                "Acoustic analysis of combustion chamber"
            ])
        
        elif failure_mode == FailureMode.THERMAL_FATIGUE:
            testing.extend([
                "Thermal cycling tests (100+ cycles)",
                "Thermal imaging during hot-fire",
                "Post-test metallurgical inspection"
            ])
        
        elif failure_mode == FailureMode.STRUCTURAL_FAILURE:
            testing.extend([
                "Hydrostatic pressure testing to 1.5x design pressure",
                "Burst testing on qualification units",
                "Non-destructive testing (X-ray, ultrasonic)"
            ])
        
        return testing
    
    def _calculate_overall_risk(self, failure_analyses: List[FailureAnalysis]) -> float:
        """Calculate overall risk score (0-100)"""
        if not failure_analyses:
            return 0.0
        
        # Weight by RPN
        total_weighted_risk = sum(f.risk_priority_number for f in failure_analyses)
        max_possible_risk = len(failure_analyses) * 25  # Max RPN = 5*5
        
        risk_score = (total_weighted_risk / max_possible_risk) * 100
        
        return min(100, risk_score)
    
    def _generate_recommendations(self, failure_analyses: List[FailureAnalysis],
                                 design_parameters: Dict[str, Any]) -> List[str]:
        """Generate overall recommendations"""
        recommendations = []
        
        # Focus on high-risk items
        critical = [f for f in failure_analyses if f.risk_priority_number > 12]
        
        if critical:
            recommendations.append(
                f"Address {len(critical)} critical failure modes before proceeding"
            )
            
            for failure in critical[:3]:  # Top 3
                recommendations.append(
                    f"Mitigate {failure.failure_mode.value}: {failure.mitigation_strategies[0] if failure.mitigation_strategies else 'Review design'}"
                )
        
        # General recommendations
        chamber_pressure_mpa = design_parameters.get('chamber_pressure_pa', 0) / 1e6
        if chamber_pressure_mpa > 25:
            recommendations.append(
                "Very high chamber pressure - consider comprehensive testing program"
            )
        
        recommendations.append(
            "Implement design review with cross-functional team"
        )
        
        recommendations.append(
            "Develop detailed test plan addressing all major failure modes"
        )
        
        return recommendations
    
    def _build_failure_database(self) -> Dict[FailureMode, Dict[str, Any]]:
        """Build database of failure modes"""
        return {
            FailureMode.COMBUSTION_INSTABILITY: {
                'description': 'Unstable combustion causing pressure oscillations',
                'root_causes': [
                    'Acoustic coupling in chamber',
                    'Improper injector design',
                    'Inadequate chamber length',
                    'Propellant mixing issues'
                ],
                'effects': [
                    'Structural vibration and fatigue',
                    'Reduced performance',
                    'Potential catastrophic failure',
                    'Injector damage'
                ],
                'detection_methods': [
                    'High-frequency pressure sensors',
                    'Acoustic monitoring',
                    'Vibration sensors',
                    'Visual inspection for damage'
                ]
            },
            FailureMode.THERMAL_FATIGUE: {
                'description': 'Cyclic thermal loading causing material fatigue',
                'root_causes': [
                    'Repeated thermal cycling',
                    'High temperature gradients',
                    'Inadequate cooling',
                    'Material selection'
                ],
                'effects': [
                    'Crack initiation and propagation',
                    'Reduced structural integrity',
                    'Potential leakage',
                    'Shortened service life'
                ],
                'detection_methods': [
                    'Thermal imaging',
                    'Crack detection (dye penetrant, X-ray)',
                    'Strain gauges',
                    'Cycle counting'
                ]
            },
            FailureMode.COOLING_FAILURE: {
                'description': 'Inadequate cooling leading to overheating',
                'root_causes': [
                    'Coolant flow blockage',
                    'Insufficient coolant flow rate',
                    'Cooling channel design flaws',
                    'Pump failure'
                ],
                'effects': [
                    'Material melting or softening',
                    'Structural failure',
                    'Catastrophic engine failure',
                    'Mission loss'
                ],
                'detection_methods': [
                    'Temperature sensors',
                    'Flow meters',
                    'Thermal imaging',
                    'Pressure monitoring'
                ]
            },
            FailureMode.STRUCTURAL_FAILURE: {
                'description': 'Mechanical failure of structural components',
                'root_causes': [
                    'Excessive pressure loads',
                    'Material defects',
                    'Inadequate wall thickness',
                    'Stress concentrations',
                    'Fatigue'
                ],
                'effects': [
                    'Catastrophic rupture',
                    'Propellant leakage',
                    'Mission failure',
                    'Vehicle loss'
                ],
                'detection_methods': [
                    'Pressure testing',
                    'Non-destructive testing',
                    'Strain gauges',
                    'Acoustic emission'
                ]
            },
            FailureMode.NOZZLE_EROSION: {
                'description': 'Erosion of nozzle material due to hot gas flow',
                'root_causes': [
                    'High gas velocity',
                    'Particulate in exhaust',
                    'Chemical attack',
                    'Inadequate material selection'
                ],
                'effects': [
                    'Performance degradation',
                    'Thrust loss',
                    'Nozzle geometry change',
                    'Potential failure'
                ],
                'detection_methods': [
                    'Visual inspection',
                    'Dimensional measurement',
                    'Performance monitoring',
                    'Borescope inspection'
                ]
            }
        }
    
    def _build_mitigation_library(self) -> Dict[FailureMode, List[Dict[str, Any]]]:
        """Build library of mitigation strategies"""
        return {
            FailureMode.COMBUSTION_INSTABILITY: [
                {
                    'strategy': 'Install acoustic dampers or baffles in chamber',
                    'effectiveness': 'high',
                    'cost': 'medium'
                },
                {
                    'strategy': 'Optimize injector element design and pattern',
                    'effectiveness': 'high',
                    'cost': 'low'
                },
                {
                    'strategy': 'Increase chamber length for better mixing',
                    'effectiveness': 'medium',
                    'cost': 'medium'
                }
            ],
            FailureMode.THERMAL_FATIGUE: [
                {
                    'strategy': 'Implement regenerative cooling system',
                    'effectiveness': 'high',
                    'cost': 'high'
                },
                {
                    'strategy': 'Use thermal barrier coatings',
                    'effectiveness': 'medium',
                    'cost': 'medium'
                },
                {
                    'strategy': 'Design for controlled thermal expansion',
                    'effectiveness': 'medium',
                    'cost': 'low'
                }
            ],
            FailureMode.COOLING_FAILURE: [
                {
                    'strategy': 'Add redundant cooling channels',
                    'effectiveness': 'high',
                    'cost': 'high'
                },
                {
                    'strategy': 'Implement real-time coolant monitoring',
                    'effectiveness': 'high',
                    'cost': 'medium'
                },
                {
                    'strategy': 'Use film cooling at critical areas',
                    'effectiveness': 'medium',
                    'cost': 'medium'
                }
            ],
            FailureMode.STRUCTURAL_FAILURE: [
                {
                    'strategy': 'Increase wall thickness with safety margin',
                    'effectiveness': 'high',
                    'cost': 'low'
                },
                {
                    'strategy': 'Use higher-strength materials',
                    'effectiveness': 'high',
                    'cost': 'medium'
                },
                {
                    'strategy': 'Add structural reinforcement',
                    'effectiveness': 'medium',
                    'cost': 'medium'
                }
            ]
        }
    
    def generate_fmea_report(self, fmea: FMEAReport) -> str:
        """Generate formatted FMEA report"""
        report = "# Failure Modes and Effects Analysis (FMEA)\n\n"
        report += f"**Design ID:** {fmea.design_id}\n"
        report += f"**Overall Risk Score:** {fmea.overall_risk_score:.1f}/100\n\n"
        
        if fmea.critical_failures:
            report += f"## ⚠️ Critical Failure Modes ({len(fmea.critical_failures)})\n\n"
            for failure in fmea.critical_failures:
                report += f"### {failure.failure_mode.value.replace('_', ' ').title()}\n"
                report += f"**RPN:** {failure.risk_priority_number} "
                report += f"(Severity: {failure.severity.name}, Likelihood: {failure.likelihood.name})\n\n"
                report += f"**Description:** {failure.description}\n\n"
                
                if failure.mitigation_strategies:
                    report += "**Mitigation Strategies:**\n"
                    for strategy in failure.mitigation_strategies[:2]:
                        report += f"• {strategy}\n"
                    report += "\n"
        
        report += "## All Failure Modes\n\n"
        for failure in fmea.failure_analyses[:5]:
            report += f"- **{failure.failure_mode.value}**: RPN {failure.risk_priority_number}\n"
        
        report += "\n## Recommendations\n\n"
        for rec in fmea.recommendations:
            report += f"• {rec}\n"
        
        return report
