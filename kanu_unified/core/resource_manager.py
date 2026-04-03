"""
Resource Manager
Détecte et gère les ressources système (CPU/GPU)
Adapte dynamiquement l'utilisation selon la charge
"""
import torch
import psutil
import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from threading import Thread, Event
import GPUtil

logger = logging.getLogger(__name__)


@dataclass
class SystemResources:
    """État des ressources système"""
    cpu_count: int
    cpu_percent: float
    ram_total_gb: float
    ram_available_gb: float
    ram_percent: float
    
    gpu_available: bool
    gpu_count: int
    gpu_names: List[str]
    gpu_memory_total_gb: List[float]
    gpu_memory_used_gb: List[float]
    gpu_utilization: List[float]
    
    other_processes_active: bool
    system_load: str  # "low", "medium", "high"


class ResourceManager:
    """
    Gère les ressources système pour entraînement adaptatif
    
    Fonctionnalités:
    - Détection automatique CPU/GPU
    - Monitoring charge système
    - Adaptation dynamique utilisation
    - Prévention surcharge
    """
    
    def __init__(
        self,
        max_gpu_usage: float = 0.95,
        min_gpu_usage: float = 0.30,
        max_cpu_usage: float = 0.90,
        min_cpu_usage: float = 0.30,
        adaptation_interval: int = 10,  # secondes
        enable_adaptive: bool = True
    ):
        self.max_gpu_usage = max_gpu_usage
        self.min_gpu_usage = min_gpu_usage
        self.max_cpu_usage = max_cpu_usage
        self.min_cpu_usage = min_cpu_usage
        self.adaptation_interval = adaptation_interval
        self.enable_adaptive = enable_adaptive
        
        # Detect resources
        self.resources = self.detect_resources()
        
        # Monitoring thread
        self.monitoring = False
        self.monitor_thread = None
        self.stop_event = Event()
        
        # Current usage targets
        self.current_gpu_target = max_gpu_usage
        self.current_cpu_target = max_cpu_usage
        
        logger.info("Resource Manager initialized")
        self._log_resources()
    
    def detect_resources(self) -> SystemResources:
        """Détecte toutes les ressources système"""
        
        # CPU
        cpu_count = psutil.cpu_count(logical=True)
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # RAM
        ram = psutil.virtual_memory()
        ram_total_gb = ram.total / (1024**3)
        ram_available_gb = ram.available / (1024**3)
        ram_percent = ram.percent
        
        # GPU
        gpu_available = torch.cuda.is_available()
        gpu_count = 0
        gpu_names = []
        gpu_memory_total_gb = []
        gpu_memory_used_gb = []
        gpu_utilization = []
        
        if gpu_available:
            gpu_count = torch.cuda.device_count()
            
            try:
                gpus = GPUtil.getGPUs()
                for gpu in gpus:
                    gpu_names.append(gpu.name)
                    gpu_memory_total_gb.append(gpu.memoryTotal / 1024)
                    gpu_memory_used_gb.append(gpu.memoryUsed / 1024)
                    gpu_utilization.append(gpu.load * 100)
            except:
                # Fallback si GPUtil échoue
                for i in range(gpu_count):
                    gpu_names.append(torch.cuda.get_device_name(i))
                    props = torch.cuda.get_device_properties(i)
                    gpu_memory_total_gb.append(props.total_memory / (1024**3))
                    gpu_memory_used_gb.append(0)
                    gpu_utilization.append(0)
        
        # Détection autres processus
        other_processes = cpu_percent > 50 or ram_percent > 70
        
        # Charge système
        if cpu_percent < 30 and ram_percent < 50:
            system_load = "low"
        elif cpu_percent < 70 and ram_percent < 80:
            system_load = "medium"
        else:
            system_load = "high"
        
        return SystemResources(
            cpu_count=cpu_count,
            cpu_percent=cpu_percent,
            ram_total_gb=ram_total_gb,
            ram_available_gb=ram_available_gb,
            ram_percent=ram_percent,
            gpu_available=gpu_available,
            gpu_count=gpu_count,
            gpu_names=gpu_names,
            gpu_memory_total_gb=gpu_memory_total_gb,
            gpu_memory_used_gb=gpu_memory_used_gb,
            gpu_utilization=gpu_utilization,
            other_processes_active=other_processes,
            system_load=system_load
        )
    
    def _log_resources(self):
        """Log des ressources détectées"""
        r = self.resources
        
        logger.info("System Resources:")
        logger.info(f"  CPU: {r.cpu_count} cores @ {r.cpu_percent:.1f}% usage")
        logger.info(f"  RAM: {r.ram_available_gb:.1f}/{r.ram_total_gb:.1f} GB available ({r.ram_percent:.1f}% used)")
        
        if r.gpu_available:
            logger.info(f"  GPU: {r.gpu_count} device(s)")
            for i, name in enumerate(r.gpu_names):
                logger.info(f"    [{i}] {name}")
                logger.info(f"        Memory: {r.gpu_memory_used_gb[i]:.1f}/{r.gpu_memory_total_gb[i]:.1f} GB")
                logger.info(f"        Utilization: {r.gpu_utilization[i]:.1f}%")
        else:
            logger.info("  GPU: Not available")
        
        logger.info(f"  System Load: {r.system_load}")
    
    def start_monitoring(self):
        """Démarre le monitoring en arrière-plan"""
        if self.monitoring:
            logger.warning("Monitoring already running")
            return
        
        self.monitoring = True
        self.stop_event.clear()
        self.monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Resource monitoring started")
    
    def stop_monitoring(self):
        """Arrête le monitoring"""
        if not self.monitoring:
            return
        
        self.monitoring = False
        self.stop_event.set()
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("Resource monitoring stopped")
    
    def _monitor_loop(self):
        """Boucle de monitoring"""
        while not self.stop_event.is_set():
            # Update resources
            self.resources = self.detect_resources()
            
            # Adapt if enabled
            if self.enable_adaptive:
                self._adapt_usage()
            
            # Wait
            self.stop_event.wait(self.adaptation_interval)
    
    def _adapt_usage(self):
        """Adapte l'utilisation selon la charge système"""
        r = self.resources
        
        # Déterminer nouveau target
        if r.system_load == "low" and not r.other_processes_active:
            # Charge faible → utilisation maximale
            new_gpu_target = self.max_gpu_usage
            new_cpu_target = self.max_cpu_usage
            
        elif r.system_load == "high" or r.other_processes_active:
            # Charge élevée → réduire utilisation
            new_gpu_target = self.min_gpu_usage
            new_cpu_target = self.min_cpu_usage
            
        else:
            # Charge moyenne → utilisation intermédiaire
            new_gpu_target = (self.max_gpu_usage + self.min_gpu_usage) / 2
            new_cpu_target = (self.max_cpu_usage + self.min_cpu_usage) / 2
        
        # Log si changement
        if new_gpu_target != self.current_gpu_target or new_cpu_target != self.current_cpu_target:
            logger.info(f"Adapting resource usage:")
            logger.info(f"  GPU: {self.current_gpu_target*100:.0f}% → {new_gpu_target*100:.0f}%")
            logger.info(f"  CPU: {self.current_cpu_target*100:.0f}% → {new_cpu_target*100:.0f}%")
            logger.info(f"  Reason: System load = {r.system_load}, Other processes = {r.other_processes_active}")
            
            self.current_gpu_target = new_gpu_target
            self.current_cpu_target = new_cpu_target
    
    def get_optimal_batch_size(self, base_batch_size: int, device: str = "cuda") -> int:
        """
        Calcule la taille de batch optimale selon ressources disponibles
        
        Args:
            base_batch_size: Taille de batch de base
            device: "cuda" ou "cpu"
        
        Returns:
            Taille de batch ajustée
        """
        if device == "cuda" and self.resources.gpu_available:
            # Ajuster selon mémoire GPU disponible
            gpu_idx = 0
            mem_available = self.resources.gpu_memory_total_gb[gpu_idx] - self.resources.gpu_memory_used_gb[gpu_idx]
            mem_total = self.resources.gpu_memory_total_gb[gpu_idx]
            
            # Si moins de 30% mémoire disponible, réduire batch size
            if mem_available / mem_total < 0.3:
                return max(1, base_batch_size // 2)
            
            # Si beaucoup de mémoire, augmenter
            elif mem_available / mem_total > 0.7:
                return base_batch_size * 2
        
        return base_batch_size
    
    def get_optimal_workers(self) -> int:
        """Calcule le nombre optimal de workers pour DataLoader"""
        # Utiliser 75% des CPU cores, minimum 1, maximum 8
        optimal = max(1, min(8, int(self.resources.cpu_count * 0.75)))
        
        # Réduire si charge CPU élevée
        if self.resources.cpu_percent > 70:
            optimal = max(1, optimal // 2)
        
        return optimal
    
    def should_reduce_usage(self) -> bool:
        """Indique si on doit réduire l'utilisation"""
        return self.resources.system_load == "high" or self.resources.other_processes_active
    
    def get_usage_report(self) -> Dict[str, Any]:
        """Rapport d'utilisation actuel"""
        r = self.resources
        
        return {
            'cpu': {
                'count': r.cpu_count,
                'usage_percent': r.cpu_percent,
                'target_percent': self.current_cpu_target * 100
            },
            'ram': {
                'total_gb': r.ram_total_gb,
                'available_gb': r.ram_available_gb,
                'usage_percent': r.ram_percent
            },
            'gpu': {
                'available': r.gpu_available,
                'count': r.gpu_count,
                'devices': [
                    {
                        'name': r.gpu_names[i],
                        'memory_total_gb': r.gpu_memory_total_gb[i],
                        'memory_used_gb': r.gpu_memory_used_gb[i],
                        'utilization_percent': r.gpu_utilization[i],
                        'target_percent': self.current_gpu_target * 100
                    }
                    for i in range(r.gpu_count)
                ] if r.gpu_available else []
            },
            'system': {
                'load': r.system_load,
                'other_processes_active': r.other_processes_active,
                'adaptive_enabled': self.enable_adaptive
            }
        }
    
    def __enter__(self):
        """Context manager entry"""
        self.start_monitoring()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_monitoring()
