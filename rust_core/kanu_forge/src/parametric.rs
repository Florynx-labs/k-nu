// KÁNU — kanu_forge::parametric
//
// Design parameter space definition with physical bounds.

use serde::{Deserialize, Serialize};

/// Bounds for a single design parameter.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParamBounds {
    pub min: f64,
    pub max: f64,
}

impl ParamBounds {
    pub fn new(min: f64, max: f64) -> Self { Self { min, max } }
    pub fn clamp(&self, v: f64) -> f64 { v.max(self.min).min(self.max) }
    pub fn range(&self) -> f64 { self.max - self.min }
    pub fn contains(&self, v: f64) -> bool { v >= self.min && v <= self.max }
}

/// Full design space for rocket engine generation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DesignSpace {
    /// Chamber pressure (Pa): 3 MPa - 25 MPa
    pub chamber_pressure: ParamBounds,
    /// Chamber radius (m): 0.05 - 0.5
    pub chamber_radius: ParamBounds,
    /// Chamber length (m): 0.1 - 1.5
    pub chamber_length: ParamBounds,
    /// Wall thickness (m): 0.002 - 0.015
    pub wall_thickness: ParamBounds,
    /// Throat radius (m): 0.02 - 0.3
    pub throat_radius: ParamBounds,
    /// Expansion ratio (Ae/A*): 4 - 80
    pub expansion_ratio: ParamBounds,
    /// O/F mixture ratio: set per propellant
    pub of_ratio: ParamBounds,
    /// Nozzle bell factor: 0.7 - 1.0
    pub nozzle_bell_factor: ParamBounds,
}

impl Default for DesignSpace {
    fn default() -> Self {
        Self {
            chamber_pressure: ParamBounds::new(3.0e6, 25.0e6),
            chamber_radius: ParamBounds::new(0.05, 0.50),
            chamber_length: ParamBounds::new(0.1, 1.5),
            wall_thickness: ParamBounds::new(0.002, 0.015),
            throat_radius: ParamBounds::new(0.02, 0.30),
            expansion_ratio: ParamBounds::new(4.0, 80.0),
            of_ratio: ParamBounds::new(1.5, 8.0),
            nozzle_bell_factor: ParamBounds::new(0.7, 1.0),
        }
    }
}

impl DesignSpace {
    /// Create design space constrained for a specific propellant.
    pub fn for_propellant(prop: &kanu_physics::Propellant) -> Self {
        let mut space = Self::default();
        space.of_ratio = ParamBounds::new(prop.of_ratio_range.0, prop.of_ratio_range.1);
        space
    }
}
