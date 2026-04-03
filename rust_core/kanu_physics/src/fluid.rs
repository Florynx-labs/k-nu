// KÁNU — kanu_physics::fluid
//
// Fluid dynamics calculations for propellant flow through engine components.
// Covers Reynolds number, pressure drops, and injector sizing.

use serde::{Deserialize, Serialize};

/// Fluid flow properties at a point in the system.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FlowProperties {
    /// Velocity (m/s)
    pub velocity: f64,
    /// Reynolds number (dimensionless)
    pub reynolds: f64,
    /// Pressure drop (Pa)
    pub pressure_drop: f64,
    /// Flow regime description
    pub regime: FlowRegime,
}

/// Flow regime classification based on Reynolds number.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum FlowRegime {
    Laminar,      // Re < 2300
    Transitional, // 2300 < Re < 4000
    Turbulent,    // Re > 4000
}

/// Compute Reynolds number.
///
/// Re = ρ · v · D / μ
///
/// The Reynolds number determines whether flow is laminar or turbulent.
/// In rocket engines, flow is almost always highly turbulent (Re > 10⁶).
pub fn reynolds_number(
    density: f64,   // kg/m³
    velocity: f64,  // m/s
    diameter: f64,  // m (hydraulic diameter)
    viscosity: f64, // Pa·s (dynamic viscosity)
) -> f64 {
    if viscosity <= 0.0 {
        return f64::INFINITY;
    }
    density * velocity * diameter / viscosity
}

/// Classify flow regime from Reynolds number.
pub fn flow_regime(re: f64) -> FlowRegime {
    if re < 2300.0 {
        FlowRegime::Laminar
    } else if re < 4000.0 {
        FlowRegime::Transitional
    } else {
        FlowRegime::Turbulent
    }
}

/// Compute Darcy friction factor.
///
/// For laminar flow: f = 64/Re
/// For turbulent flow: Colebrook-White approximation (Swamee-Jain)
///
/// f = 0.25 / (log10(ε/(3.7·D) + 5.74/Re^0.9))²
///
/// Reference: Swamee & Jain (1976)
pub fn darcy_friction_factor(re: f64, roughness: f64, diameter: f64) -> f64 {
    if re < 2300.0 {
        // Laminar: exact Hagen-Poiseuille solution
        64.0 / re
    } else {
        // Turbulent: Swamee-Jain explicit approximation of Colebrook-White
        let term = roughness / (3.7 * diameter) + 5.74 / re.powf(0.9);
        0.25 / term.log10().powi(2)
    }
}

/// Compute pressure drop through a pipe/channel.
///
/// ΔP = f · (L/D) · (ρ · v² / 2)
///
/// This is the Darcy-Weisbach equation for head loss in pipe flow.
/// Used for estimating pressure drops in feed lines, manifolds, and
/// cooling channels.
///
/// Reference: Darcy-Weisbach equation
pub fn pressure_drop_pipe(
    friction_factor: f64,
    length: f64,       // m
    diameter: f64,     // m
    density: f64,      // kg/m³
    velocity: f64,     // m/s
) -> f64 {
    friction_factor * (length / diameter) * (density * velocity * velocity / 2.0)
}

/// Compute pressure drop across an injector orifice.
///
/// ΔP = ṁ² / (2 · ρ · Cd² · A²)
///
/// where Cd is the discharge coefficient (typically 0.6-0.8 for rocket injectors).
///
/// The injector pressure drop should be 15-25% of chamber pressure
/// to prevent combustion instability (Crocco's criterion).
pub fn injector_pressure_drop(
    mass_flow: f64,
    density: f64,
    cd: f64,          // discharge coefficient
    orifice_area: f64,
) -> f64 {
    if density <= 0.0 || cd <= 0.0 || orifice_area <= 0.0 {
        return f64::INFINITY;
    }
    let effective_area = cd * orifice_area;
    mass_flow * mass_flow / (2.0 * density * effective_area * effective_area)
}

/// Compute flow velocity from mass flow rate.
///
/// v = ṁ / (ρ · A)
pub fn flow_velocity(mass_flow: f64, density: f64, area: f64) -> f64 {
    if density <= 0.0 || area <= 0.0 {
        return 0.0;
    }
    mass_flow / (density * area)
}

/// Compute cooling channel flow properties.
///
/// For regenerative cooling, propellant flows through channels in the
/// chamber wall before injection. This computes the flow conditions
/// and pressure drop through those channels.
pub fn cooling_channel_analysis(
    mass_flow: f64,      // Total coolant flow (kg/s)
    num_channels: u32,
    channel_width: f64,  // m
    channel_height: f64, // m
    channel_length: f64, // m
    density: f64,        // kg/m³
    viscosity: f64,      // Pa·s
) -> FlowProperties {
    let channel_area = channel_width * channel_height;
    let hydraulic_diameter = 2.0 * channel_width * channel_height
        / (channel_width + channel_height);

    let flow_per_channel = mass_flow / num_channels as f64;
    let velocity = flow_velocity(flow_per_channel, density, channel_area);
    let re = reynolds_number(density, velocity, hydraulic_diameter, viscosity);
    let regime = flow_regime(re);

    let roughness = 3.0e-6; // typical machined surface roughness (m)
    let f = darcy_friction_factor(re, roughness, hydraulic_diameter);
    let dp = pressure_drop_pipe(f, channel_length, hydraulic_diameter, density, velocity);

    FlowProperties {
        velocity,
        reynolds: re,
        pressure_drop: dp,
        regime,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_reynolds_number() {
        // Water-like fluid: ρ=1000, v=1 m/s, D=0.01m, μ=0.001 Pa·s
        let re = reynolds_number(1000.0, 1.0, 0.01, 0.001);
        assert!((re - 10000.0).abs() < 1.0, "Re = {re}");
    }

    #[test]
    fn test_flow_regime_laminar() {
        assert_eq!(flow_regime(1000.0), FlowRegime::Laminar);
    }

    #[test]
    fn test_flow_regime_turbulent() {
        assert_eq!(flow_regime(10000.0), FlowRegime::Turbulent);
    }

    #[test]
    fn test_friction_factor_laminar() {
        let f = darcy_friction_factor(2000.0, 0.0, 0.01);
        assert!((f - 0.032).abs() < 0.001, "f_laminar = {f}, expected 0.032");
    }

    #[test]
    fn test_friction_factor_turbulent() {
        let f = darcy_friction_factor(100000.0, 1e-5, 0.01);
        // Typical turbulent friction factor ~0.018-0.025
        assert!(f > 0.01 && f < 0.05, "f_turbulent = {f}");
    }

    #[test]
    fn test_pressure_drop_pipe() {
        let dp = pressure_drop_pipe(0.02, 1.0, 0.01, 1000.0, 5.0);
        // ΔP = 0.02 * (1/0.01) * (1000 * 25 / 2) = 25000 Pa
        assert!((dp - 25000.0).abs() < 1.0, "ΔP = {dp} Pa");
    }

    #[test]
    fn test_injector_pressure_drop() {
        let dp = injector_pressure_drop(10.0, 1000.0, 0.7, 0.001);
        // Should give a meaningful pressure drop
        assert!(dp > 0.0);
        assert!(dp < 1e9); // not infinite
    }

    #[test]
    fn test_cooling_channel() {
        let result = cooling_channel_analysis(
            50.0,   // 50 kg/s total
            100,    // 100 channels
            0.002,  // 2mm wide
            0.003,  // 3mm tall
            0.5,    // 50cm long
            810.0,  // RP-1 density
            0.002,  // RP-1 viscosity
        );
        assert!(result.velocity > 0.0);
        assert!(result.reynolds > 0.0);
        assert!(result.pressure_drop > 0.0);
        assert_eq!(result.regime, FlowRegime::Turbulent);
    }
}
