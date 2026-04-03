// KÁNU — kanu_forge::mutation
//
// Genetic operators: crossover and mutation for evolutionary optimization.

use rand::Rng;
use rand_distr::{Normal, Distribution};
use kanu_physics::validation::RocketDesign;
use crate::parametric::DesignSpace;

/// Mutate a design by applying Gaussian perturbation to each parameter.
///
/// Each parameter is perturbed by: x' = x + N(0, σ·range)
/// where σ is the mutation_strength (typically 0.05 = 5% of range).
pub fn mutate(rng: &mut impl Rng, design: &RocketDesign, space: &DesignSpace, strength: f64, new_id: u64) -> RocketDesign {
    let mut d = design.clone();
    d.id = new_id;

    d.chamber_pressure_pa = perturb(rng, d.chamber_pressure_pa, &space.chamber_pressure, strength);
    d.chamber_radius_m = perturb(rng, d.chamber_radius_m, &space.chamber_radius, strength);
    d.chamber_length_m = perturb(rng, d.chamber_length_m, &space.chamber_length, strength);
    d.wall_thickness_m = perturb(rng, d.wall_thickness_m, &space.wall_thickness, strength);
    d.throat_radius_m = perturb(rng, d.throat_radius_m, &space.throat_radius, strength);
    d.expansion_ratio = perturb(rng, d.expansion_ratio, &space.expansion_ratio, strength);
    d.of_ratio = perturb(rng, d.of_ratio, &space.of_ratio, strength);
    d.nozzle_bell_factor = perturb(rng, d.nozzle_bell_factor, &space.nozzle_bell_factor, strength);

    // Ensure throat < chamber (geometry constraint)
    d.throat_radius_m = d.throat_radius_m.min(d.chamber_radius_m * 0.8);
    d
}

/// Simulated Binary Crossover (SBX) between two parents.
///
/// SBX produces children near parents with a probability distribution
/// that mimics single-point crossover in binary representation.
/// η_c is the distribution index (higher = children closer to parents).
pub fn crossover_sbx(rng: &mut impl Rng, p1: &RocketDesign, p2: &RocketDesign, space: &DesignSpace, eta_c: f64, id1: u64, id2: u64) -> (RocketDesign, RocketDesign) {
    let mut c1 = p1.clone();
    let mut c2 = p2.clone();
    c1.id = id1;
    c2.id = id2;

    sbx_param(rng, &mut c1.chamber_pressure_pa, &mut c2.chamber_pressure_pa, &space.chamber_pressure, eta_c);
    sbx_param(rng, &mut c1.chamber_radius_m, &mut c2.chamber_radius_m, &space.chamber_radius, eta_c);
    sbx_param(rng, &mut c1.chamber_length_m, &mut c2.chamber_length_m, &space.chamber_length, eta_c);
    sbx_param(rng, &mut c1.wall_thickness_m, &mut c2.wall_thickness_m, &space.wall_thickness, eta_c);
    sbx_param(rng, &mut c1.throat_radius_m, &mut c2.throat_radius_m, &space.throat_radius, eta_c);
    sbx_param(rng, &mut c1.expansion_ratio, &mut c2.expansion_ratio, &space.expansion_ratio, eta_c);
    sbx_param(rng, &mut c1.of_ratio, &mut c2.of_ratio, &space.of_ratio, eta_c);
    sbx_param(rng, &mut c1.nozzle_bell_factor, &mut c2.nozzle_bell_factor, &space.nozzle_bell_factor, eta_c);

    // Inherit propellant from parent 1 for both children (same propellant class)
    c1.propellant_name = p1.propellant_name.clone();
    c2.propellant_name = p1.propellant_name.clone();

    // Enforce geometry constraint
    c1.throat_radius_m = c1.throat_radius_m.min(c1.chamber_radius_m * 0.8);
    c2.throat_radius_m = c2.throat_radius_m.min(c2.chamber_radius_m * 0.8);

    (c1, c2)
}

fn perturb(rng: &mut impl Rng, value: f64, bounds: &crate::parametric::ParamBounds, strength: f64) -> f64 {
    let sigma = strength * bounds.range();
    let normal = Normal::new(0.0, sigma).unwrap();
    let delta: f64 = normal.sample(rng);
    bounds.clamp(value + delta)
}

fn sbx_param(rng: &mut impl Rng, x1: &mut f64, x2: &mut f64, bounds: &crate::parametric::ParamBounds, eta: f64) {
    if rng.gen::<f64>() > 0.5 { return; } // 50% chance of crossover per parameter
    
    let u: f64 = rng.gen();
    let beta = if u <= 0.5 {
        (2.0 * u).powf(1.0 / (eta + 1.0))
    } else {
        (1.0 / (2.0 * (1.0 - u))).powf(1.0 / (eta + 1.0))
    };

    let v1 = *x1;
    let v2 = *x2;
    *x1 = bounds.clamp(0.5 * ((1.0 + beta) * v1 + (1.0 - beta) * v2));
    *x2 = bounds.clamp(0.5 * ((1.0 - beta) * v1 + (1.0 + beta) * v2));
}

#[cfg(test)]
mod tests {
    use super::*;
    use rand::SeedableRng;
    use kanu_physics::thermodynamics::Propellant;

    fn sample_design() -> RocketDesign {
        RocketDesign {
            id: 0, propellant_name: "LOX/RP-1".into(),
            chamber_pressure_pa: 10.0e6, chamber_radius_m: 0.15,
            chamber_length_m: 0.4, wall_thickness_m: 0.006,
            throat_radius_m: 0.08, expansion_ratio: 15.0,
            of_ratio: 2.56, chamber_material: "Inconel 718".into(),
            nozzle_material: "Niobium C-103".into(), nozzle_bell_factor: 0.8,
        }
    }

    #[test]
    fn test_mutation_stays_in_bounds() {
        let mut rng = rand::rngs::StdRng::seed_from_u64(42);
        let prop = Propellant::lox_rp1();
        let space = DesignSpace::for_propellant(&prop);
        let d = sample_design();
        for i in 0..100 {
            let m = mutate(&mut rng, &d, &space, 0.1, i);
            assert!(space.chamber_pressure.contains(m.chamber_pressure_pa));
            assert!(m.throat_radius_m <= m.chamber_radius_m * 0.8 + 1e-10);
        }
    }

    #[test]
    fn test_crossover() {
        let mut rng = rand::rngs::StdRng::seed_from_u64(42);
        let prop = Propellant::lox_rp1();
        let space = DesignSpace::for_propellant(&prop);
        let p1 = sample_design();
        let mut p2 = sample_design();
        p2.chamber_pressure_pa = 20.0e6;
        let (c1, c2) = crossover_sbx(&mut rng, &p1, &p2, &space, 20.0, 100, 101);
        assert!(space.chamber_pressure.contains(c1.chamber_pressure_pa));
        assert!(space.chamber_pressure.contains(c2.chamber_pressure_pa));
    }
}
