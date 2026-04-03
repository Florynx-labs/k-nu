// KÁNU — kanu_physics::nozzle
//
// Converging-diverging (de Laval) nozzle physics.
// Isentropic flow relations, thrust coefficient, and nozzle sizing.
//
// All formulas from NASA SP-125 and Sutton & Biblarz "Rocket Propulsion Elements".

use serde::{Deserialize, Serialize};
use crate::{G0, P_ATM_SEA_LEVEL};

/// Complete nozzle performance calculation result.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NozzlePerformance {
    /// Exhaust velocity at nozzle exit (m/s)
    pub exit_velocity: f64,
    /// Thrust coefficient (dimensionless)
    pub thrust_coefficient: f64,
    /// Exit pressure (Pa)
    pub exit_pressure: f64,
    /// Exit Mach number
    pub exit_mach: f64,
    /// Exit-to-throat area ratio (Ae/A*)
    pub area_ratio: f64,
    /// Thrust (N)
    pub thrust: f64,
    /// Specific impulse (s)
    pub isp: f64,
    /// Mass flow rate (kg/s)
    pub mass_flow_rate: f64,
}

/// Compute nozzle exit velocity using isentropic expansion.
///
/// Ve = sqrt( (2·γ/(γ-1)) · R·Tc · (1 - (Pe/Pc)^((γ-1)/γ)) )
///
/// This is the velocity achieved by expanding gas from chamber conditions
/// (Pc, Tc) to exit pressure Pe through an ideal nozzle.
///
/// Reference: Sutton & Biblarz Eq. 3-16
pub fn exit_velocity(
    gamma: f64,
    r_specific: f64,
    tc: f64,
    pc: f64,    // Chamber pressure (Pa)
    pe: f64,    // Exit pressure (Pa)
) -> f64 {
    let gm1 = gamma - 1.0;
    let pressure_ratio = pe / pc;
    let exponent = gm1 / gamma;

    let term = 1.0 - pressure_ratio.powf(exponent);
    let coeff = (2.0 * gamma / gm1) * r_specific * tc;

    (coeff * term).max(0.0).sqrt()
}

/// Compute exit Mach number from pressure ratio using isentropic relation.
///
/// Me = sqrt( (2/(γ-1)) · ((Pc/Pe)^((γ-1)/γ) - 1) )
///
/// Reference: Standard isentropic flow relation
pub fn exit_mach_number(gamma: f64, pc: f64, pe: f64) -> f64 {
    let gm1 = gamma - 1.0;
    let pressure_ratio = pc / pe;
    let exponent = gm1 / gamma;

    let term = pressure_ratio.powf(exponent) - 1.0;
    ((2.0 / gm1) * term).max(0.0).sqrt()
}

/// Compute nozzle area ratio (Ae/A*) from exit Mach number.
///
/// Ae/A* = (1/Me) · ((2/(γ+1)) · (1 + (γ-1)/2 · Me²))^((γ+1)/(2·(γ-1)))
///
/// This determines the physical size of the nozzle bell relative to the throat.
///
/// Reference: NASA SP-125, Eq. 2
pub fn area_ratio_from_mach(gamma: f64, mach: f64) -> f64 {
    if mach <= 0.0 {
        return f64::INFINITY;
    }

    let gp1 = gamma + 1.0;
    let gm1 = gamma - 1.0;

    let base = (2.0 / gp1) * (1.0 + (gm1 / 2.0) * mach * mach);
    let exponent = gp1 / (2.0 * gm1);

    (1.0 / mach) * base.powf(exponent)
}

/// Compute exit pressure from expansion ratio using iterative solution.
///
/// Given Ae/A* and Pc, find Pe. Uses Newton-Raphson iteration on the
/// area-Mach relation.
pub fn exit_pressure_from_area_ratio(
    gamma: f64,
    pc: f64,
    area_ratio: f64,
) -> f64 {
    // Find exit Mach number from area ratio using bisection
    // (supersonic branch: Me > 1)
    let mut m_low = 1.0_f64;
    let mut m_high = 50.0_f64;

    for _ in 0..100 {
        let m_mid = (m_low + m_high) / 2.0;
        let ar = area_ratio_from_mach(gamma, m_mid);

        if ar < area_ratio {
            m_low = m_mid;
        } else {
            m_high = m_mid;
        }
    }

    let me = (m_low + m_high) / 2.0;

    // Pe = Pc * (1 + (γ-1)/2 · Me²)^(-γ/(γ-1))
    let gm1 = gamma - 1.0;
    let term = 1.0 + (gm1 / 2.0) * me * me;
    pc * term.powf(-gamma / gm1)
}

/// Compute thrust coefficient Cf.
///
/// Cf = sqrt( (2γ²/(γ-1)) · (2/(γ+1))^((γ+1)/(γ-1)) · (1-(Pe/Pc)^((γ-1)/γ)) )
///    + (Pe - Pa) · Ae / (Pc · A*)
///
/// The thrust coefficient captures the nozzle's efficiency in converting
/// chamber pressure into thrust. It depends on the nozzle geometry (expansion
/// ratio) and ambient conditions.
///
/// Reference: Sutton & Biblarz Eq. 3-30
pub fn thrust_coefficient(
    gamma: f64,
    pc: f64,     // Chamber pressure (Pa)
    pe: f64,     // Exit pressure (Pa)
    pa: f64,     // Ambient pressure (Pa)
    area_ratio: f64,  // Ae/A*
) -> f64 {
    let gp1 = gamma + 1.0;
    let gm1 = gamma - 1.0;

    // Momentum thrust term
    let a = (2.0 * gamma * gamma) / gm1;
    let b = (2.0 / gp1).powf(gp1 / gm1);
    let c = 1.0 - (pe / pc).powf(gm1 / gamma);
    let momentum_cf = (a * b * c).max(0.0).sqrt();

    // Pressure thrust term
    let pressure_cf = ((pe - pa) / pc) * area_ratio;

    momentum_cf + pressure_cf
}

/// Compute mass flow rate through a choked nozzle throat.
///
/// ṁ = Pc · A* / c*
///
/// where A* is the throat area and c* is characteristic velocity.
/// The flow is choked (Mach 1.0) at the throat for all practical rocket engines.
///
/// Reference: Sutton & Biblarz Eq. 3-24
pub fn mass_flow_rate(pc: f64, throat_area: f64, c_star: f64) -> f64 {
    pc * throat_area / c_star
}

/// Compute thrust from mass flow rate and exhaust conditions.
///
/// F = ṁ · Ve + (Pe - Pa) · Ae
///
/// This is the complete thrust equation including both momentum and pressure terms.
///
/// Reference: Newton's 3rd Law applied to rocket propulsion
pub fn thrust(
    mass_flow: f64,
    exit_velocity: f64,
    pe: f64,     // Exit pressure (Pa)
    pa: f64,     // Ambient pressure (Pa)
    exit_area: f64,
) -> f64 {
    mass_flow * exit_velocity + (pe - pa) * exit_area
}

/// Compute specific impulse.
///
/// Isp = F / (ṁ · g₀)
///
/// The specific impulse is the key measure of propellant efficiency.
/// Higher Isp = more thrust per unit mass of propellant consumed.
pub fn specific_impulse(thrust: f64, mass_flow: f64) -> f64 {
    if mass_flow <= 0.0 {
        return 0.0;
    }
    thrust / (mass_flow * G0)
}

/// Compute throat area from desired thrust level.
///
/// A* = F / (Cf · Pc)
///
/// This is the fundamental sizing equation for a rocket engine.
pub fn throat_area_from_thrust(target_thrust: f64, cf: f64, pc: f64) -> f64 {
    if cf <= 0.0 || pc <= 0.0 {
        return 0.0;
    }
    target_thrust / (cf * pc)
}

/// Compute complete nozzle performance for given design parameters.
pub fn compute_nozzle_performance(
    gamma: f64,
    r_specific: f64,
    tc: f64,
    pc: f64,           // Chamber pressure (Pa)
    expansion_ratio: f64,  // Ae/A*
    throat_area: f64,  // A* (m²)
    pa: f64,           // Ambient pressure (Pa)
    c_star: f64,       // Characteristic velocity (m/s)
) -> NozzlePerformance {
    let pe = exit_pressure_from_area_ratio(gamma, pc, expansion_ratio);
    let me = exit_mach_number(gamma, pc, pe);
    let ve = exit_velocity(gamma, r_specific, tc, pc, pe);
    let cf = thrust_coefficient(gamma, pc, pe, pa, expansion_ratio);
    let mdot = mass_flow_rate(pc, throat_area, c_star);
    let exit_area = throat_area * expansion_ratio;
    let f = thrust(mdot, ve, pe, pa, exit_area);
    let isp = specific_impulse(f, mdot);

    NozzlePerformance {
        exit_velocity: ve,
        thrust_coefficient: cf,
        exit_pressure: pe,
        exit_mach: me,
        area_ratio: expansion_ratio,
        thrust: f,
        isp,
        mass_flow_rate: mdot,
    }
}

/// Compute optimal expansion ratio for a given ambient pressure.
///
/// The optimal expansion ratio is when Pe = Pa (perfectly adapted nozzle).
/// This maximizes thrust for a given chamber pressure and altitude.
pub fn optimal_expansion_ratio(gamma: f64, pc: f64, pa: f64) -> f64 {
    let me = exit_mach_number(gamma, pc, pa);
    area_ratio_from_mach(gamma, me)
}

/// Get ambient pressure for a given altitude using barometric formula.
///
/// P(h) = P₀ · exp(-h / H)
///
/// where H ≈ 8500 m is the scale height of Earth's atmosphere.
/// Valid approximation up to ~80 km.
pub fn ambient_pressure_at_altitude(altitude_m: f64) -> f64 {
    let scale_height = 8500.0; // meters
    P_ATM_SEA_LEVEL * (-altitude_m / scale_height).exp()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::thermodynamics::{Propellant, specific_gas_constant, characteristic_velocity};

    fn setup_lox_rp1() -> (f64, f64, f64, f64) {
        let prop = Propellant::lox_rp1();
        let r = specific_gas_constant(prop.molecular_weight);
        let c_star = characteristic_velocity(prop.gamma, r, prop.combustion_temperature);
        (prop.gamma, r, prop.combustion_temperature, c_star)
    }

    #[test]
    fn test_exit_velocity_lox_rp1() {
        let (gamma, r, tc, _) = setup_lox_rp1();
        let pc = 10.0e6; // 10 MPa
        let pe = 0.1e6;  // 100 kPa (sea level)
        let ve = exit_velocity(gamma, r, tc, pc, pe);
        // Exhaust velocity for LOX/RP-1 should be ~2700-3000 m/s
        assert!(
            ve > 2500.0 && ve < 3200.0,
            "Ve = {ve} m/s — expected ~2800 for LOX/RP-1"
        );
    }

    #[test]
    fn test_exit_mach_number() {
        let gamma = 1.24;
        let pc = 10.0e6;
        let pe = 0.05e6;
        let me = exit_mach_number(gamma, pc, pe);
        // Mach number should be supersonic (> 1) for any expansion
        assert!(me > 1.0, "Me = {me} — must be supersonic");
        assert!(me < 10.0, "Me = {me} — unreasonably high");
    }

    #[test]
    fn test_area_ratio_mach_1() {
        // At Mach 1 (throat), area ratio should be 1.0
        let ar = area_ratio_from_mach(1.4, 1.0);
        assert!((ar - 1.0).abs() < 1e-10, "A/A* at M=1 should be 1.0, got {ar}");
    }

    #[test]
    fn test_area_ratio_supersonic() {
        // At Mach 3, area ratio should be > 1
        let ar = area_ratio_from_mach(1.4, 3.0);
        assert!(ar > 1.0);
        // For γ=1.4, M=3: Ae/A* ≈ 4.23
        assert!((ar - 4.23).abs() < 0.1, "Ae/A* at M=3, γ=1.4 = {ar}");
    }

    #[test]
    fn test_thrust_coefficient_range() {
        let gamma = 1.24;
        let pc = 10.0e6;
        let pe = 0.05e6;
        let pa = P_ATM_SEA_LEVEL;
        let ar = 15.0;
        let cf = thrust_coefficient(gamma, pc, pe, pa, ar);
        // Cf typically ranges from 1.0 to 2.0 for practical engines
        assert!(
            cf > 1.0 && cf < 2.2,
            "Cf = {cf} — should be in range [1.0, 2.2]"
        );
    }

    #[test]
    fn test_specific_impulse_lox_rp1() {
        let (gamma, r, tc, c_star) = setup_lox_rp1();
        let pc = 10.0e6;
        let ar = 15.0;
        let throat_diam = 0.20; // 20 cm throat
        let throat_area = std::f64::consts::PI * (throat_diam / 2.0).powi(2);

        let perf = compute_nozzle_performance(
            gamma, r, tc, pc, ar, throat_area, P_ATM_SEA_LEVEL, c_star,
        );

        // LOX/RP-1 Isp at sea level should be ~270-310 s
        assert!(
            perf.isp > 250.0 && perf.isp < 330.0,
            "Isp = {} s — expected 270-310 for LOX/RP-1 at sea level",
            perf.isp
        );
    }

    #[test]
    fn test_ambient_pressure_sea_level() {
        let p = ambient_pressure_at_altitude(0.0);
        assert!((p - P_ATM_SEA_LEVEL).abs() < 1.0);
    }

    #[test]
    fn test_ambient_pressure_10km() {
        let p = ambient_pressure_at_altitude(10_000.0);
        // At 10 km, pressure ≈ 26.5 kPa
        assert!(p > 20_000.0 && p < 35_000.0, "P(10km) = {p} Pa");
    }

    #[test]
    fn test_ambient_pressure_vacuum() {
        let p = ambient_pressure_at_altitude(200_000.0);
        // At 200 km, pressure is essentially zero
        assert!(p < 1.0, "P(200km) = {p} Pa — should be ~0");
    }

    #[test]
    fn test_mass_flow_rate() {
        let pc = 10.0e6;
        let throat_area = 0.01; // m²
        let c_star = 1800.0;    // m/s
        let mdot = mass_flow_rate(pc, throat_area, c_star);
        // ṁ = 10e6 * 0.01 / 1800 ≈ 55.6 kg/s
        assert!((mdot - 55.56).abs() < 1.0, "mdot = {mdot} kg/s");
    }

    #[test]
    fn test_optimal_expansion_ratio() {
        let gamma = 1.24;
        let pc = 10.0e6;
        let ar = optimal_expansion_ratio(gamma, pc, P_ATM_SEA_LEVEL);
        // For LOX/RP-1 at 10 MPa, optimal sea-level expansion is ~12-20
        assert!(ar > 5.0 && ar < 40.0, "Optimal AR = {ar}");
    }
}
