// KÁNU — kanu_world_model::stress
//
// Stress testing: evaluate designs under off-nominal conditions.

use serde::{Deserialize, Serialize};
use kanu_physics::validation::{RocketDesign, DesignPerformance, evaluate_design};
use crate::conditions::OperatingCondition;

/// Result of a single stress test scenario.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StressTestResult {
    pub scenario: String,
    pub passed: bool,
    pub performance: Option<DesignPerformance>,
    pub failure_reasons: Vec<String>,
}

/// Complete stress test report for one design.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StressReport {
    pub design_id: u64,
    pub tests: Vec<StressTestResult>,
    pub all_passed: bool,
    pub pass_rate: f64,
}

/// Run stress tests on a design across multiple conditions.
pub fn stress_test_design(design: &RocketDesign) -> StressReport {
    let mut tests = Vec::new();
    
    // Test 1: Different altitude conditions
    for cond in OperatingCondition::standard_profiles() {
        let result = evaluate_design(design, cond.ambient_pressure_pa);
        tests.push(StressTestResult {
            scenario: format!("Altitude: {}", cond.name),
            passed: result.is_valid,
            performance: result.performance,
            failure_reasons: result.reasons,
        });
    }

    // Test 2: Chamber pressure variation ±20%
    for factor in [0.8, 1.2] {
        let mut d = design.clone();
        d.chamber_pressure_pa *= factor;
        let result = evaluate_design(&d, kanu_physics::P_ATM_SEA_LEVEL);
        tests.push(StressTestResult {
            scenario: format!("Pc × {:.1}", factor),
            passed: result.is_valid,
            performance: result.performance,
            failure_reasons: result.reasons,
        });
    }

    // Test 3: O/F ratio variation ±10%
    for factor in [0.9, 1.1] {
        let mut d = design.clone();
        d.of_ratio *= factor;
        let result = evaluate_design(&d, kanu_physics::P_ATM_SEA_LEVEL);
        tests.push(StressTestResult {
            scenario: format!("O/F × {:.1}", factor),
            passed: result.is_valid,
            performance: result.performance,
            failure_reasons: result.reasons,
        });
    }

    let pass_count = tests.iter().filter(|t| t.passed).count();
    let total = tests.len();

    StressReport {
        design_id: design.id,
        tests,
        all_passed: pass_count == total,
        pass_rate: pass_count as f64 / total as f64,
    }
}

/// Run stress tests on multiple designs, return only those that pass all.
pub fn filter_by_stress_test(designs: &[RocketDesign]) -> Vec<(RocketDesign, StressReport)> {
    designs.iter()
        .map(|d| {
            let report = stress_test_design(d);
            (d.clone(), report)
        })
        .filter(|(_, report)| report.pass_rate >= 0.75) // At least 75% pass rate
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_stress_test() {
        let d = RocketDesign {
            id: 0, propellant_name: "LOX/RP-1".into(),
            chamber_pressure_pa: 10.0e6, chamber_radius_m: 0.15,
            chamber_length_m: 0.4, wall_thickness_m: 0.006,
            throat_radius_m: 0.08, expansion_ratio: 15.0,
            of_ratio: 2.56, chamber_material: "Inconel 718".into(),
            nozzle_material: "Niobium C-103".into(), nozzle_bell_factor: 0.8,
        };
        let report = stress_test_design(&d);
        assert!(!report.tests.is_empty());
        assert!(report.pass_rate >= 0.0 && report.pass_rate <= 1.0);
    }
}
