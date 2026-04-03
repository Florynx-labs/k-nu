// KÁNU — kanu_evolve::objectives
//
// Multi-objective fitness evaluation for rocket engine designs.

use serde::{Deserialize, Serialize};
use kanu_physics::validation::{DesignPerformance, RocketDesign, evaluate_design};

/// Objectives to optimize. Each objective has a direction.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Direction {
    Maximize,
    Minimize,
}

/// A single objective function value.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ObjectiveValue {
    pub name: String,
    pub value: f64,
    pub weight: f64,
}

/// Complete fitness for one design across all objectives.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Fitness {
    /// Normalized objective values (all in minimize direction)
    pub objectives: Vec<f64>,
    /// Constraint violation penalty (0.0 = feasible)
    pub constraint_violation: f64,
    /// Is the design feasible?
    pub feasible: bool,
    /// Raw performance data
    pub performance: DesignPerformance,
}

/// Objective definitions for rocket engine optimization.
/// Convention: all objectives are normalized to MINIMIZE direction.
pub struct ObjectiveSet {
    pub names: Vec<String>,
    pub directions: Vec<Direction>,
}

impl Default for ObjectiveSet {
    fn default() -> Self {
        Self {
            names: vec![
                "neg_isp".into(),        // maximize Isp → minimize -Isp
                "neg_thrust".into(),     // maximize thrust → minimize -thrust
                "mass".into(),           // minimize mass
                "cost".into(),           // minimize cost
                "neg_tw_ratio".into(),   // maximize T/W → minimize -T/W
            ],
            directions: vec![
                Direction::Minimize,  // -Isp
                Direction::Minimize,  // -thrust
                Direction::Minimize,  // mass
                Direction::Minimize,  // cost
                Direction::Minimize,  // -T/W
            ],
        }
    }
}

/// Evaluate fitness of a design across all objectives.
pub fn evaluate_fitness(design: &RocketDesign, ambient_pa: f64) -> Option<Fitness> {
    let result = evaluate_design(design, ambient_pa);
    let perf = result.performance?;

    let feasible = result.is_valid;
    let constraint_violation = if feasible { 0.0 } else { result.reasons.len() as f64 };

    // All normalized to minimize direction
    let objectives = vec![
        -perf.isp_s,                          // maximize Isp
        -perf.thrust_n / 1000.0,              // maximize thrust (kN scale)
        perf.engine_mass_kg,                   // minimize mass
        perf.estimated_cost_usd / 1_000_000.0, // minimize cost (M$ scale)
        -perf.thrust_to_weight,                // maximize T/W
    ];

    Some(Fitness {
        objectives,
        constraint_violation,
        feasible,
        performance: perf,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_evaluate_fitness() {
        let d = RocketDesign {
            id: 0, propellant_name: "LOX/RP-1".into(),
            chamber_pressure_pa: 10.0e6, chamber_radius_m: 0.15,
            chamber_length_m: 0.4, wall_thickness_m: 0.006,
            throat_radius_m: 0.08, expansion_ratio: 15.0,
            of_ratio: 2.56, chamber_material: "Inconel 718".into(),
            nozzle_material: "Niobium C-103".into(), nozzle_bell_factor: 0.8,
        };
        let f = evaluate_fitness(&d, kanu_physics::P_ATM_SEA_LEVEL);
        assert!(f.is_some());
        let f = f.unwrap();
        assert_eq!(f.objectives.len(), 5);
        assert!(f.objectives[0] < 0.0); // -Isp should be negative
    }
}
