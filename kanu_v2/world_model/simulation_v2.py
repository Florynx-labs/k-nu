"""
World Model V2 - Advanced Simulation System
Multi-scenario testing with Monte Carlo, surrogate models, and failure-first approach
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class SimulationScenario(Enum):
    """Different simulation scenarios"""
    NOMINAL = "nominal"
    HOT_CASE = "hot_case"
    COLD_CASE = "cold_case"
    HIGH_ALTITUDE = "high_altitude"
    SEA_LEVEL = "sea_level"
    THROTTLED = "throttled"
    STARTUP = "startup"
    SHUTDOWN = "shutdown"
    THERMAL_CYCLE = "thermal_cycle"
    VIBRATION = "vibration"
    OFF_NOMINAL = "off_nominal"


@dataclass
class SimulationResult:
    """Result from a single simulation run"""
    scenario: SimulationScenario
    success: bool
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    failure_modes: List[str] = field(default_factory=list)
    stress_levels: Dict[str, float] = field(default_factory=dict)
    thermal_profile: Dict[str, float] = field(default_factory=dict)
    margin_of_safety: float = 0.0


@dataclass
class MonteCarloResults:
    """Results from Monte Carlo analysis"""
    num_runs: int
    success_rate: float
    mean_performance: Dict[str, float] = field(default_factory=dict)
    std_performance: Dict[str, float] = field(default_factory=dict)
    percentile_95: Dict[str, float] = field(default_factory=dict)
    percentile_5: Dict[str, float] = field(default_factory=dict)
    failure_distribution: Dict[str, int] = field(default_factory=dict)


class SurrogateModel:
    """
    Fast approximation model for expensive simulations
    Uses polynomial regression for quick performance estimates
    """
    
    def __init__(self, degree: int = 2):
        self.degree = degree
        self.coefficients = {}
        self.trained = False
    
    def train(self, X: np.ndarray, y: Dict[str, np.ndarray]):
        """
        Train surrogate model on simulation data
        X: (n_samples, n_features) - design parameters
        y: dict of (n_samples,) - performance metrics
        """
        logger.info(f"Training surrogate model with {X.shape[0]} samples")
        
        for metric_name, metric_values in y.items():
            # Polynomial features
            X_poly = self._polynomial_features(X)
            
            # Least squares fit
            coeffs = np.linalg.lstsq(X_poly, metric_values, rcond=None)[0]
            self.coefficients[metric_name] = coeffs
        
        self.trained = True
        logger.info("Surrogate model trained")
    
    def predict(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        """Predict performance metrics for new designs"""
        if not self.trained:
            raise ValueError("Model not trained yet")
        
        X_poly = self._polynomial_features(X)
        
        predictions = {}
        for metric_name, coeffs in self.coefficients.items():
            predictions[metric_name] = X_poly @ coeffs
        
        return predictions
    
    def _polynomial_features(self, X: np.ndarray) -> np.ndarray:
        """Generate polynomial features"""
        n_samples, n_features = X.shape
        
        # Start with bias term
        features = [np.ones(n_samples)]
        
        # Linear terms
        for i in range(n_features):
            features.append(X[:, i])
        
        # Quadratic terms
        if self.degree >= 2:
            for i in range(n_features):
                features.append(X[:, i] ** 2)
            
            # Interaction terms
            for i in range(n_features):
                for j in range(i + 1, n_features):
                    features.append(X[:, i] * X[:, j])
        
        return np.column_stack(features)


class WorldModelV2:
    """
    Advanced simulation system with multi-scenario testing,
    Monte Carlo analysis, and failure-first approach
    """
    
    def __init__(self):
        self.surrogate_model = SurrogateModel(degree=2)
        self.simulation_history: List[SimulationResult] = []
        
        # Real-world imperfections
        self.manufacturing_tolerances = {
            'wall_thickness': 0.0002,  # ±0.2mm
            'throat_radius': 0.0001,   # ±0.1mm
            'chamber_pressure': 0.05,  # ±5%
            'of_ratio': 0.02           # ±2%
        }
    
    def simulate_multi_scenario(self, design: Dict[str, Any]) -> List[SimulationResult]:
        """
        Run design through multiple scenarios
        """
        logger.info("Running multi-scenario simulation")
        
        scenarios = [
            SimulationScenario.NOMINAL,
            SimulationScenario.HOT_CASE,
            SimulationScenario.COLD_CASE,
            SimulationScenario.HIGH_ALTITUDE,
            SimulationScenario.SEA_LEVEL,
            SimulationScenario.THROTTLED,
            SimulationScenario.STARTUP,
            SimulationScenario.SHUTDOWN
        ]
        
        results = []
        for scenario in scenarios:
            result = self._simulate_scenario(design, scenario)
            results.append(result)
            self.simulation_history.append(result)
        
        return results
    
    def _simulate_scenario(self, design: Dict[str, Any], 
                          scenario: SimulationScenario) -> SimulationResult:
        """Simulate a specific scenario"""
        
        # Adjust parameters based on scenario
        adjusted_design = self._adjust_for_scenario(design, scenario)
        
        # Run physics simulation
        performance = self._calculate_performance(adjusted_design)
        stress = self._calculate_stress(adjusted_design)
        thermal = self._calculate_thermal(adjusted_design)
        
        # Check for failures
        failures = self._check_failures(adjusted_design, stress, thermal)
        
        # Calculate margin of safety
        mos = self._calculate_margin_of_safety(adjusted_design, stress)
        
        success = len(failures) == 0 and mos > 0
        
        return SimulationResult(
            scenario=scenario,
            success=success,
            performance_metrics=performance,
            failure_modes=failures,
            stress_levels=stress,
            thermal_profile=thermal,
            margin_of_safety=mos
        )
    
    def _adjust_for_scenario(self, design: Dict[str, Any], 
                            scenario: SimulationScenario) -> Dict[str, Any]:
        """Adjust design parameters for specific scenario"""
        adjusted = design.copy()
        
        if scenario == SimulationScenario.HOT_CASE:
            # Increase temperature by 10%
            adjusted['ambient_temp_k'] = design.get('ambient_temp_k', 288) * 1.1
            adjusted['chamber_pressure_pa'] = design.get('chamber_pressure_pa', 15e6) * 1.05
        
        elif scenario == SimulationScenario.COLD_CASE:
            # Decrease temperature
            adjusted['ambient_temp_k'] = design.get('ambient_temp_k', 288) * 0.9
            adjusted['chamber_pressure_pa'] = design.get('chamber_pressure_pa', 15e6) * 0.95
        
        elif scenario == SimulationScenario.HIGH_ALTITUDE:
            adjusted['ambient_pressure_pa'] = 1000  # Near vacuum
        
        elif scenario == SimulationScenario.SEA_LEVEL:
            adjusted['ambient_pressure_pa'] = 101325
        
        elif scenario == SimulationScenario.THROTTLED:
            adjusted['chamber_pressure_pa'] = design.get('chamber_pressure_pa', 15e6) * 0.7
        
        return adjusted
    
    def _calculate_performance(self, design: Dict[str, Any]) -> Dict[str, float]:
        """Calculate performance metrics"""
        # Simplified performance model
        chamber_pressure = design.get('chamber_pressure_pa', 15e6)
        throat_area = np.pi * design.get('throat_radius_m', 0.08) ** 2
        expansion_ratio = design.get('expansion_ratio', 30)
        
        # Thrust calculation (simplified)
        thrust_coefficient = 1.8  # Typical value
        thrust = chamber_pressure * throat_area * thrust_coefficient
        
        # ISP calculation (simplified)
        propellant = design.get('propellant_name', 'LOX/RP-1')
        base_isp = {
            'LOX/RP-1': 300,
            'LOX/LH2': 450,
            'LOX/CH4': 370
        }.get(propellant, 320)
        
        # Adjust for expansion ratio
        isp = base_isp * (1 + 0.1 * np.log(expansion_ratio / 30))
        
        # Thrust-to-weight
        mass_kg = design.get('mass_kg', 100)
        tw_ratio = thrust / (mass_kg * 9.81)
        
        return {
            'thrust_n': thrust,
            'isp_s': isp,
            'thrust_to_weight': tw_ratio,
            'chamber_pressure_mpa': chamber_pressure / 1e6
        }
    
    def _calculate_stress(self, design: Dict[str, Any]) -> Dict[str, float]:
        """Calculate stress levels"""
        chamber_pressure = design.get('chamber_pressure_pa', 15e6)
        chamber_radius = design.get('chamber_radius_m', 0.15)
        wall_thickness = design.get('wall_thickness_m', 0.005)
        
        # Hoop stress
        hoop_stress = (chamber_pressure * chamber_radius) / wall_thickness
        
        # Longitudinal stress
        longitudinal_stress = (chamber_pressure * chamber_radius) / (2 * wall_thickness)
        
        # Von Mises stress (simplified)
        von_mises = np.sqrt(hoop_stress**2 - hoop_stress*longitudinal_stress + longitudinal_stress**2)
        
        return {
            'hoop_stress_pa': hoop_stress,
            'longitudinal_stress_pa': longitudinal_stress,
            'von_mises_stress_pa': von_mises
        }
    
    def _calculate_thermal(self, design: Dict[str, Any]) -> Dict[str, float]:
        """Calculate thermal profile"""
        # Simplified thermal model
        chamber_temp = 3500  # Combustion temperature (K)
        
        # Wall temperature depends on cooling
        if design.get('regenerative_cooling'):
            wall_temp = 800  # With cooling
        else:
            wall_temp = 1200  # Without cooling
        
        return {
            'chamber_temp_k': chamber_temp,
            'wall_temp_k': wall_temp,
            'thermal_gradient_k': chamber_temp - wall_temp
        }
    
    def _check_failures(self, design: Dict[str, Any], 
                       stress: Dict[str, float],
                       thermal: Dict[str, float]) -> List[str]:
        """Check for failure modes"""
        failures = []
        
        # Material limits
        material = design.get('chamber_material', 'Inconel 718')
        material_limits = {
            'Inconel 718': {'max_temp_k': 980, 'yield_strength_pa': 1100e6},
            'SS 316L': {'max_temp_k': 870, 'yield_strength_pa': 290e6},
            'Niobium C-103': {'max_temp_k': 1370, 'yield_strength_pa': 345e6}
        }
        
        if material in material_limits:
            limits = material_limits[material]
            
            # Thermal failure
            if thermal['wall_temp_k'] > limits['max_temp_k']:
                failures.append(f"Thermal failure: {thermal['wall_temp_k']:.0f}K > {limits['max_temp_k']}K")
            
            # Structural failure
            if stress['von_mises_stress_pa'] > limits['yield_strength_pa']:
                failures.append(f"Structural failure: stress exceeds yield strength")
        
        return failures
    
    def _calculate_margin_of_safety(self, design: Dict[str, Any],
                                    stress: Dict[str, float]) -> float:
        """Calculate margin of safety"""
        material = design.get('chamber_material', 'Inconel 718')
        material_limits = {
            'Inconel 718': {'yield_strength_pa': 1100e6},
            'SS 316L': {'yield_strength_pa': 290e6},
            'Niobium C-103': {'yield_strength_pa': 345e6}
        }
        
        if material in material_limits:
            yield_strength = material_limits[material]['yield_strength_pa']
            applied_stress = stress['von_mises_stress_pa']
            
            # MOS = (Allowable / Applied) - 1
            mos = (yield_strength / applied_stress) - 1
            return mos
        
        return 0.0
    
    def monte_carlo_analysis(self, design: Dict[str, Any], 
                            num_runs: int = 1000) -> MonteCarloResults:
        """
        Run Monte Carlo analysis with manufacturing tolerances
        """
        logger.info(f"Running Monte Carlo analysis with {num_runs} runs")
        
        successes = 0
        performance_samples = {
            'thrust_n': [],
            'isp_s': [],
            'thrust_to_weight': []
        }
        failure_counts = {}
        
        for i in range(num_runs):
            # Add random variations based on tolerances
            varied_design = self._apply_tolerances(design)
            
            # Simulate
            result = self._simulate_scenario(varied_design, SimulationScenario.NOMINAL)
            
            if result.success:
                successes += 1
            
            # Collect performance
            for metric, value in result.performance_metrics.items():
                if metric in performance_samples:
                    performance_samples[metric].append(value)
            
            # Count failures
            for failure in result.failure_modes:
                failure_counts[failure] = failure_counts.get(failure, 0) + 1
        
        # Calculate statistics
        success_rate = successes / num_runs
        
        mean_perf = {k: np.mean(v) for k, v in performance_samples.items()}
        std_perf = {k: np.std(v) for k, v in performance_samples.items()}
        p95 = {k: np.percentile(v, 95) for k, v in performance_samples.items()}
        p5 = {k: np.percentile(v, 5) for k, v in performance_samples.items()}
        
        logger.info(f"Monte Carlo complete: {success_rate*100:.1f}% success rate")
        
        return MonteCarloResults(
            num_runs=num_runs,
            success_rate=success_rate,
            mean_performance=mean_perf,
            std_performance=std_perf,
            percentile_95=p95,
            percentile_5=p5,
            failure_distribution=failure_counts
        )
    
    def _apply_tolerances(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """Apply manufacturing tolerances as random variations"""
        varied = design.copy()
        
        for param, tolerance in self.manufacturing_tolerances.items():
            if param in varied:
                nominal = varied[param]
                # Random variation within tolerance
                variation = np.random.uniform(-tolerance, tolerance)
                
                if param in ['chamber_pressure', 'of_ratio']:
                    # Percentage variation
                    varied[param] = nominal * (1 + variation)
                else:
                    # Absolute variation
                    varied[param] = nominal + variation
        
        return varied
    
    def failure_first_testing(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test how the design breaks
        Systematically increase loads until failure
        """
        logger.info("Running failure-first testing")
        
        failure_points = {}
        
        # Test pressure limits
        pressure_failure = self._find_pressure_limit(design)
        failure_points['pressure_limit_mpa'] = pressure_failure / 1e6
        
        # Test temperature limits
        temp_failure = self._find_temperature_limit(design)
        failure_points['temperature_limit_k'] = temp_failure
        
        # Test cycle limits
        cycle_failure = self._estimate_cycle_life(design)
        failure_points['estimated_cycles'] = cycle_failure
        
        return failure_points
    
    def _find_pressure_limit(self, design: Dict[str, Any]) -> float:
        """Find pressure at which design fails"""
        nominal_pressure = design.get('chamber_pressure_pa', 15e6)
        
        # Incrementally increase pressure
        for multiplier in np.arange(1.0, 3.0, 0.1):
            test_design = design.copy()
            test_design['chamber_pressure_pa'] = nominal_pressure * multiplier
            
            stress = self._calculate_stress(test_design)
            
            material = design.get('chamber_material', 'Inconel 718')
            yield_strength = {
                'Inconel 718': 1100e6,
                'SS 316L': 290e6,
                'Niobium C-103': 345e6
            }.get(material, 1000e6)
            
            if stress['von_mises_stress_pa'] > yield_strength:
                return nominal_pressure * multiplier
        
        return nominal_pressure * 3.0  # Max tested
    
    def _find_temperature_limit(self, design: Dict[str, Any]) -> float:
        """Find temperature at which material fails"""
        material = design.get('chamber_material', 'Inconel 718')
        
        limits = {
            'Inconel 718': 980,
            'SS 316L': 870,
            'Niobium C-103': 1370
        }
        
        return limits.get(material, 1000)
    
    def _estimate_cycle_life(self, design: Dict[str, Any]) -> int:
        """Estimate number of thermal cycles before failure"""
        # Simplified Coffin-Manson relationship
        chamber_pressure_mpa = design.get('chamber_pressure_pa', 15e6) / 1e6
        
        # Higher pressure = more cycles needed = lower life
        if chamber_pressure_mpa > 25:
            return 50
        elif chamber_pressure_mpa > 20:
            return 100
        elif chamber_pressure_mpa > 15:
            return 200
        else:
            return 500
    
    def train_surrogate_from_history(self):
        """Train surrogate model from simulation history"""
        if len(self.simulation_history) < 10:
            logger.warning("Not enough simulation history to train surrogate")
            return
        
        # Extract features and targets
        X = []
        y = {'thrust_n': [], 'isp_s': []}
        
        for result in self.simulation_history:
            if result.scenario == SimulationScenario.NOMINAL and result.success:
                # Features: design parameters (simplified)
                features = [
                    result.stress_levels.get('hoop_stress_pa', 0) / 1e6,
                    result.thermal_profile.get('wall_temp_k', 0) / 1000,
                    result.performance_metrics.get('chamber_pressure_mpa', 0)
                ]
                X.append(features)
                
                # Targets: performance
                y['thrust_n'].append(result.performance_metrics.get('thrust_n', 0))
                y['isp_s'].append(result.performance_metrics.get('isp_s', 0))
        
        if len(X) > 0:
            X = np.array(X)
            y = {k: np.array(v) for k, v in y.items()}
            
            self.surrogate_model.train(X, y)
            logger.info("Surrogate model trained from history")
