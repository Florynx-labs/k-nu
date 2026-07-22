"""
Training Monitor Module
Provides real-time tracking of hardware resources (CPU/GPU) and training metrics.
"""
import logging
import time
import os
from typing import Dict, Any

try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger(__name__)

class TrainingMonitor:
    """
    Monitors system resources (CPU, RAM, GPU) and records training metrics
    like loss, tokens/s, and dataset growth.
    """
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics_history = []
        logger.info("Training Monitor initialized")
        
    def get_system_load(self) -> Dict[str, Any]:
        """
        Captures the current system resource utilization.
        """
        metrics = {
            'timestamp': time.time(),
            'cpu_percent': 0.0,
            'ram_percent': 0.0,
            'gpu_percent': 0.0,  # Mocked unless pynvml is integrated
        }
        
        if psutil:
            metrics['cpu_percent'] = psutil.cpu_percent(interval=0.1)
            metrics['ram_percent'] = psutil.virtual_memory().percent
            
        return metrics
        
    def record_training_step(self, loss: float, tokens_per_sec: float, gpu_usage: float = None):
        """
        Records the metrics for a single training step.
        """
        current_metrics = self.get_system_load()
        current_metrics.update({
            'loss': loss,
            'tokens_per_sec': tokens_per_sec,
            'elapsed_time_s': time.time() - self.start_time
        })
        
        if gpu_usage is not None:
            current_metrics['gpu_percent'] = gpu_usage
            
        self.metrics_history.append(current_metrics)
        
        # Keep history bounded
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
            
        return current_metrics
        
    def generate_report(self) -> str:
        """
        Generates a human-readable summary of the current training session.
        """
        if not self.metrics_history:
            return "No training data recorded yet."
            
        latest = self.metrics_history[-1]
        elapsed = time.time() - self.start_time
        
        report = f"🎓 INTENSIVE TRAINING MONITORING\n"
        report += f"Duration: {elapsed/3600:.2f} hours\n"
        report += f"Current Loss: {latest.get('loss', 0.0):.4f}\n"
        report += f"Tokens/sec: {latest.get('tokens_per_sec', 0.0):.1f}\n"
        report += f"CPU Usage: {latest.get('cpu_percent', 0.0)}%\n"
        report += f"RAM Usage: {latest.get('ram_percent', 0.0)}%\n"
        if latest.get('gpu_percent') > 0:
            report += f"GPU Usage: {latest.get('gpu_percent')}%\n"
            
        return report
