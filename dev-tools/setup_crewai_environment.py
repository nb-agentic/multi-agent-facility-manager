#!/usr/bin/env python3
"""
Complete CrewAI Environment Setup Script
Implements all optimizations from the research recommendations.
"""
import subprocess
import requests
import time
import os
import psutil
from pathlib import Path


def check_ollama_installation():
    """Check if Ollama is installed"""
    try:
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama is installed:", result.stdout.strip())
            return True
        else:
            print("❌ Ollama version check failed")
            return False
    except FileNotFoundError:
        print("❌ Ollama not found. Please install Ollama first:")
        print("   curl -fsSL https://ollama.ai/install.sh | sh")
        return False


def check_ollama_service():
    """Check if Ollama service is running"""
    try:
        response = requests.get('http://localhost:11434/api/version', timeout=10)
        if response.status_code == 200:
            version_info = response.json()
            print(f"✅ Ollama service is running (version: {version_info.get('version', 'unknown')})")
            return True
        else:
            print(f"❌ Ollama service responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to Ollama service: {e}")
        return False


def start_ollama_service():
    """Start Ollama service if not running"""
    if check_ollama_service():
        return True
        
    print("🚀 Starting Ollama service...")
    try:
        # Start Ollama in background
        subprocess.Popen(['ollama', 'serve'], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        
        # Wait for service to start
        for i in range(10):
            time.sleep(2)
            if check_ollama_service():
                return True
            print(f"   Waiting for service... ({i+1}/10)")
            
        print("❌ Failed to start Ollama service")
        return False
        
    except Exception as e:
        print(f"❌ Error starting Ollama service: {e}")
        return False


def install_required_models():
    """Install all required models for the agents"""
    required_models = [
        "mistral:7b",      # HVAC and Coordinator
        "gemma2:2b",       # Security and Power
        "qwen2.5vl:7b",    # Network (already available)
    ]
    
    print("📦 Installing required models...")
    
    for model in required_models:
        print(f"   Installing {model}...")
        try:
            result = subprocess.run(['ollama', 'pull', model], 
                                  capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print(f"   ✅ {model} installed successfully")
            else:
                print(f"   ❌ Failed to install {model}: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Timeout installing {model}")
            return False
        except Exception as e:
            print(f"   ❌ Error installing {model}: {e}")
            return False
    
    return True


def verify_models():
    """Verify all required models are available"""
    print("🔍 Verifying installed models...")
    
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            available_models = result.stdout
            required_models = ["mistral:7b", "gemma2:2b", "qwen2.5vl:7b"]
            
            for model in required_models:
                if model in available_models:
                    print(f"   ✅ {model} is available")
                else:
                    print(f"   ❌ {model} is missing")
                    return False
            return True
        else:
            print("❌ Failed to list models")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying models: {e}")
        return False


def set_memory_optimizations():
    """Set environment variables for memory optimization"""
    print("🧠 Setting memory optimizations...")
    
    optimizations = {
        'OLLAMA_NUM_PARALLEL': '1',           # Reduce parallel requests
        'OLLAMA_MAX_LOADED_MODELS': '2',      # Limit loaded models
        'OLLAMA_FLASH_ATTENTION': 'true',     # Enable flash attention
        'OTEL_SDK_DISABLED': 'true',          # Disable telemetry
    }
    
    for key, value in optimizations.items():
        os.environ[key] = value
        print(f"   {key}={value}")
    
    # Check current memory usage
    memory = psutil.virtual_memory()
    print(f"   Current memory usage: {memory.percent:.1f}% ({memory.used / 1024**3:.1f}GB / {memory.total / 1024**3:.1f}GB)")
    
    if memory.percent > 80:
        print("   ⚠️  High memory usage detected. Consider closing other applications.")
    
    return True


def create_config_directories():
    """Create necessary configuration directories"""
    print("📁 Creating configuration directories...")
    
    directories = [
        Path('intellicenter/config'),
        Path('logs'),
        Path('data')
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {directory}")
    
    return True


def test_llm_connectivity():
    """Test LLM connectivity with each model"""
    print("🧪 Testing LLM connectivity...")
    
    models_to_test = {
        "mistral:7b": "What is HVAC?",
        "gemma2:2b": "What is security?", 
        "qwen2.5vl:7b": "What is networking?"
    }
    
    for model, prompt in models_to_test.items():
        try:
            print(f"   Testing {model}...")
            
            # Use ollama run command for testing
            result = subprocess.run(['ollama', 'run', model, prompt], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and result.stdout.strip():
                print(f"   ✅ {model} responded successfully")
            else:
                print(f"   ❌ {model} failed to respond properly")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"   ⏰ {model} response timed out")
            return False
        except Exception as e:
            print(f"   ❌ Error testing {model}: {e}")
            return False
    
    return True


def create_environment_file():
    """Create .env file with optimized settings"""
    print("📝 Creating environment configuration...")
    
    env_content = """# IntelliCenter Environment Configuration
# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_NUM_PARALLEL=1
OLLAMA_MAX_LOADED_MODELS=2
OLLAMA_FLASH_ATTENTION=true

# CrewAI Configuration  
CREWAI_LLM_PROVIDER=ollama
CREWAI_MODEL=mistral:7b

# Disable Telemetry
OTEL_SDK_DISABLED=true
OPENAI_API_KEY=sk-fake-key-for-local-llm

# Performance Settings
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
"""
    
    env_path = Path('.env')
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"   ✅ Created {env_path}")
    return True


def main():
    """Main setup function"""
    print("🚀 IntelliCenter CrewAI Environment Setup")
    print("=" * 50)
    
    steps = [
        ("Checking Ollama installation", check_ollama_installation),
        ("Starting Ollama service", start_ollama_service),
        ("Installing required models", install_required_models),
        ("Verifying models", verify_models),
        ("Setting memory optimizations", set_memory_optimizations),
        ("Creating config directories", create_config_directories),
        ("Testing LLM connectivity", test_llm_connectivity),
        ("Creating environment file", create_environment_file),
    ]
    
    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}...")
        if not step_func():
            print(f"\n❌ Setup failed at: {step_name}")
            return False
    
    print("\n" + "=" * 50)
    print("🎉 IntelliCenter CrewAI Environment Setup Complete!")
    print("\nNext steps:")
    print("1. Run: source venv/bin/activate.fish")
    print("2. Test: python test_optimized_crew.py")
    print("3. Start: python manual_agent_test.py")
    print("\n📊 System Status:")
    
    # Final system status
    memory = psutil.virtual_memory()
    print(f"   Memory: {memory.percent:.1f}% used")
    print(f"   Available models: mistral:7b, gemma2:2b, qwen2.5vl:7b")
    print(f"   Ollama service: Running on localhost:11434")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)