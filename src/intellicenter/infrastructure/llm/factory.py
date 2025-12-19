import gc
import time
import psutil
from typing import Optional, Dict, Any

from langchain_community.llms import Ollama
from intellicenter.infrastructure.memory import get_memory_optimizer, MemoryPriority
from intellicenter.shared.logger import log_token_usage, get_logger

logger = get_logger("intellicenter.infrastructure.llm")

class OptimizedOllama(Ollama):
    """Memory-optimized Ollama wrapper for RTX 4060 constraints"""
    agent_type: str = "standard"
    last_used: float = 0.0
    usage_count: int = 0
    model_name: str = ""

    def __init__(self, model: str = "ollama/mistral-nemo:latest", agent_type: str = "standard", **kwargs):
        # Ensure model name is properly formatted for Ollama
        if not model.startswith("ollama/"):
            model = f"ollama/{model}"
        
        # Set base_url if not provided
        if "base_url" not in kwargs:
            kwargs["base_url"] = "http://localhost:11434"
            
        super().__init__(model=model, **kwargs)
        self.agent_type = agent_type
        self.last_used = time.time()
        self.usage_count = 0
        self.model_name = model
    
    def _call(self, prompt: str, stop: Optional[list] = None, **kwargs) -> str:
        """Enhanced call with memory tracking and optimization"""
        self.last_used = time.time()
        self.usage_count += 1
        
        cleanup_interval = 5 if self.agent_type != "critical" else 10
        if self.usage_count % cleanup_interval == 0:
            self._cleanup_memory()
        
        try:
            response = ""
            for chunk in self._stream(prompt, stop=stop, **kwargs):
                response += chunk.text
            
            result = response.strip()
            
            # Log token usage (estimated)
            input_tokens = len(prompt) // 4
            output_tokens = len(result) // 4
            log_token_usage(
                model=self.model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                agent_type=self.agent_type
            )
            
            return result
            
        except Exception as e:
            logger.error("llm_call_error", model=self.model_name, error=str(e))
            return self._fallback_response(prompt)
    
    def _cleanup_memory(self):
        """Perform memory cleanup"""
        gc.collect()
        memory_percent = psutil.virtual_memory().percent
        
        if memory_percent > 80:
            print(f"🧹 Memory cleanup - Usage: {memory_percent:.1f}%")
    
    def _fallback_response(self, prompt: str) -> str:
        """Provide fallback response on LLM failure"""
        if "temperature" in prompt.lower():
            return "medium"
        elif "power" in prompt.lower():
            return "maintain current power distribution"
        else:
            return "analysis_required"
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get LLM usage statistics"""
        return {
            "model": self.model_name,
            "agent_type": self.agent_type, 
            "usage_count": self.usage_count,
            "last_used": self.last_used,
            "memory_percent": psutil.virtual_memory().percent
        }

class LLMManager:
    """Centralized LLM management for memory optimization"""
    
    def __init__(self):
        self.active_models: Dict[str, OptimizedOllama] = {}
        self.max_memory_percent = 75
        self.memory_optimizer = get_memory_optimizer()
        self.max_concurrent_models = 2  # RTX 4060 constraint
        
    def get_llm(self, agent_type: str = "standard") -> OptimizedOllama:
        """Get optimized LLM instance based on agent type and memory constraints"""
        
        # Check memory constraints using MemoryOptimizer
        memory_stats = self.memory_optimizer.get_memory_stats()
        
        if memory_stats.used_memory_gb >= self.memory_optimizer.memory_threshold_gb:
            print(f"⚠️  Memory threshold exceeded during LLM loading: {memory_stats.used_memory_gb:.1f}GB >= {self.memory_optimizer.memory_threshold_gb}GB")
            cleanup_count = self.memory_optimizer.cleanup_memory(force=True)
            print(f"🧹 MemoryOptimizer cleaned up {cleanup_count} models")
            
            # Also perform LLM-specific cleanup
            self._emergency_cleanup()
            
            # Re-check after cleanup
            memory_stats = self.memory_optimizer.get_memory_stats()
            if memory_stats.used_memory_gb >= self.memory_optimizer.max_memory_gb:
                raise MemoryError(f"Insufficient memory to load {agent_type} LLM: {memory_stats.used_memory_gb:.1f}GB >= {self.memory_optimizer.max_memory_gb}GB")
        
        model_config = self._get_model_config(agent_type)
        model_key = f"{agent_type}_{model_config['model']}"
        
        # Check if we're at the concurrent model limit
        if model_key not in self.active_models and len(self.active_models) >= self.max_concurrent_models:
            print(f"⚠️  Maximum concurrent LLM models reached ({self.max_concurrent_models}), performing cleanup")
            self._emergency_cleanup()
        
        if model_key not in self.active_models:
            # Estimate memory usage for the model (rough estimate based on model size)
            estimated_memory_mb = self._estimate_model_memory(model_config['model'])
            
            # Check if we can load the model using MemoryOptimizer
            can_load, reason = self.memory_optimizer.can_load_model(estimated_memory_mb)
            if not can_load:
                # Try cleanup and check again
                cleanup_count = self.memory_optimizer.cleanup_memory(force=True)
                print(f"🧹 Cleaned up {cleanup_count} models to make room for {agent_type} LLM")
                can_load, reason = self.memory_optimizer.can_load_model(estimated_memory_mb)
                
                if not can_load:
                    raise MemoryError(f"Cannot load {agent_type} LLM: {reason}")
            
            print(f"🧠 Loading {model_config['model']} for {agent_type} agent (estimated: {estimated_memory_mb:.0f}MB)")
            self.active_models[model_key] = OptimizedOllama(
                model=model_config['model'],
                agent_type=agent_type,
                temperature=model_config['temperature'],
                num_predict=model_config['max_tokens']
            )
        
        return self.active_models[model_key]
    
    def _get_model_config(self, agent_type: str) -> Dict[str, Any]:
        """Get model configuration based on agent type"""
        configs = {
            "critical": {
                "model": "ollama/qwen2.5vl:7b",
                "temperature": 0.1,
                "max_tokens": 100
            },
            "standard": {
                "model": "ollama/qwen2.5vl:7b",
                "temperature": 0.2,
                "max_tokens": 150
            },
            "coordinator": {
                "model": "ollama/mistral-nemo:latest",
                "temperature": 0.05,
                "max_tokens": 300
            },
            "hvac": {
                "model": "ollama/mistral:7b",
                "temperature": 0.1,
                "max_tokens": 200
            },
            "security": {
                "model": "ollama/gemma2:2b",
                "temperature": 0.05,
                "max_tokens": 150
            },
            "power": {
                "model": "ollama/gemma2:2b",
                "temperature": 0.1,
                "max_tokens": 150
            },
            "network": {
                "model": "ollama/qwen2.5vl:7b",
                "temperature": 0.15,
                "max_tokens": 200
            }
        }
        
        return configs.get(agent_type, configs["standard"])
    
    def _estimate_model_memory(self, model_name: str) -> float:
        """Estimate memory usage for a model in MB"""
        # Rough estimates based on model sizes
        model_memory_estimates = {
            "ollama/qwen2.5vl:7b": 4500,      # ~4.5GB for 7B model
            "ollama/mistral-nemo:latest": 8000, # ~8GB for larger model
            "ollama/mistral:7b": 4500,        # ~4.5GB for 7B model
            "ollama/gemma2:2b": 1500,         # ~1.5GB for 2B model
        }
        
        # Extract base model name
        for key, memory in model_memory_estimates.items():
            if key in model_name:
                return memory
        
        # Default estimate for unknown models
        return 2000  # 2GB default
    
    def _emergency_cleanup(self):
        """Emergency memory cleanup when usage is too high"""
        print("⚠️  High LLM memory usage detected - performing emergency cleanup")
        
        if len(self.active_models) > 1:
            # Sort by last used time, remove oldest first
            sorted_models = sorted(self.active_models.items(),
                                 key=lambda x: x[1].last_used)
            
            # Remove half of the models, keeping at least 1
            models_to_remove = max(1, len(self.active_models) // 2)
            
            for i in range(models_to_remove):
                if len(self.active_models) <= 1:
                    break
                oldest_key, _ = sorted_models[i]
                print(f"🧹 Removing LLM: {oldest_key}")
                del self.active_models[oldest_key]
        
        gc.collect()
    
    def get_memory_report(self) -> str:
        """Generate comprehensive memory usage report"""
        memory_stats = self.memory_optimizer.get_memory_stats()
        report = f"💾 LLM Memory: {memory_stats.memory_percent:.1f}% used ({memory_stats.used_memory_gb:.1f}GB/{memory_stats.total_memory_gb:.1f}GB), {len(self.active_models)} active LLM models."
        
        if self.active_models:
            report += f" Models: {', '.join(self.active_models.keys())}"
        
        return report

llm_manager = LLMManager()

def get_llm(agent_type: str = "standard") -> OptimizedOllama:
    """Global function to get optimized LLM instance"""
    return llm_manager.get_llm(agent_type)

def get_memory_report() -> str:
    """Get system memory report"""
    return llm_manager.get_memory_report()