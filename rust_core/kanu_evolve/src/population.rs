// KÁNU — kanu_evolve::population
//
// Population management for evolutionary optimization.

use serde::{Deserialize, Serialize};
use kanu_physics::validation::RocketDesign;
use crate::objectives::Fitness;

/// An individual in the population: design + fitness + NSGA-II metadata.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Individual {
    pub design: RocketDesign,
    pub fitness: Fitness,
    /// NSGA-II: Pareto front rank (0 = first front = best)
    pub rank: usize,
    /// NSGA-II: Crowding distance (higher = more isolated = preferred)
    pub crowding_distance: f64,
}

/// A generation of the evolutionary process.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Generation {
    pub number: usize,
    pub individuals: Vec<Individual>,
    /// Number of feasible individuals
    pub num_feasible: usize,
    /// Number of Pareto-optimal individuals (rank 0)
    pub num_pareto_front: usize,
    /// Best Isp in this generation
    pub best_isp: f64,
    /// Best thrust in this generation
    pub best_thrust: f64,
}

impl Generation {
    pub fn new(number: usize, individuals: Vec<Individual>) -> Self {
        let num_feasible = individuals.iter().filter(|i| i.fitness.feasible).count();
        let num_pareto = individuals.iter().filter(|i| i.rank == 0).count();
        let best_isp = individuals.iter()
            .filter(|i| i.fitness.feasible)
            .map(|i| i.fitness.performance.isp_s)
            .fold(0.0_f64, f64::max);
        let best_thrust = individuals.iter()
            .filter(|i| i.fitness.feasible)
            .map(|i| i.fitness.performance.thrust_n)
            .fold(0.0_f64, f64::max);

        Self { number, individuals, num_feasible, num_pareto_front: num_pareto, best_isp, best_thrust }
    }
}
