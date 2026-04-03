// KÁNU — kanu_physics::thermodynamics
//
// Real thermodynamic calculations for rocket combustion chambers.
// All formulas from Sutton & Biblarz "Rocket Propulsion Elements" and NASA SP-125.

use serde::{Deserialize, Serialize};
use crate::R_UNIVERSAL;

/// Propellant combination with real thermochemical properties.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Propellant {
    pub name: String,
    /// Ratio of specific heats (Cp/Cv) of combustion products
    pub gamma: f64,
    /// Mean molecular weight of combustion products (kg/mol)
    pub molecular_weight: f64,
    /// Adiabatic flame temperature at optimal mixture ratio (K)
    pub combustion_temperature: f64,
    /// Optimal oxidizer-to-fuel mass ratio
    pub optimal_of_ratio: f64,
    /// Valid O/F ratio range [min, max]
    pub of_ratio_range: (f64, f64),
    /// Oxidizer density (kg/m³)
    pub density_oxidizer: f64,
    /// Fuel density (kg/m³)
    pub density_fuel: f64,
}

impl Propellant {
    /// LOX/RP-1 (Kerosene) — Most common bipropellant (Merlin, F-1, RD-180)
    pub fn lox_rp1() -> Self {
        Self {
            name: "LOX/RP-1".into(),
            gamma: 1.24,
            molecular_weight: 0.0233,
            combustion_temperature: 3670.0,
            optimal_of_ratio: 2.56,
            of_ratio_range: (2.0, 3.2),
            density_oxidizer: 1141.0,
            density_fuel: 810.0,
        }
    }

    /// LOX/LH2 — Highest Isp bipropellant (SSME, RL-10, Vulcain)
    pub fn lox_lh2() -> Self {
        Self {
            name: "LOX/LH2".into(),
            gamma: 1.26,
            molecular_weight: 0.0100,
            combustion_temperature: 3400.0,
            optimal_of_ratio: 6.0,
            of_ratio_range: (4.0, 8.0),
            density_oxidizer: 1141.0,
            density_fuel: 70.8,
        }
    }

    /// N2O4/UDMH — Hypergolic (Proton, Long March)
    pub fn n2o4_udmh() -> Self {
        Self {
            name: "N2O4/UDMH".into(),
            gamma: 1.25,
            molecular_weight: 0.0250,
            combustion_temperature: 3400.0,
            optimal_of_ratio: 2.6,
            of_ratio_range: (2.0, 3.2),
            density_oxidizer: 1440.0,
            density_fuel: 793.0,
        }
    }

    /// LOX/CH4 — Next-gen (Raptor, BE-4)
    pub fn lox_ch4() -> Self {
        Self {
            name: "LOX/CH4".into(),
            gamma: 1.25,
            molecular_weight: 0.0200,
            combustion_temperature: 3550.0,
            optimal_of_ratio: 3.6,
            of_ratio_range: (2.8, 4.5),
            density_oxidizer: 1141.0,
            density_fuel: 422.6,
        }
    }

    /// Get propellant by name
    pub fn by_name(name: &str) -> Option<Self> {
        match name {
            "LOX/RP-1" => Some(Self::lox_rp1()),
            "LOX/LH2" => Some(Self::lox_lh2()),
            "N2O4/UDMH" => Some(Self::n2o4_udmh()),
            "LOX/CH4" => Some(Self::lox_ch4()),
            _ => None,
        }
    }

    /// All available propellants
    pub fn all() -> Vec<Self> {
        vec![
            Self::lox_rp1(),
            Self::lox_lh2(),
            Self::n2o4_udmh(),
            Self::lox_ch4(),
        ]
    }
}

/// Computed combustion properties for a given propellant at specific conditions.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CombustionProperties {
    /// Specific gas constant R = R_universal / M (J/(kg·K))
    pub specific_gas_constant: f64,
    /// Characteristic velocity c* (m/s)
    pub c_star: f64,
    /// Combustion temperature adjusted for O/F ratio (K)
    pub chamber_temperature: f64,
    /// Ratio of specific heats
    pub gamma: f64,
}

/// Compute the specific gas constant for combustion products.
///
/// R_specific = R_universal / M
///
/// where M is the mean molecular weight of the exhaust gas.
pub fn specific_gas_constant(molecular_weight: f64) -> f64 {
    R_UNIVERSAL / molecular_weight
}

/// Compute characteristic velocity c* (m/s).
///
/// c* = sqrt(γ · R · Tc) / (γ · sqrt((2/(γ+1))^((γ+1)/(γ-1))))
///
/// This is a measure of combustion efficiency — depends only on propellant
/// chemistry and combustion temperature, not on nozzle geometry.
///
/// Reference: Sutton & Biblarz Eq. 3-32
pub fn characteristic_velocity(gamma: f64, r_specific: f64, tc: f64) -> f64 {
    let gp1 = gamma + 1.0;
    let gm1 = gamma - 1.0;

    // (2/(γ+1))^((γ+1)/(γ-1))
    let base = 2.0 / gp1;
    let exponent = gp1 / gm1;
    let term = base.powf(exponent);

    // c* = sqrt(γ · R · Tc) / (γ · sqrt(term))
    (gamma * r_specific * tc).sqrt() / (gamma * term.sqrt())
}

/// Adjust combustion temperature for off-optimal mixture ratio.
///
/// The flame temperature peaks at the optimal O/F ratio and decreases
/// as you deviate from it. This uses a parabolic approximation:
///
/// Tc_adjusted = Tc_peak · (1 - k · ((OF - OF_opt) / OF_opt)²)
///
/// where k ≈ 0.3 is an empirical correction factor.
pub fn adjusted_combustion_temperature(
    tc_peak: f64,
    of_ratio: f64,
    of_optimal: f64,
) -> f64 {
    let k = 0.3; // empirical correction factor
    let deviation = (of_ratio - of_optimal) / of_optimal;
    let correction = 1.0 - k * deviation * deviation;
    tc_peak * correction.max(0.5) // floor at 50% to avoid nonsense
}

/// Compute full combustion properties for a propellant at given conditions.
pub fn compute_combustion(propellant: &Propellant, of_ratio: f64) -> CombustionProperties {
    let r_spec = specific_gas_constant(propellant.molecular_weight);
    let tc = adjusted_combustion_temperature(
        propellant.combustion_temperature,
        of_ratio,
        propellant.optimal_of_ratio,
    );
    let c_star = characteristic_velocity(propellant.gamma, r_spec, tc);

    CombustionProperties {
        specific_gas_constant: r_spec,
        c_star,
        chamber_temperature: tc,
        gamma: propellant.gamma,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_specific_gas_constant_lox_rp1() {
        let prop = Propellant::lox_rp1();
        let r = specific_gas_constant(prop.molecular_weight);
        // R = 8.314 / 0.0233 ≈ 356.8 J/(kg·K)
        assert!((r - 356.8).abs() < 1.0, "R_specific = {r}");
    }

    #[test]
    fn test_characteristic_velocity_lox_rp1() {
        let prop = Propellant::lox_rp1();
        let r = specific_gas_constant(prop.molecular_weight);
        let c_star = characteristic_velocity(prop.gamma, r, prop.combustion_temperature);
        // c* for LOX/RP-1 should be approximately 1750-1850 m/s
        assert!(
            c_star > 1700.0 && c_star < 1900.0,
            "c* = {c_star} m/s — expected ~1800 m/s for LOX/RP-1"
        );
    }

    #[test]
    fn test_characteristic_velocity_lox_lh2() {
        let prop = Propellant::lox_lh2();
        let r = specific_gas_constant(prop.molecular_weight);
        let c_star = characteristic_velocity(prop.gamma, r, prop.combustion_temperature);
        // c* for LOX/LH2 should be approximately 2300-2400 m/s
        assert!(
            c_star > 2200.0 && c_star < 2500.0,
            "c* = {c_star} m/s — expected ~2350 m/s for LOX/LH2"
        );
    }

    #[test]
    fn test_adjusted_temperature_at_optimal() {
        let prop = Propellant::lox_rp1();
        let tc = adjusted_combustion_temperature(
            prop.combustion_temperature,
            prop.optimal_of_ratio,
            prop.optimal_of_ratio,
        );
        assert!((tc - prop.combustion_temperature).abs() < 0.01);
    }

    #[test]
    fn test_adjusted_temperature_off_optimal() {
        let prop = Propellant::lox_rp1();
        // At O/F = 2.0 (off-optimal), temperature should be lower
        let tc = adjusted_combustion_temperature(
            prop.combustion_temperature,
            2.0,
            prop.optimal_of_ratio,
        );
        assert!(tc < prop.combustion_temperature);
        assert!(tc > 0.5 * prop.combustion_temperature);
    }

    #[test]
    fn test_propellant_by_name() {
        assert!(Propellant::by_name("LOX/RP-1").is_some());
        assert!(Propellant::by_name("LOX/LH2").is_some());
        assert!(Propellant::by_name("INVALID").is_none());
    }

    #[test]
    fn test_compute_combustion() {
        let prop = Propellant::lox_rp1();
        let result = compute_combustion(&prop, prop.optimal_of_ratio);
        assert!(result.c_star > 1700.0);
        assert!((result.chamber_temperature - prop.combustion_temperature).abs() < 1.0);
        assert!(result.specific_gas_constant > 300.0);
    }
}
