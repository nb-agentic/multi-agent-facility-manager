"""
Memory Management System for IntelliCenter

Implements comprehensive memory optimization for RTX 4060 constraints (8GB limit, 7GB trigger).
Features LRU cache, dynamic model loading/unloading, and memory monitoring.
"""

import gc
import time
import psutil
import threading
from collections import OrderedDict
from typing import Dict, Any, Optional, List, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class MemoryPriority(Enum):
    """Memory priority levels for model management"""
    CRITICAL = 1    # Security, emergency systems
    HIGH = 2        # HVAC, power management
    MEDIUM = 3      # Network, coordination
    LOW = 4         # Analytics, reporting


@dataclass
class ModelInfo:
    """Information about a loaded model"""
    model_id: str
    model_instance: Any
    priority: MemoryPriority
    last_used: float
    usage_count: int
    estimated_memory_mb: float
    load_time: float
    agent_type: str


@dataclass
class MemoryStats:
    """Current memory statistics"""
    total_memory_gb: float
    used_memory_gb: float
    available_memory_gb: float
    memory_percent: float
    gpu_memory_gb: Optional[float] = None
    gpu_used_gb: Optional[float] = None
    active_models: int = 0
    estimated_model_memory_mb: float = 0.0


class LRUModelCache:
    """LRU cache implementation for model management"""
    
    def __init__(self, max_size: int = 2):
        self.max_size = max_size
        self.cache: OrderedDict[str, ModelInfo] = OrderedDict()
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[ModelInfo]:
        """Get model from cache and mark as recently used"""
        with self._lock:
            if key in self.cache:
                # Move to end (most recently used)
                model_info = self.cache.pop(key)
                model_info.last_used = time.time()
                model_info.usage_count += 1
                self.cache[key] = model_info
                return model_info
            return None
    
    def put(self, key: str, model_info: ModelInfo) -> Optional[ModelInfo]:
        """Add model to cache, return evicted model if any"""
        with self._lock:
            evicted = None
            
            if key in self.cache:
                # Update existing
                self.cache.pop(key)
            elif len(self.cache) >= self.max_size:
                # Evict least recently used
                lru_key, evicted = self.cache.popitem(last=False)
                logger.info(f"Evicting LRU model: {lru_key}")
            
            self.cache[key] = model_info
            return evicted
    
    def remove(self, key: str) -> Optional[ModelInfo]:
        """Remove model from cache"""
        with self._lock:
            return self.cache.pop(key, None)
    
    def clear(self):
        """Clear all models from cache"""
        with self._lock:
            evicted = list(self.cache.values())
            self.cache.clear()
            return evicted
    
    def get_lru_key(self) -> Optional[str]:
        """Get least recently used key"""
        with self._lock:
            if self.cache:
                return next(iter(self.cache))
            return None
    
    def get_all_models(self) -> List[ModelInfo]:
        """Get all cached models"""
        with self._lock:
            return list(self.cache.values())
    
    def size(self) -> int:
        """Get current cache size"""
        with self._lock:
            return len(self.cache)


class MemoryOptimizer:
    """
    Comprehensive memory optimization system for RTX 4060 constraints.
    
    Features:
    - LRU cache for model management
    - Dynamic model loading/unloading
    - Memory monitoring and cleanup triggers
    - Max concurrent models (2 for RTX 4060)
    - Memory checks before model loading
    - Cleanup routines for 7GB threshold
    """
    
    def __init__(self, 
                 max_concurrent_models: int = 2,
                 memory_threshold_gb: float = 7.0,
                 max_memory_gb: float = 8.0,
                 cleanup_interval_seconds: int = 30):
        """
        Initialize memory optimizer
        
        Args:
            max_concurrent_models: Maximum models to keep in memory (2 for RTX 4060)
            memory_threshold_gb: Trigger cleanup at this threshold (7GB for RTX 4060)
            max_memory_gb: Maximum system memory (8GB for RTX 4060)
            cleanup_interval_seconds: How often to run cleanup checks
        """
        self.max_concurrent_models = max_concurrent_models
        self.memory_threshold_gb = memory_threshold_gb
        self.max_memory_gb = max_memory_gb
        self.cleanup_interval = cleanup_interval_seconds
        
        # LRU cache for models
        self.model_cache = LRUModelCache(max_size=max_concurrent_models)
        
        # Memory monitoring
        self._monitoring_active = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._cleanup_callbacks: List[Callable[[], None]] = []
        
        # Statistics
        self.cleanup_count = 0
        self.eviction_count = 0
        self.load_count = 0
        
        # Thread safety
        self._lock = threading.RLock()
        
        logger.info(f"MemoryOptimizer initialized: {max_concurrent_models} models, "
                   f"{memory_threshold_gb}GB threshold, {max_memory_gb}GB max")
    
    def start_monitoring(self):
        """Start background memory monitoring"""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._monitor_thread = threading.Thread(target=self._monitor_memory, daemon=True)
        self._monitor_thread.start()
        logger.info("Memory monitoring started")
    
    def stop_monitoring(self):
        """Stop background memory monitoring"""
        self._monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
        logger.info("Memory monitoring stopped")
    
    def _monitor_memory(self):
        """Background memory monitoring loop"""
        while self._monitoring_active:
            try:
                stats = self.get_memory_stats()
                
                if stats.used_memory_gb >= self.memory_threshold_gb:
                    logger.warning(f"Memory threshold exceeded: {stats.used_memory_gb:.1f}GB >= {self.memory_threshold_gb}GB")
                    self.cleanup_memory(force=True)
                
                time.sleep(self.cleanup_interval)
                
            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")
                time.sleep(self.cleanup_interval)
    
    def get_memory_stats(self) -> MemoryStats:
        """Get current memory statistics"""
        memory = psutil.virtual_memory()
        
        stats = MemoryStats(
            total_memory_gb=memory.total / (1024**3),
            used_memory_gb=memory.used / (1024**3),
            available_memory_gb=memory.available / (1024**3),
            memory_percent=memory.percent,
            active_models=self.model_cache.size(),
            estimated_model_memory_mb=sum(m.estimated_memory_mb for m in self.model_cache.get_all_models())
        )
        
        # Try to get GPU memory if available
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]  # Assume single GPU (RTX 4060)
                stats.gpu_memory_gb = gpu.memoryTotal / 1024
                stats.gpu_used_gb = gpu.memoryUsed / 1024
        except ImportError:
            pass  # GPU monitoring not available
        
        return stats
    
    def can_load_model(self, estimated_memory_mb: float) -> Tuple[bool, str]:
        """
        Check if a model can be loaded given current memory constraints
        
        Returns:
            (can_load, reason)
        """
        stats = self.get_memory_stats()
        
        # Check if we're at model limit
        if self.model_cache.size() >= self.max_concurrent_models:
            return False, f"Maximum concurrent models reached ({self.max_concurrent_models})"
        
        # Check memory threshold
        estimated_total_gb = stats.used_memory_gb + (estimated_memory_mb / 1024)
        if estimated_total_gb >= self.memory_threshold_gb:
            return False, f"Would exceed memory threshold: {estimated_total_gb:.1f}GB >= {self.memory_threshold_gb}GB"
        
        # Check absolute maximum
        if estimated_total_gb >= self.max_memory_gb:
            return False, f"Would exceed maximum memory: {estimated_total_gb:.1f}GB >= {self.max_memory_gb}GB"
        
        return True, "Memory check passed"
    
    @contextmanager
    def load_model(self, model_id: str, model_factory: Callable[[], Any], 
                   priority: MemoryPriority, agent_type: str, 
                   estimated_memory_mb: float = 500.0):
        """
        Context manager for loading and managing models
        
        Args:
            model_id: Unique identifier for the model
            model_factory: Function that creates the model instance
            priority: Memory priority level
            agent_type: Type of agent using the model
            estimated_memory_mb: Estimated memory usage in MB
        """
        model_info = None
        
        try:
            # Check if model is already cached
            model_info = self.model_cache.get(model_id)
            
            if model_info is None:
                # Check if we can load the model
                can_load, reason = self.can_load_model(estimated_memory_mb)
                
                if not can_load:
                    # Try cleanup and check again
                    self.cleanup_memory(force=True)
                    can_load, reason = self.can_load_model(estimated_memory_mb)
                    
                    if not can_load:
                        raise MemoryError(f"Cannot load model {model_id}: {reason}")
                
                # Load the model
                logger.info(f"Loading model {model_id} for {agent_type} agent")
                start_time = time.time()
                
                model_instance = model_factory()
                load_time = time.time() - start_time
                
                model_info = ModelInfo(
                    model_id=model_id,
                    model_instance=model_instance,
                    priority=priority,
                    last_used=time.time(),
                    usage_count=1,
                    estimated_memory_mb=estimated_memory_mb,
                    load_time=load_time,
                    agent_type=agent_type
                )
                
                # Add to cache (may evict LRU model)
                evicted = self.model_cache.put(model_id, model_info)
                if evicted:
                    self._cleanup_model(evicted)
                    self.eviction_count += 1
                
                self.load_count += 1
                logger.info(f"Model {model_id} loaded in {load_time:.2f}s")
            
            yield model_info.model_instance
            
        except Exception as e:
            logger.error(f"Error loading model {model_id}: {e}")
            raise
        
        finally:
            # Update usage statistics
            if model_info:
                model_info.last_used = time.time()
    
    def unload_model(self, model_id: str) -> bool:
        """
        Manually unload a specific model
        
        Returns:
            True if model was unloaded, False if not found
        """
        with self._lock:
            model_info = self.model_cache.remove(model_id)
            if model_info:
                self._cleanup_model(model_info)
                logger.info(f"Manually unloaded model: {model_id}")
                return True
            return False
    
    def cleanup_memory(self, force: bool = False) -> int:
        """
        Perform memory cleanup based on current usage
        
        Args:
            force: Force cleanup even if not needed
            
        Returns:
            Number of models cleaned up
        """
        with self._lock:
            stats = self.get_memory_stats()
            cleaned_count = 0
            
            # Determine if cleanup is needed
            needs_cleanup = (
                force or 
                stats.used_memory_gb >= self.memory_threshold_gb or
                stats.memory_percent >= 85.0
            )
            
            if not needs_cleanup:
                return 0
            
            logger.info(f"Starting memory cleanup - Memory: {stats.used_memory_gb:.1f}GB ({stats.memory_percent:.1f}%)")
            
            # Get models sorted by priority and usage
            models = self.model_cache.get_all_models()
            
            # Sort by priority (higher priority = lower number = keep longer)
            # Then by last used time (older = evict first)
            models.sort(key=lambda m: (m.priority.value, m.last_used))
            
            # Remove models until we're under threshold or have minimum models
            target_models = max(1, self.max_concurrent_models // 2)  # Keep at least 1, prefer half
            
            while (len(models) > target_models and 
                   (stats.used_memory_gb >= self.memory_threshold_gb * 0.9 or force)):
                
                model_to_remove = models.pop(0)  # Remove lowest priority, oldest
                
                if self.model_cache.remove(model_to_remove.model_id):
                    self._cleanup_model(model_to_remove)
                    cleaned_count += 1
                    
                    # Update stats
                    stats = self.get_memory_stats()
                    logger.info(f"Cleaned up model {model_to_remove.model_id}, "
                              f"memory now: {stats.used_memory_gb:.1f}GB")
            
            # Force garbage collection
            gc.collect()
            
            self.cleanup_count += 1
            
            # Run additional cleanup callbacks
            for callback in self._cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Cleanup callback error: {e}")
            
            final_stats = self.get_memory_stats()
            logger.info(f"Memory cleanup completed: {cleaned_count} models removed, "
                       f"memory: {final_stats.used_memory_gb:.1f}GB ({final_stats.memory_percent:.1f}%)")
            
            return cleaned_count
    
    def _cleanup_model(self, model_info: ModelInfo):
        """Clean up a specific model instance"""
        try:
            # Try to call cleanup method if available
            if hasattr(model_info.model_instance, 'cleanup'):
                model_info.model_instance.cleanup()
            elif hasattr(model_info.model_instance, 'close'):
                model_info.model_instance.close()
            
            # Clear reference
            model_info.model_instance = None
            
        except Exception as e:
            logger.error(f"Error cleaning up model {model_info.model_id}: {e}")
    
    def add_cleanup_callback(self, callback: Callable[[], None]):
        """Add a callback to be called during cleanup"""
        self._cleanup_callbacks.append(callback)
    
    def get_model_report(self) -> str:
        """Generate detailed model usage report"""
        stats = self.get_memory_stats()
        models = self.model_cache.get_all_models()
        
        report = [
            f"🧠 Memory Optimizer Report",
            f"   System Memory: {stats.used_memory_gb:.1f}GB / {stats.total_memory_gb:.1f}GB ({stats.memory_percent:.1f}%)",
            f"   Active Models: {stats.active_models} / {self.max_concurrent_models}",
            f"   Estimated Model Memory: {stats.estimated_model_memory_mb:.0f}MB",
            f"   Threshold: {self.memory_threshold_gb}GB",
            ""
        ]
        
        if stats.gpu_memory_gb:
            report.append(f"   GPU Memory: {stats.gpu_used_gb:.1f}GB / {stats.gpu_memory_gb:.1f}GB")
            report.append("")
        
        if models:
            report.append("   Loaded Models:")
            for model in sorted(models, key=lambda m: m.last_used, reverse=True):
                age = time.time() - model.last_used
                report.append(f"   • {model.model_id} ({model.agent_type})")
                report.append(f"     Priority: {model.priority.name}, Usage: {model.usage_count}, "
                            f"Age: {age:.0f}s, Memory: {model.estimated_memory_mb:.0f}MB")
        else:
            report.append("   No models currently loaded")
        
        report.extend([
            "",
            f"   Statistics:",
            f"   • Models loaded: {self.load_count}",
            f"   • Models evicted: {self.eviction_count}",
            f"   • Cleanup runs: {self.cleanup_count}"
        ])
        
        return "\n".join(report)
    
    def emergency_cleanup(self) -> int:
        """Emergency cleanup - remove all non-critical models"""
        with self._lock:
            logger.warning("🚨 Emergency memory cleanup initiated")
            
            models = self.model_cache.get_all_models()
            cleaned_count = 0
            
            # Remove all non-critical models
            for model in models:
                if model.priority != MemoryPriority.CRITICAL:
                    if self.model_cache.remove(model.model_id):
                        self._cleanup_model(model)
                        cleaned_count += 1
                        logger.warning(f"Emergency cleanup: removed {model.model_id}")
            
            # Force aggressive garbage collection
            for _ in range(3):
                gc.collect()
            
            stats = self.get_memory_stats()
            logger.warning(f"Emergency cleanup completed: {cleaned_count} models removed, "
                         f"memory: {stats.used_memory_gb:.1f}GB")
            
            return cleaned_count
    
    def shutdown(self):
        """Shutdown memory optimizer and cleanup all resources"""
        logger.info("Shutting down memory optimizer")
        
        self.stop_monitoring()
        
        # Clean up all models
        models = self.model_cache.clear()
        for model in models:
            self._cleanup_model(model)
        
        # Final garbage collection
        gc.collect()
        
        logger.info("Memory optimizer shutdown complete")


# Global memory optimizer instance
memory_optimizer = MemoryOptimizer()


def get_memory_optimizer() -> MemoryOptimizer:
    """Get the global memory optimizer instance"""
    return memory_optimizer


def start_memory_monitoring():
    """Start global memory monitoring"""
    memory_optimizer.start_monitoring()


def stop_memory_monitoring():
    """Stop global memory monitoring"""
    memory_optimizer.stop_monitoring()


def get_memory_report() -> str:
    """Get comprehensive memory report"""
    return memory_optimizer.get_model_report()


def cleanup_memory(force: bool = False) -> int:
    """Perform memory cleanup"""
    return memory_optimizer.cleanup_memory(force=force)