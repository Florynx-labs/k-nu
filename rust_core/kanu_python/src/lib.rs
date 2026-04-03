// KÁNU — kanu_python
//
// PyO3 bridge: exposes Rust engine to Python orchestrator.
// Follows the "Core/Adapter" pattern — thin wrappers around pure Rust logic.

use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use serde_json;

use kanu_physics::validation::{RocketDesign, evaluate_design};
use kanu_physics::thermodynamics::Propellant;
use kanu_forge::generator::generate_population;
use kanu_evolve::nsga2::{run_nsga2, NsgaIIConfig};
use kanu_world_model::stress::{stress_test_design, filter_by_stress_test};

/// Initialize the Rust logging system.
#[pyfunction]
fn init_logging() {
    let _ = env_logger::try_init();
}

/// Generate a population of random rocket engine designs.
///
/// Args:
///     seed: Random seed for reproducibility
///     count: Number of designs to generate
///     propellants_json: JSON array of propellant names, e.g. '["LOX/RP-1","LOX/LH2"]'
///
/// Returns:
///     JSON string of Vec<RocketDesign>
#[pyfunction]
fn forge_designs(seed: u64, count: usize, propellants_json: &str) -> PyResult<String> {
    let prop_names: Vec<String> = serde_json::from_str(propellants_json)
        .map_err(|e| PyValueError::new_err(format!("Invalid propellants JSON: {e}")))?;
    
    let designs = generate_population(seed, count, &prop_names);
    serde_json::to_string(&designs)
        .map_err(|e| PyValueError::new_err(format!("Serialization error: {e}")))
}

/// Evaluate a single design and return validation + performance.
///
/// Args:
///     design_json: JSON string of a RocketDesign
///     ambient_pressure_pa: Ambient pressure in Pascals
///
/// Returns:
///     JSON string of ValidationResult
#[pyfunction]
fn validate_design(design_json: &str, ambient_pressure_pa: f64) -> PyResult<String> {
    let design: RocketDesign = serde_json::from_str(design_json)
        .map_err(|e| PyValueError::new_err(format!("Invalid design JSON: {e}")))?;
    
    let result = evaluate_design(&design, ambient_pressure_pa);
    serde_json::to_string(&result)
        .map_err(|e| PyValueError::new_err(format!("Serialization error: {e}")))
}

/// Validate a batch of designs. Returns JSON array of ValidationResults.
#[pyfunction]
fn validate_designs_batch(designs_json: &str, ambient_pressure_pa: f64) -> PyResult<String> {
    let designs: Vec<RocketDesign> = serde_json::from_str(designs_json)
        .map_err(|e| PyValueError::new_err(format!("Invalid designs JSON: {e}")))?;
    
    let results: Vec<_> = designs.iter()
        .map(|d| evaluate_design(d, ambient_pressure_pa))
        .collect();
    
    serde_json::to_string(&results)
        .map_err(|e| PyValueError::new_err(format!("Serialization error: {e}")))
}

/// Run NSGA-II optimization on designs.
///
/// Args:
///     designs_json: JSON array of initial RocketDesign population
///     config_json: JSON object with optimization parameters:
///         population_size, generations, crossover_prob, mutation_prob,
///         mutation_strength, sbx_eta, ambient_pressure_pa, seed
///
/// Returns:
///     JSON string of Vec<Generation> (optimization history)
#[pyfunction]
fn run_optimization(designs_json: &str, config_json: &str) -> PyResult<String> {
    let designs: Vec<RocketDesign> = serde_json::from_str(designs_json)
        .map_err(|e| PyValueError::new_err(format!("Invalid designs JSON: {e}")))?;

    let cfg: serde_json::Value = serde_json::from_str(config_json)
        .map_err(|e| PyValueError::new_err(format!("Invalid config JSON: {e}")))?;

    let config = NsgaIIConfig {
        population_size: cfg.get("population_size").and_then(|v| v.as_u64()).unwrap_or(200) as usize,
        generations: cfg.get("generations").and_then(|v| v.as_u64()).unwrap_or(100) as usize,
        crossover_prob: cfg.get("crossover_prob").and_then(|v| v.as_f64()).unwrap_or(0.9),
        mutation_prob: cfg.get("mutation_prob").and_then(|v| v.as_f64()).unwrap_or(0.1),
        mutation_strength: cfg.get("mutation_strength").and_then(|v| v.as_f64()).unwrap_or(0.05),
        sbx_eta: cfg.get("sbx_eta").and_then(|v| v.as_f64()).unwrap_or(20.0),
        ambient_pressure_pa: cfg.get("ambient_pressure_pa").and_then(|v| v.as_f64()).unwrap_or(101325.0),
        seed: cfg.get("seed").and_then(|v| v.as_u64()).unwrap_or(42),
    };

    let history = run_nsga2(designs, &config);
    serde_json::to_string(&history)
        .map_err(|e| PyValueError::new_err(format!("Serialization error: {e}")))
}

/// Stress test a single design across multiple conditions.
///
/// Returns JSON string of StressReport.
#[pyfunction]
fn stress_test(design_json: &str) -> PyResult<String> {
    let design: RocketDesign = serde_json::from_str(design_json)
        .map_err(|e| PyValueError::new_err(format!("Invalid design JSON: {e}")))?;
    
    let report = stress_test_design(&design);
    serde_json::to_string(&report)
        .map_err(|e| PyValueError::new_err(format!("Serialization error: {e}")))
}

/// Stress test a batch of designs and return only those passing.
///
/// Returns JSON array of [design, stress_report] pairs.
#[pyfunction]
fn stress_test_batch(designs_json: &str) -> PyResult<String> {
    let designs: Vec<RocketDesign> = serde_json::from_str(designs_json)
        .map_err(|e| PyValueError::new_err(format!("Invalid designs JSON: {e}")))?;
    
    let results = filter_by_stress_test(&designs);
    let output: Vec<serde_json::Value> = results.into_iter()
        .map(|(d, r)| serde_json::json!({"design": d, "stress_report": r}))
        .collect();
    
    serde_json::to_string(&output)
        .map_err(|e| PyValueError::new_err(format!("Serialization error: {e}")))
}

/// Get available propellants as JSON.
#[pyfunction]
fn get_propellants() -> PyResult<String> {
    let props = Propellant::all();
    serde_json::to_string(&props)
        .map_err(|e| PyValueError::new_err(format!("Serialization error: {e}")))
}

/// Get available materials as JSON.
#[pyfunction]
fn get_materials() -> PyResult<String> {
    let mats = kanu_physics::materials::Material::all();
    serde_json::to_string(&mats)
        .map_err(|e| PyValueError::new_err(format!("Serialization error: {e}")))
}

/// Python module definition.
#[pymodule]
fn kanu_engine(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(init_logging, m)?)?;
    m.add_function(wrap_pyfunction!(forge_designs, m)?)?;
    m.add_function(wrap_pyfunction!(validate_design, m)?)?;
    m.add_function(wrap_pyfunction!(validate_designs_batch, m)?)?;
    m.add_function(wrap_pyfunction!(run_optimization, m)?)?;
    m.add_function(wrap_pyfunction!(stress_test, m)?)?;
    m.add_function(wrap_pyfunction!(stress_test_batch, m)?)?;
    m.add_function(wrap_pyfunction!(get_propellants, m)?)?;
    m.add_function(wrap_pyfunction!(get_materials, m)?)?;
    Ok(())
}
