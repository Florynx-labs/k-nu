// KÁNU — kanu_world_model::conditions
//
// Operating condition profiles for design evaluation.

use serde::{Deserialize, Serialize};
use kanu_physics::nozzle::ambient_pressure_at_altitude;

/// An operating condition at which a design is evaluated.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OperatingCondition {
    pub name: String,
    pub altitude_m: f64,
    pub ambient_pressure_pa: f64,
    pub ambient_temperature_k: f64,
}

impl OperatingCondition {
    pub fn sea_level() -> Self {
        Self { name: "Sea Level".into(), altitude_m: 0.0, ambient_pressure_pa: 101325.0, ambient_temperature_k: 288.15 }
    }
    pub fn altitude_10km() -> Self {
        let alt = 10_000.0;
        Self { name: "10 km Altitude".into(), altitude_m: alt, ambient_pressure_pa: ambient_pressure_at_altitude(alt), ambient_temperature_k: 223.15 }
    }
    pub fn altitude_30km() -> Self {
        let alt = 30_000.0;
        Self { name: "30 km Altitude".into(), altitude_m: alt, ambient_pressure_pa: ambient_pressure_at_altitude(alt), ambient_temperature_k: 226.65 }
    }
    pub fn vacuum() -> Self {
        Self { name: "Vacuum".into(), altitude_m: 200_000.0, ambient_pressure_pa: 0.0, ambient_temperature_k: 2.7 }
    }
    pub fn standard_profiles() -> Vec<Self> {
        vec![Self::sea_level(), Self::altitude_10km(), Self::altitude_30km(), Self::vacuum()]
    }
}
