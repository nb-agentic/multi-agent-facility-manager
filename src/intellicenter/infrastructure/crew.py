"""
Async CrewAI Wrapper for Non-Blocking Agent Operations
Handles memory optimization and concurrent execution.
"""
import asyncio
import json
import time
import psutil
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional
from crewai import Agent, Task, Crew
from crewai import LLM
from intellicenter.infrastructure.llm.factory import get_llm, get_memory_report
from intellicenter.infrastructure.memory import get_memory_optimizer, MemoryPriority


class AsyncCrewAI:
    """Async wrapper for CrewAI operations with memory management"""
    
    def __init__(self, crew: Crew, agent_name: str = "unknown"):
        self.crew = crew
        self.agent_name = agent_name
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix=f"crew-{agent_name}")
        self.last_execution = 0
        self.execution_count = 0
        self.memory_optimizer = get_memory_optimizer()
        
    async def async_kickoff(self, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run CrewAI kickoff in a separate thread with timeout and error handling"""
        start_time = time.time()
        self.execution_count += 1
        
        try:
            # Check memory constraints before execution using MemoryOptimizer
            memory_stats = self.memory_optimizer.get_memory_stats()
            
            if memory_stats.used_memory_gb >= self.memory_optimizer.memory_threshold_gb:
                print(f"⚠️  Memory threshold exceeded ({memory_stats.used_memory_gb:.1f}GB >= {self.memory_optimizer.memory_threshold_gb}GB) before {self.agent_name} execution")
                cleanup_count = self.memory_optimizer.cleanup_memory(force=True)
                print(f"🧹 Cleaned up {cleanup_count} models before {self.agent_name} execution")
                
                # Re-check after cleanup
                memory_stats = self.memory_optimizer.get_memory_stats()
                if memory_stats.used_memory_gb >= self.memory_optimizer.max_memory_gb:
                    raise MemoryError(f"Insufficient memory for {self.agent_name} execution: {memory_stats.used_memory_gb:.1f}GB >= {self.memory_optimizer.max_memory_gb}GB")
            
            # Run CrewAI in thread with timeout
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(self.executor, self._safe_kickoff, inputs),
                timeout=60.0  # 60 second timeout
            )
            
            execution_time = time.time() - start_time
            self.last_execution = time.time()
            
            # Monitor memory after execution
            memory_after = self.memory_optimizer.get_memory_stats()
            
            print(f"✅ {self.agent_name} completed in {execution_time:.2f}s (Memory: {memory_after.used_memory_gb:.1f}GB/{memory_after.total_memory_gb:.1f}GB)")
            
            # Trigger cleanup if memory usage is high after execution
            if memory_after.used_memory_gb >= self.memory_optimizer.memory_threshold_gb:
                cleanup_count = self.memory_optimizer.cleanup_memory()
                if cleanup_count > 0:
                    print(f"🧹 Post-execution cleanup: {cleanup_count} models removed")
            
            return {
                "result": result,
                "execution_time": execution_time,
                "memory_usage_gb": memory_after.used_memory_gb,
                "memory_percent": memory_after.memory_percent,
                "active_models": memory_after.active_models,
                "status": "success"
            }
            
        except asyncio.TimeoutError:
            print(f"⏰ {self.agent_name} execution timed out after 60 seconds")
            return {
                "result": None,
                "error": "Execution timeout",
                "status": "timeout"
            }
        except MemoryError as e:
            print(f"💾 {self.agent_name} execution failed due to memory constraints: {e}")
            return {
                "result": None,
                "error": str(e),
                "status": "memory_error"
            }
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ {self.agent_name} execution failed after {execution_time:.2f}s: {e}")
            return {
                "result": None,
                "error": str(e),
                "execution_time": execution_time,
                "status": "error"
            }
    
    def _safe_kickoff(self, inputs: Optional[Dict[str, Any]] = None):
        """Safe CrewAI kickoff with error handling"""
        try:
            if inputs:
                return self.crew.kickoff(inputs=inputs)
            else:
                return self.crew.kickoff()
        except Exception as e:
            print(f"❌ CrewAI kickoff error in {self.agent_name}: {e}")
            raise e
    
    async def _cleanup_memory(self):
        """Perform memory cleanup using MemoryOptimizer"""
        cleanup_count = self.memory_optimizer.cleanup_memory(force=True)
        await asyncio.sleep(0.1)  # Allow cleanup to complete
        return cleanup_count
        
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics including memory optimizer stats"""
        memory_stats = self.memory_optimizer.get_memory_stats()
        return {
            "agent_name": self.agent_name,
            "execution_count": self.execution_count,
            "last_execution": self.last_execution,
            "memory_usage_gb": memory_stats.used_memory_gb,
            "memory_percent": memory_stats.memory_percent,
            "active_models": memory_stats.active_models,
            "estimated_model_memory_mb": memory_stats.estimated_model_memory_mb,
            "memory_threshold_gb": self.memory_optimizer.memory_threshold_gb,
            "max_memory_gb": self.memory_optimizer.max_memory_gb
        }
    
    def __del__(self):
        """Cleanup executor on deletion"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)


# Use centralized LLM configuration from llm_config module


def create_optimized_crew(agent_config: Dict[str, Any], task_config: Dict[str, Any],
                         agent_type: str, tools: list = None) -> Crew:
    """Create an optimized CrewAI crew with proper LLM configuration and memory checks"""
    
    # Check memory constraints before creating crew
    memory_optimizer = get_memory_optimizer()
    memory_stats = memory_optimizer.get_memory_stats()
    
    if memory_stats.used_memory_gb >= memory_optimizer.memory_threshold_gb:
        print(f"⚠️  Memory threshold exceeded during crew creation: {memory_stats.used_memory_gb:.1f}GB >= {memory_optimizer.memory_threshold_gb}GB")
        cleanup_count = memory_optimizer.cleanup_memory(force=True)
        print(f"🧹 Cleaned up {cleanup_count} models before creating {agent_type} crew")
        
        # Re-check after cleanup
        memory_stats = memory_optimizer.get_memory_stats()
        if memory_stats.used_memory_gb >= memory_optimizer.max_memory_gb:
            raise MemoryError(f"Insufficient memory to create {agent_type} crew: {memory_stats.used_memory_gb:.1f}GB >= {memory_optimizer.max_memory_gb}GB")
    
    # Get optimized LLM from centralized configuration
    llm = get_llm(agent_type)
    
    # Create agent with optimized settings
    agent = Agent(
        role=agent_config["role"],
        goal=agent_config["goal"],
        backstory=agent_config["backstory"],
        llm=llm,
        verbose=False,  # Reduce logging overhead
        allow_delegation=False,
        tools=tools or [],
        max_execution_time=agent_config.get("max_execution_time", 30)
    )
    
    # Create task
    task = Task(
        description=task_config["description"],
        expected_output=task_config["expected_output"],
        agent=agent
    )
    
    # Create crew with memory optimization
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=False,  # Reduce memory overhead
        memory=False,   # Disable memory for better performance
        planning=False, # Disable planning to reduce complexity
        max_execution_time=agent_config.get("max_execution_time", 30)
    )
    
    print(f"✅ Created {agent_type} crew (Memory: {memory_stats.used_memory_gb:.1f}GB/{memory_stats.total_memory_gb:.1f}GB)")
    return crew


async def test_async_crew():
    """Test the async CrewAI wrapper"""
    print("🧪 Testing Async CrewAI Wrapper...")
    
    # Create a simple test crew
    from crewai import Agent, Task, Crew
    
    llm = get_llm("network")
    
    test_agent = Agent(
        role="Test Agent",
        goal="Test the async wrapper",
        backstory="A simple test agent",
        llm=llm,
        verbose=False
    )
    
    test_task = Task(
        description="Say hello and confirm the system is working",
        expected_output="A simple greeting message",
        agent=test_agent
    )
    
    test_crew = Crew(
        agents=[test_agent],
        tasks=[test_task],
        verbose=False
    )
    
    # Test async execution
    async_crew = AsyncCrewAI(test_crew, "test")
    result = await async_crew.async_kickoff()
    
    print(f"Test Result: {result}")
    print(f"LLM Manager Report: {get_memory_report()}")
    print(f"Memory Optimizer Report:\n{get_memory_optimizer().get_model_report()}")
    
    return result["status"] == "success"


if __name__ == "__main__":
    asyncio.run(test_async_crew())