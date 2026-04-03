// KÁNU — kanu_physics::validation
//
// Design validation: rejects physically impossible or unsafe designs.

use serde::{Deserialize, Serialize};
use crate::materials::{Material, check_chamber_structure, estimate_engine_mass};
use crate::thermodynamics::{Propellant, compute_combustion};
use crate::nozzle::compute_nozzle_performance;

/// A complete rocket engine design with all parameters.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RocketDesign {
    pub id: u64,
    pub propellant_name: String,
    pub chamber_pressure_pa: f64,
    pub chamber_radius_m: f64,
    pub chamber_length_m: f64,
    pub wall_thickness_m: f64,
    pub throat_radius_m: f64,
    pub expansion_ratio: f64,
    pub of_ratio: f64,
    pub chamber_material: String,
    pub nozzle_material: String,
    pub nozzle_bell_factor: f64,
}

/// Performance metrics computed from physics.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DesignPerformance {
    pub thrust_n: f64,
    pub isp_s: f64,
    pub mass_flow_kg_s: f64,
    pub exit_velocity_m_s: f64,
    pub thrust_coefficient: f64,
    pub c_star_m_s: f64,
    pub chamber_temperature_k: f64,
    pub exit_pressure_pa: f64,
    pub engine_mass_kg: f64,
    pub thrust_to_weight: f64,
    pub estimated_cost_usd: f64,
}

/// Validation result with pass/fail and reasons.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationResult {
    pub is_valid: bool,
    pub reasons: Vec<String>,
    pub performance: Option<DesignPerformance>,
}

/// Evaluate a design: compute performance and validate physics.
pub fn evaluate_design(design: &RocketDesign, ambient_pressure_pa: f64) -> ValidationResult {
    let mut reasons = Vec::new();

    // Look up propellant
    let propellant = match Propellant::by_name(&design.propellant_name) {
        Some(p) => p,
        None => return ValidationResult { is_valid: false, reasons: vec![format!("Unknown propellant: {}", design.propellant_name)], performance: None },
    };

    // Look up materials
    let chamber_mat = match Material::by_name(&design.chamber_material) {
        Some(m) => m,
        None => return ValidationResult { is_valid: false, reasons: vec![format!("Unknown chamber material: {}", design.chamber_material)], performance: None },
    };
    let nozzle_mat = match Material::by_name(&design.nozzle_material) {
        Some(m) => m,
        None => return ValidationResult { is_valid: false, reasons: vec![format!("Unknown nozzle material: {}", design.nozzle_material)], performance: None },
    };

    // Check O/F ratio is within valid range
    if design.of_ratio < propellant.of_ratio_range.0 || design.of_ratio > propellant.of_ratio_range.1 {
        reasons.push(format!("O/F ratio {:.2} outside valid range [{:.1}, {:.1}]", design.of_ratio, propellant.of_ratio_range.0, propellant.of_ratio_range.1));
    }

    // Check chamber pressure bounds (1 MPa - 30 MPa)
    if design.chamber_pressure_pa < 1.0e6 || design.chamber_pressure_pa > 30.0e6 {
        reasons.push(format!("Chamber pressure {:.1} MPa outside valid range [1, 30]", design.chamber_pressure_pa / 1e6));
    }

    // Check expansion ratio bounds
    if design.expansion_ratio < 2.0 || design.expansion_ratio > 200.0 {
        reasons.push(format!("Expansion ratio {:.1} outside valid range [2, 200]", design.expansion_ratio));
    }

    // Check geometry sanity
    if design.throat_radius_m >= design.chamber_radius_m {
        reasons.push("Throat radius >= chamber radius (impossible geometry)".into());
    }
    if design.wall_thickness_m < 0.001 || design.wall_thickness_m > 0.05 {
        reasons.push(format!("Wall thickness {:.1} mm outside range [1, 50]", design.wall_thickness_m * 1000.0));
    }

    // Compute combustion
    let combustion = compute_combustion(&propellant, design.of_ratio);

    // Compute nozzle performance
    let throat_area = std::f64::consts::PI * design.throat_radius_m.powi(2);
    let r_specific = crate::thermodynamics::specific_gas_constant(propellant.molecular_weight);

    let perf = compute_nozzle_performance(
        combustion.gamma, r_specific, combustion.chamber_temperature,
        design.chamber_pressure_pa, design.expansion_ratio,
        throat_area, ambient_pressure_pa, combustion.c_star,
    );

    // Check thrust is positive
    if perf.thrust <= 0.0 {
        reasons.push("Computed thrust is zero or negative".into());
    }

    // Check Isp is in reasonable range
    if perf.isp < 100.0 || perf.isp > 500.0 {
        reasons.push(format!("Isp {:.1} s outside reasonable range [100, 500]", perf.isp));
    }

    // Structural checks
    // For chamber wall temperature, assume regenerative cooling brings it to ~800K
    let wall_temp = 800.0_f64.min(combustion.chamber_temperature * 0.25);
    let structural = check_chamber_structure(&chamber_mat, design.chamber_pressure_pa, design.chamber_radius_m, design.wall_thickness_m, wall_temp, 1.5);
    for check in &structural {
        if !check.passes {
            reasons.push(format!("STRUCTURAL FAIL: {}", check.description));
        }
    }

    // Mass & cost estimation
    let mass = estimate_engine_mass(&chamber_mat, &nozzle_mat, design.chamber_radius_m, design.chamber_length_m, design.wall_thickness_m, design.throat_radius_m, design.expansion_ratio, design.nozzle_bell_factor);
    let cost = crate::materials::estimate_engine_cost(mass, &chamber_mat, &nozzle_mat, 0.5, 4.0);
    let t_to_w = if mass > 0.0 { perf.thrust / (mass * 9.80665) } else { 0.0 };

    // Check T/W ratio
    if t_to_w < 10.0 {
        reasons.push(format!("Thrust-to-weight {:.1} is too low (min 10)", t_to_w));
    }

    let performance = DesignPerformance {
        thrust_n: perf.thrust,
        isp_s: perf.isp,
        mass_flow_kg_s: perf.mass_flow_rate,
        exit_velocity_m_s: perf.exit_velocity,
        thrust_coefficient: perf.thrust_coefficient,
        c_star_m_s: combustion.c_star,
        chamber_temperature_k: combustion.chamber_temperature,
        exit_pressure_pa: perf.exit_pressure,
        engine_mass_kg: mass,
        thrust_to_weight: t_to_w,
        estimated_cost_usd: cost,
    };

    ValidationResult {
        is_valid: reasons.is_empty(),
        reasons,
        performance: Some(performance),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_design() -> RocketDesign {
        RocketDesign {
            id: 1,
            propellant_name: "LOX/RP-1".into(),
            chamber_pressure_pa: 10.0e6,
            chamber_radius_m: 0.15,
            chamber_length_m: 0.4,
            wall_thickness_m: 0.006,
            throat_radius_m: 0.08,
            expansion_ratio: 15.0,
            of_ratio: 2.56,
            chamber_material: "Inconel 718".into(),
            nozzle_material: "Niobium C-103".into(),
            nozzle_bell_factor: 0.8,
        }
    }

    #[test]
    fn test_valid_design() {
        let d = sample_design();
        let r = evaluate_design(&d, crate::P_ATM_SEA_LEVEL);
        assert!(r.is_valid, "Design should be valid. Failures: {:?}", r.reasons);
        let p = r.performance.unwrap();
        assert!(p.thrust_n > 0.0);
        assert!(p.isp_s > 200.0 && p.isp_s < 400.0);
    }

    #[test]
    fn test_invalid_propellant() {
        let mut d = sample_design();
        d.propellant_name = "FAKE".into();
        let r = evaluate_design(&d, crate::P_ATM_SEA_LEVEL);
        assert!(!r.is_valid);
    }

    #[test]
    fn test_impossible_geometry() {
        let mut d = sample_design();
        d.throat_radius_m = 0.20; // bigger than chamber
        let r = evaluate_design(&d, crate::P_ATM_SEA_LEVEL);
        assert!(!r.is_valid);
    }
}
