#!/usr/bin/env python3
"""
Test CrewAI Integration with Ollama
Verifies that CrewAI can properly use Ollama models
"""
import asyncio
import json
import sys
sys.path.append('.')

from crewai import Agent, Task, Crew, LLM

async def test_direct_crewai():
    """Test CrewAI directly with Ollama"""
    print("🧪 Testing Direct CrewAI Integration with Ollama")
    print("="*60)
    
    try:
        # Create LLM instance using CrewAI's LLM class
        print("🧠 Creating LLM instance...")
        llm = LLM(
            model="ollama/mistral:7b",
            base_url="http://localhost:11434"
        )
        print(f"✅ LLM created: {llm.model}")
        
        # Create a simple agent
        print("🤖 Creating agent...")
        agent = Agent(
            role="Test Specialist",
            goal="Test the CrewAI integration",
            backstory="A simple test agent to verify CrewAI works with Ollama",
            llm=llm,
            verbose=False
        )
        print("✅ Agent created")
        
        # Create a simple task
        print("📋 Creating task...")
        task = Task(
            description="Say hello and confirm you are working. Keep response under 20 words.",
            expected_output="A brief greeting confirming the system is operational",
            agent=agent
        )
        print("✅ Task created")
        
        # Create crew
        print("👥 Creating crew...")
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False
        )
        print("✅ Crew created")
        
        # Test execution with timeout
        print("🚀 Testing crew execution...")
        
        # Use asyncio.to_thread for async execution
        result = await asyncio.wait_for(
            asyncio.to_thread(crew.kickoff),
            timeout=30.0
        )
        
        print(f"✅ CrewAI execution successful!")
        print(f"📤 Result: {result}")
        
        return True
        
    except asyncio.TimeoutError:
        print("⏰ CrewAI execution timed out after 30 seconds")
        return False
    except Exception as e:
        print(f"❌ CrewAI test failed: {e}")
        return False

async def test_ollama_direct():
    """Test Ollama directly to ensure it's working"""
    print("\n🔍 Testing Ollama Direct Connection")
    print("-"*40)
    
    try:
        import requests
        
        # Test Ollama API directly
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral:7b",
                "prompt": "Hello, are you working? Respond with just 'Yes, I am working.'",
                "stream": False
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            ollama_response = data.get("response", "No response")
            print(f"✅ Ollama direct test successful: {ollama_response}")
            return True
        else:
            print(f"❌ Ollama API returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ollama direct test failed: {e}")
        return False

async def main():
    """Run comprehensive CrewAI integration test"""
    print("🚀 CrewAI Integration Verification")
    print("="*60)
    
    # Test 1: Ollama direct connection
    ollama_works = await test_ollama_direct()
    
    if not ollama_works:
        print("\n❌ Ollama is not working properly. Fix Ollama first.")
        return False
    
    # Test 2: CrewAI integration
    crewai_works = await test_direct_crewai()
    
    print("\n" + "="*60)
    print("📊 INTEGRATION TEST RESULTS")
    print("="*60)
    print(f"🔗 Ollama Direct: {'✅ Working' if ollama_works else '❌ Failed'}")
    print(f"🤖 CrewAI Integration: {'✅ Working' if crewai_works else '❌ Failed'}")
    
    if ollama_works and crewai_works:
        print("\n🎉 CrewAI integration is working correctly!")
        print("💡 Your agents should now be able to respond to events.")
        return True
    else:
        print("\n❌ Integration issues detected.")
        if ollama_works and not crewai_works:
            print("💡 Ollama works but CrewAI integration has issues.")
            print("   This suggests a CrewAI configuration problem.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)