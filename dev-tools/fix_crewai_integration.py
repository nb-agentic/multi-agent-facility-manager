#!/usr/bin/env python3
"""
Fix CrewAI to use Ollama properly instead of trying to use OpenAI
"""
import os
import sys
sys.path.append('.')

# Set environment variables for CrewAI to use Ollama
os.environ['OPENAI_API_BASE'] = 'http://localhost:11434/v1'
os.environ['OPENAI_API_KEY'] = 'ollama'  # Dummy key for Ollama
os.environ['OPENAI_MODEL_NAME'] = 'mistral:7b'

# Test CrewAI with Ollama
def test_crewai_ollama():
    """Test CrewAI with Ollama backend"""
    from crewai import Agent, Task, Crew
    from langchain_ollama import OllamaLLM
    
    print("🧪 Testing CrewAI with Ollama...")
    
    # Create Ollama LLM with proper provider specification
    llm = OllamaLLM(
        model="ollama/mistral:7b",  # Specify ollama provider
        base_url="http://localhost:11434"
    )
    
    # Create a simple agent
    agent = Agent(
        role="Test Agent",
        goal="Test CrewAI with Ollama",
        backstory="A simple test agent to verify CrewAI works with Ollama",
        llm=llm,
        verbose=True
    )
    
    # Create a simple task
    task = Task(
        description="Say hello and confirm you are working with Ollama",
        expected_output="A greeting message confirming Ollama integration",
        agent=agent
    )
    
    # Create crew
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=True
    )
    
    try:
        print("🚀 Running CrewAI with Ollama...")
        result = crew.kickoff()
        print(f"✅ Success! Result: {result}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_crewai_ollama()
    if success:
        print("🎉 CrewAI + Ollama integration working!")
    else:
        print("💥 CrewAI + Ollama integration failed!")