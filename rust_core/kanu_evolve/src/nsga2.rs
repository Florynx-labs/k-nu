// KÁNU — kanu_evolve::nsga2
//
// Full NSGA-II (Non-dominated Sorting Genetic Algorithm II) implementation.
// Reference: Deb et al. (2002) "A Fast and Elitist Multiobjective Genetic Algorithm: NSGA-II"

use rand::Rng;
use rand::SeedableRng;
use kanu_physics::validation::RocketDesign;
use kanu_physics::thermodynamics::Propellant;
use kanu_forge::parametric::DesignSpace;
use kanu_forge::mutation::{mutate, crossover_sbx};
use crate::objectives::evaluate_fitness;
use crate::population::{Individual, Generation};

/// NSGA-II optimizer configuration.
pub struct NsgaIIConfig {
    pub population_size: usize,
    pub generations: usize,
    pub crossover_prob: f64,
    pub mutation_prob: f64,
    pub mutation_strength: f64,
    pub sbx_eta: f64,
    pub ambient_pressure_pa: f64,
    pub seed: u64,
}

impl Default for NsgaIIConfig {
    fn default() -> Self {
        Self {
            population_size: 200,
            generations: 100,
            crossover_prob: 0.9,
            mutation_prob: 0.1,
            mutation_strength: 0.05,
            sbx_eta: 20.0,
            ambient_pressure_pa: kanu_physics::P_ATM_SEA_LEVEL,
            seed: 42,
        }
    }
}

/// Run NSGA-II optimization on an initial population.
pub fn run_nsga2(
    initial_designs: Vec<RocketDesign>,
    config: &NsgaIIConfig,
) -> Vec<Generation> {
    let mut rng = rand::rngs::StdRng::seed_from_u64(config.seed);
    let mut history: Vec<Generation> = Vec::new();

    // Evaluate initial population
    let mut pop: Vec<Individual> = initial_designs.into_iter()
        .filter_map(|d| {
            evaluate_fitness(&d, config.ambient_pressure_pa).map(|f| Individual {
                design: d, fitness: f, rank: 0, crowding_distance: 0.0,
            })
        })
        .collect();

    // Trim or pad to population_size
    pop.truncate(config.population_size);

    // Assign ranks and crowding distances
    fast_non_dominated_sort(&mut pop);
    assign_crowding_distance(&mut pop);

    log::info!("NSGA-II: Initial pop = {}, feasible = {}",
        pop.len(), pop.iter().filter(|i| i.fitness.feasible).count());

    history.push(Generation::new(0, pop.clone()));

    let mut next_id = pop.len() as u64;

    for gen in 1..=config.generations {
        // Create offspring via tournament selection + crossover + mutation
        let mut offspring = Vec::with_capacity(config.population_size);

        while offspring.len() < config.population_size {
            let p1 = tournament_select(&pop, &mut rng);
            let p2 = tournament_select(&pop, &mut rng);

            let prop = Propellant::by_name(&p1.design.propellant_name)
                .unwrap_or_else(Propellant::lox_rp1);
            let space = DesignSpace::for_propellant(&prop);

            if rng.gen::<f64>() < config.crossover_prob {
                let (c1, c2) = crossover_sbx(&mut rng, &p1.design, &p2.design, &space, config.sbx_eta, next_id, next_id + 1);
                next_id += 2;
                
                let c1 = if rng.gen::<f64>() < config.mutation_prob {
                    mutate(&mut rng, &c1, &space, config.mutation_strength, next_id)
                } else { c1 };
                let c2 = if rng.gen::<f64>() < config.mutation_prob {
                    next_id += 1;
                    mutate(&mut rng, &c2, &space, config.mutation_strength, next_id)
                } else { c2 };

                if let Some(f) = evaluate_fitness(&c1, config.ambient_pressure_pa) {
                    offspring.push(Individual { design: c1, fitness: f, rank: 0, crowding_distance: 0.0 });
                }
                if let Some(f) = evaluate_fitness(&c2, config.ambient_pressure_pa) {
                    offspring.push(Individual { design: c2, fitness: f, rank: 0, crowding_distance: 0.0 });
                }
            } else {
                let m = mutate(&mut rng, &p1.design, &space, config.mutation_strength, next_id);
                next_id += 1;
                if let Some(f) = evaluate_fitness(&m, config.ambient_pressure_pa) {
                    offspring.push(Individual { design: m, fitness: f, rank: 0, crowding_distance: 0.0 });
                }
            }
        }

        // Combine parent + offspring (elitism)
        let mut combined = pop;
        combined.extend(offspring);

        // Non-dominated sort on combined population
        fast_non_dominated_sort(&mut combined);
        assign_crowding_distance(&mut combined);

        // Select next generation: fill by front, then by crowding distance
        pop = select_next_generation(&mut combined, config.population_size);

        if gen % 10 == 0 || gen == config.generations {
            let g = Generation::new(gen, pop.clone());
            log::info!("Gen {}: feasible={}, pareto_front={}, best_isp={:.1}s, best_thrust={:.0}N",
                gen, g.num_feasible, g.num_pareto_front, g.best_isp, g.best_thrust);
            history.push(g);
        }
    }

    history
}

/// Fast Non-Dominated Sort (Deb et al. 2002, Algorithm 1).
/// Assigns Pareto front rank to each individual.
/// Feasible solutions always dominate infeasible ones.
pub fn fast_non_dominated_sort(pop: &mut Vec<Individual>) {
    let n = pop.len();
    let mut domination_count = vec![0usize; n];
    let mut dominated_set: Vec<Vec<usize>> = vec![Vec::new(); n];
    let mut fronts: Vec<Vec<usize>> = vec![Vec::new()];

    for i in 0..n {
        for j in (i + 1)..n {
            match dominates(&pop[i], &pop[j]) {
                DomResult::Left => {
                    dominated_set[i].push(j);
                    domination_count[j] += 1;
                }
                DomResult::Right => {
                    dominated_set[j].push(i);
                    domination_count[i] += 1;
                }
                DomResult::Neither => {}
            }
        }
        if domination_count[i] == 0 {
            pop[i].rank = 0;
            fronts[0].push(i);
        }
    }

    let mut k = 0;
    while !fronts[k].is_empty() {
        let mut next_front = Vec::new();
        for &i in &fronts[k] {
            for &j in &dominated_set[i] {
                domination_count[j] -= 1;
                if domination_count[j] == 0 {
                    pop[j].rank = k + 1;
                    next_front.push(j);
                }
            }
        }
        k += 1;
        fronts.push(next_front);
    }
}

enum DomResult { Left, Right, Neither }

/// Check if individual a dominates b.
/// Feasible always dominates infeasible. Among infeasible, less violation wins.
fn dominates(a: &Individual, b: &Individual) -> DomResult {
    // Feasibility first
    if a.fitness.feasible && !b.fitness.feasible { return DomResult::Left; }
    if !a.fitness.feasible && b.fitness.feasible { return DomResult::Right; }
    if !a.fitness.feasible && !b.fitness.feasible {
        if a.fitness.constraint_violation < b.fitness.constraint_violation { return DomResult::Left; }
        if a.fitness.constraint_violation > b.fitness.constraint_violation { return DomResult::Right; }
        return DomResult::Neither;
    }

    // Both feasible: Pareto dominance (all objectives in minimize direction)
    let mut a_better = false;
    let mut b_better = false;
    for (oa, ob) in a.fitness.objectives.iter().zip(b.fitness.objectives.iter()) {
        if oa < ob { a_better = true; }
        if ob < oa { b_better = true; }
    }
    if a_better && !b_better { DomResult::Left }
    else if b_better && !a_better { DomResult::Right }
    else { DomResult::Neither }
}

/// Assign crowding distance within each front.
pub fn assign_crowding_distance(pop: &mut Vec<Individual>) {
    let max_rank = pop.iter().map(|i| i.rank).max().unwrap_or(0);
    
    for rank in 0..=max_rank {
        let indices: Vec<usize> = pop.iter().enumerate()
            .filter(|(_, ind)| ind.rank == rank)
            .map(|(i, _)| i)
            .collect();

        if indices.len() <= 2 {
            for &idx in &indices {
                pop[idx].crowding_distance = f64::INFINITY;
            }
            continue;
        }

        for &idx in &indices {
            pop[idx].crowding_distance = 0.0;
        }

        let num_obj = pop[indices[0]].fitness.objectives.len();
        for m in 0..num_obj {
            let mut sorted_idx = indices.clone();
            sorted_idx.sort_by(|&a, &b| {
                pop[a].fitness.objectives[m].partial_cmp(&pop[b].fitness.objectives[m])
                    .unwrap_or(std::cmp::Ordering::Equal)
            });

            // Boundary points get infinite distance
            pop[sorted_idx[0]].crowding_distance = f64::INFINITY;
            pop[*sorted_idx.last().unwrap()].crowding_distance = f64::INFINITY;

            let f_max = pop[*sorted_idx.last().unwrap()].fitness.objectives[m];
            let f_min = pop[sorted_idx[0]].fitness.objectives[m];
            let range = f_max - f_min;
            if range <= 0.0 { continue; }

            for i in 1..(sorted_idx.len() - 1) {
                let prev = pop[sorted_idx[i - 1]].fitness.objectives[m];
                let next = pop[sorted_idx[i + 1]].fitness.objectives[m];
                pop[sorted_idx[i]].crowding_distance += (next - prev) / range;
            }
        }
    }
}

/// Binary tournament selection using crowded comparison operator.
fn tournament_select<'a>(pop: &'a [Individual], rng: &mut impl Rng) -> &'a Individual {
    let i = rng.gen_range(0..pop.len());
    let j = rng.gen_range(0..pop.len());
    crowded_compare(&pop[i], &pop[j])
}

/// Crowded comparison: prefer lower rank, then higher crowding distance.
fn crowded_compare<'a>(a: &'a Individual, b: &'a Individual) -> &'a Individual {
    if a.rank < b.rank { a }
    else if b.rank < a.rank { b }
    else if a.crowding_distance > b.crowding_distance { a }
    else { b }
}

/// Select next generation from sorted combined population.
fn select_next_generation(combined: &mut Vec<Individual>, target_size: usize) -> Vec<Individual> {
    let max_rank = combined.iter().map(|i| i.rank).max().unwrap_or(0);
    let mut next_gen = Vec::with_capacity(target_size);

    for rank in 0..=max_rank {
        let mut front: Vec<Individual> = combined.iter()
            .filter(|i| i.rank == rank)
            .cloned()
            .collect();

        if next_gen.len() + front.len() <= target_size {
            next_gen.extend(front);
        } else {
            // Sort by crowding distance (descending) and take what we need
            front.sort_by(|a, b| b.crowding_distance.partial_cmp(&a.crowding_distance)
                .unwrap_or(std::cmp::Ordering::Equal));
            let remaining = target_size - next_gen.len();
            next_gen.extend(front.into_iter().take(remaining));
            break;
        }
    }

    next_gen
}

#[cfg(test)]
mod tests {
    use super::*;
    use kanu_forge::generator::generate_population;

    #[test]
    fn test_nsga2_runs() {
        let props = vec!["LOX/RP-1".into()];
        let designs = generate_population(42, 50, &props);
        let config = NsgaIIConfig {
            population_size: 30,
            generations: 5,
            ..Default::default()
        };
        let history = run_nsga2(designs, &config);
        assert!(!history.is_empty());
        let last = history.last().unwrap();
        assert!(last.individuals.len() <= 30);
    }

    #[test]
    fn test_non_dominated_sort() {
        // Create a simple scenario with known dominance
        let d = RocketDesign {
            id: 0, propellant_name: "LOX/RP-1".into(),
            chamber_pressure_pa: 10.0e6, chamber_radius_m: 0.15,
            chamber_length_m: 0.4, wall_thickness_m: 0.006,
            throat_radius_m: 0.08, expansion_ratio: 15.0,
            of_ratio: 2.56, chamber_material: "Inconel 718".into(),
            nozzle_material: "Niobium C-103".into(), nozzle_bell_factor: 0.8,
        };
        let f = evaluate_fitness(&d, kanu_physics::P_ATM_SEA_LEVEL).unwrap();
        let mut pop = vec![
            Individual { design: d.clone(), fitness: f.clone(), rank: 0, crowding_distance: 0.0 },
            Individual { design: d.clone(), fitness: f.clone(), rank: 0, crowding_distance: 0.0 },
        ];
        fast_non_dominated_sort(&mut pop);
        // Same fitness → same rank (non-dominating)
        assert_eq!(pop[0].rank, pop[1].rank);
    }
}
