#!/usr/bin/env python3
"""
Test Ollama connection and LLM configuration
"""
import sys
import os
sys.path.append('.')

from intellicenter.llm.llm_config import get_llm

def test_ollama_connection():
    print("🧪 Testing Ollama LLM connection...")
    
    try:
        # Test critical agent LLM
        llm = get_llm("critical")
        print(f"✅ LLM created: {llm.model_name}")
        
        # Test a simple prompt
        test_prompt = "What is the optimal temperature for a server room? Answer in one sentence."
        print(f"📤 Sending test prompt: {test_prompt}")
        
        response = llm._call(test_prompt)
        print(f"📥 Response: {response}")
        
        # Test usage stats
        stats = llm.get_usage_stats()
        print(f"📊 Usage stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_ollama_connection()
    if success:
        print("🎉 Ollama LLM is working correctly!")
    else:
        print("💥 Ollama LLM test failed!")