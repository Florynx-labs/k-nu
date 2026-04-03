// KÁNU — kanu_physics::materials
//
// Material properties and structural analysis.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Material {
    pub name: String,
    pub category: String,
    pub density: f64,
    pub yield_strength: f64,
    pub ultimate_strength: f64,
    pub max_service_temperature: f64,
    pub thermal_conductivity: f64,
    pub cte: f64,
    pub cost_per_kg: f64,
}

impl Material {
    pub fn inconel_718() -> Self {
        Self { name: "Inconel 718".into(), category: "Nickel Superalloy".into(), density: 8190.0, yield_strength: 1034.0e6, ultimate_strength: 1241.0e6, max_service_temperature: 973.0, thermal_conductivity: 11.4, cte: 13.0e-6, cost_per_kg: 45.0 }
    }
    pub fn ss_316l() -> Self {
        Self { name: "SS 316L".into(), category: "Stainless Steel".into(), density: 7990.0, yield_strength: 205.0e6, ultimate_strength: 515.0e6, max_service_temperature: 1143.0, thermal_conductivity: 16.3, cte: 16.0e-6, cost_per_kg: 8.0 }
    }
    pub fn copper_cucr() -> Self {
        Self { name: "Copper C18200 (CuCr)".into(), category: "Copper Alloy".into(), density: 8890.0, yield_strength: 310.0e6, ultimate_strength: 450.0e6, max_service_temperature: 723.0, thermal_conductivity: 325.0, cte: 17.6e-6, cost_per_kg: 25.0 }
    }
    pub fn niobium_c103() -> Self {
        Self { name: "Niobium C-103".into(), category: "Refractory Alloy".into(), density: 8850.0, yield_strength: 270.0e6, ultimate_strength: 400.0e6, max_service_temperature: 1473.0, thermal_conductivity: 42.0, cte: 7.2e-6, cost_per_kg: 150.0 }
    }
    pub fn ti_6al_4v() -> Self {
        Self { name: "Ti-6Al-4V".into(), category: "Titanium Alloy".into(), density: 4430.0, yield_strength: 880.0e6, ultimate_strength: 950.0e6, max_service_temperature: 673.0, thermal_conductivity: 6.7, cte: 8.6e-6, cost_per_kg: 60.0 }
    }
    pub fn by_name(name: &str) -> Option<Self> {
        match name {
            "Inconel 718" => Some(Self::inconel_718()),
            "SS 316L" => Some(Self::ss_316l()),
            "Copper C18200 (CuCr)" => Some(Self::copper_cucr()),
            "Niobium C-103" => Some(Self::niobium_c103()),
            "Ti-6Al-4V" => Some(Self::ti_6al_4v()),
            _ => None,
        }
    }
    pub fn all() -> Vec<Self> {
        vec![Self::inconel_718(), Self::ss_316l(), Self::copper_cucr(), Self::niobium_c103(), Self::ti_6al_4v()]
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StructuralCheck {
    pub margin_of_safety: f64,
    pub passes: bool,
    pub description: String,
}

/// Hoop stress: σ = P·r/t (thin-wall pressure vessel)
pub fn hoop_stress(pressure: f64, radius: f64, wall_thickness: f64) -> f64 {
    if wall_thickness <= 0.0 { return f64::INFINITY; }
    pressure * radius / wall_thickness
}

/// Axial stress = σ_hoop / 2
pub fn axial_stress(pressure: f64, radius: f64, wall_thickness: f64) -> f64 {
    hoop_stress(pressure, radius, wall_thickness) / 2.0
}

/// Margin of Safety = (σ_allow / (σ_applied · SF)) - 1
pub fn margin_of_safety(allowable: f64, applied: f64, sf: f64) -> f64 {
    if applied <= 0.0 { return f64::INFINITY; }
    (allowable / (applied * sf)) - 1.0
}

pub fn thermal_margin(mat: &Material, temp: f64) -> f64 {
    (mat.max_service_temperature - temp) / mat.max_service_temperature
}

pub fn check_chamber_structure(mat: &Material, pc: f64, radius: f64, wall: f64, temp: f64, sf: f64) -> Vec<StructuralCheck> {
    let mut checks = Vec::new();
    let sh = hoop_stress(pc, radius, wall);
    let mos_h = margin_of_safety(mat.yield_strength, sh, sf);
    checks.push(StructuralCheck { margin_of_safety: mos_h, passes: mos_h >= 0.0, description: format!("Hoop: {:.1} MPa vs yield {:.1} MPa (SF={sf})", sh/1e6, mat.yield_strength/1e6) });
    let tm = thermal_margin(mat, temp);
    checks.push(StructuralCheck { margin_of_safety: tm, passes: tm > 0.0, description: format!("Temp: {temp:.0} K vs max {:.0} K", mat.max_service_temperature) });
    let sa = axial_stress(pc, radius, wall);
    let mos_a = margin_of_safety(mat.yield_strength, sa, sf);
    checks.push(StructuralCheck { margin_of_safety: mos_a, passes: mos_a >= 0.0, description: format!("Axial: {:.1} MPa vs yield {:.1} MPa", sa/1e6, mat.yield_strength/1e6) });
    checks
}

/// Mass estimation for engine: chamber + nozzle + convergent + injector + 20% margin
pub fn estimate_engine_mass(chamber_mat: &Material, nozzle_mat: &Material, chamber_r: f64, chamber_l: f64, wall: f64, throat_r: f64, exp_ratio: f64, bell: f64) -> f64 {
    let pi = std::f64::consts::PI;
    let chamber_vol = 2.0 * pi * chamber_r * chamber_l * wall;
    let chamber_mass = chamber_vol * chamber_mat.density;
    let exit_r = throat_r * exp_ratio.sqrt();
    let nozzle_l = (exit_r - throat_r) * bell * 1.5;
    let nozzle_surf = pi * (throat_r + exit_r) * ((exit_r - throat_r).powi(2) + nozzle_l.powi(2)).sqrt();
    let nozzle_mass = nozzle_surf * wall * nozzle_mat.density;
    let conv_mass = chamber_mass * 0.3;
    let inj_mass = pi * chamber_r.powi(2) * wall * 2.0 * chamber_mat.density;
    (chamber_mass + nozzle_mass + conv_mass + inj_mass) * 1.2
}

pub fn estimate_engine_cost(mass: f64, chamber_mat: &Material, nozzle_mat: &Material, chamber_frac: f64, mfg_factor: f64) -> f64 {
    let cm = mass * chamber_frac;
    let nm = mass * (1.0 - chamber_frac);
    (cm * chamber_mat.cost_per_kg + nm * nozzle_mat.cost_per_kg) * mfg_factor
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_hoop_stress() {
        let s = hoop_stress(10.0e6, 0.1, 0.005);
        assert!((s - 200.0e6).abs() < 1e3);
    }
    #[test]
    fn test_margin_positive() {
        let m = margin_of_safety(1000.0e6, 200.0e6, 1.5);
        assert!((m - 2.333).abs() < 0.01);
    }
    #[test]
    fn test_material_by_name() {
        assert!(Material::by_name("Inconel 718").is_some());
        assert!(Material::by_name("Fake").is_none());
    }
}
