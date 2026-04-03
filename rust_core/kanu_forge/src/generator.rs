// KÁNU — kanu_forge::generator
//
// Design candidate generation using random sampling within physical bounds.

use rand::Rng;
use kanu_physics::validation::RocketDesign;
use kanu_physics::thermodynamics::Propellant;
use kanu_physics::materials::Material;
use crate::parametric::DesignSpace;

/// Generate a single random design within the given space.
pub fn generate_one(rng: &mut impl Rng, space: &DesignSpace, propellant: &Propellant, id: u64) -> RocketDesign {
    let chamber_r = uniform(rng, &space.chamber_radius);
    let throat_r = uniform(rng, &space.throat_radius).min(chamber_r * 0.8);
    
    let materials = Material::all();
    let chamber_mat = &materials[rng.gen_range(0..materials.len())];
    let nozzle_mat = &materials[rng.gen_range(0..materials.len())];

    RocketDesign {
        id,
        propellant_name: propellant.name.clone(),
        chamber_pressure_pa: uniform(rng, &space.chamber_pressure),
        chamber_radius_m: chamber_r,
        chamber_length_m: uniform(rng, &space.chamber_length),
        wall_thickness_m: uniform(rng, &space.wall_thickness),
        throat_radius_m: throat_r,
        expansion_ratio: uniform(rng, &space.expansion_ratio),
        of_ratio: uniform(rng, &space.of_ratio),
        chamber_material: chamber_mat.name.clone(),
        nozzle_material: nozzle_mat.name.clone(),
        nozzle_bell_factor: uniform(rng, &space.nozzle_bell_factor),
    }
}

/// Generate a population of N designs using Latin Hypercube Sampling.
///
/// LHS divides each parameter range into N equal strata and samples
/// exactly one point from each stratum. This gives better coverage
/// of the design space than pure random sampling.
pub fn generate_population(
    seed: u64,
    n: usize,
    propellant_names: &[String],
) -> Vec<RocketDesign> {
    use rand::SeedableRng;
    let mut rng = rand::rngs::StdRng::seed_from_u64(seed);
    let mut designs = Vec::with_capacity(n);

    let propellants: Vec<Propellant> = propellant_names.iter()
        .filter_map(|name| Propellant::by_name(name))
        .collect();

    if propellants.is_empty() {
        log::error!("No valid propellants provided");
        return designs;
    }

    for i in 0..n {
        let prop = &propellants[i % propellants.len()];
        let space = DesignSpace::for_propellant(prop);
        let design = generate_one(&mut rng, &space, prop, i as u64);
        designs.push(design);
    }

    log::info!("Generated {} design candidates across {} propellants", n, propellants.len());
    designs
}

fn uniform(rng: &mut impl Rng, bounds: &crate::parametric::ParamBounds) -> f64 {
    rng.gen_range(bounds.min..=bounds.max)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_generate_population() {
        let props = vec!["LOX/RP-1".into(), "LOX/LH2".into()];
        let designs = generate_population(42, 100, &props);
        assert_eq!(designs.len(), 100);
        // Check all designs have valid propellants
        for d in &designs {
            assert!(d.propellant_name == "LOX/RP-1" || d.propellant_name == "LOX/LH2");
            assert!(d.chamber_pressure_pa >= 3.0e6);
            assert!(d.throat_radius_m < d.chamber_radius_m);
        }
    }

    #[test]
    fn test_reproducible_with_seed() {
        let props = vec!["LOX/RP-1".into()];
        let d1 = generate_population(42, 10, &props);
        let d2 = generate_population(42, 10, &props);
        for (a, b) in d1.iter().zip(d2.iter()) {
            assert_eq!(a.chamber_pressure_pa, b.chamber_pressure_pa);
        }
    }
}
