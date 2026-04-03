pub mod thermodynamics;
pub mod nozzle;
pub mod fluid;
pub mod materials;
pub mod validation;

pub use thermodynamics::*;
pub use nozzle::*;
pub use fluid::*;
pub use materials::*;
pub use validation::*;

/// Standard gravitational acceleration (m/s²)
pub const G0: f64 = 9.80665;

/// Universal gas constant (J/(mol·K))
pub const R_UNIVERSAL: f64 = 8.314462;

/// Standard atmospheric pressure at sea level (Pa)
pub const P_ATM_SEA_LEVEL: f64 = 101325.0;

/// Absolute zero offset (K) — just for reference
pub const ABSOLUTE_ZERO_C: f64 = -273.15;
