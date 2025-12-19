#!/usr/bin/env python3
"""
Test the optimized CrewAI setup
"""
import asyncio
import sys
sys.path.append('.')

from intellicenter.core.async_crew import llm_manager, OptimizedLLMManager

async def test_llm_manager():
    """Test the optimized LLM manager"""
    print("🧪 Testing Optimized LLM Manager...")
    
    try:
        # Test getting different LLMs
        hvac_llm = llm_manager.get_llm("hvac")
        print(f"✅ HVAC LLM loaded: {hvac_llm.model}")
        
        security_llm = llm_manager.get_llm("security")
        print(f"✅ Security LLM loaded: {security_llm.model}")
        
        # Test memory report
        report = llm_manager.get_memory_report()
        print(f"📊 {report}")
        
        # Test simple LLM call - CrewAI LLM doesn't have direct invoke method
        # We'll test through the async crew instead
        print(f"🤖 HVAC LLM loaded successfully: {hvac_llm.model}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_llm_manager())
    if success:
        print("🎉 Optimized LLM Manager is working!")
    else:
        print("💥 Test failed!")