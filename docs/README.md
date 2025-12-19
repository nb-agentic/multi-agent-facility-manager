# IntelliCenter Documentation

## Project Overview

IntelliCenter is an advanced multi-agent facility management system that leverages artificial intelligence to coordinate and optimize data center operations. The system uses specialized AI agents to manage HVAC, security, power, and network infrastructure, with a central coordinator agent ensuring holistic facility management.

**Key Features:**
- 🤖 **Multi-Agent AI Architecture**: Specialized agents for each facility domain
- ⚡ **Real-Time Coordination**: Event-driven communication and decision making
- 🎯 **Scenario Orchestration**: Automated responses to facility emergencies
- 📊 **Performance Monitoring**: Comprehensive metrics and analytics
- 🔧 **Manual Override**: Human intervention capabilities
- 🌐 **WebSocket Integration**: Real-time dashboard and monitoring

**Architecture Highlights:**
- Distributed agent-based system with centralized coordination
- Event-driven communication using async event bus
- CrewAI integration for advanced AI decision making
- Memory-optimized for RTX 4060 constraints
- Comprehensive testing and validation framework

---

## Installation and Setup

### Prerequisites

#### System Requirements
- **Operating System:** Linux, macOS, or Windows
- **Python:** 3.10 or higher
- **GPU:** NVIDIA RTX 4060 (8GB VRAM) or equivalent
- **RAM:** 16GB minimum, 32GB recommended
- **Storage:** 20GB free space
- **Network:** Stable internet connection

#### Software Dependencies
- **Python 3.10+** with pip
- **Node.js 18+** for frontend
- **Ollama** for LLM inference
- **Git** for repository management

### Step-by-Step Installation

#### 1. Clone the Repository
```bash
git clone <repository-url>
cd intellicenter
```

#### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

#### 3. Install and Configure Ollama
```bash
# Install Ollama (follow instructions for your OS)
# https://ollama.ai/download

# Start Ollama service
ollama serve

# Pull required models
ollama pull llama3.1:8b
```

#### 4. Set Up Frontend
```bash
cd frontend
npm install
cd ..
```

#### 5. Configure Environment Variables
```bash
# Create .env file (optional)
cat > .env << EOF
# LLM Configuration
OLLAMA_HOST=http://localhost:11434
MAX_CONCURRENT_MODELS=2
MEMORY_THRESHOLD_GB=7

# WebSocket Configuration
WEBSOCKET_HOST=localhost
WEBSOCKET_PORT=8000

# Logging Configuration
LOG_LEVEL=INFO
EOF
```

#### 6. Verify Installation
```bash
# Test Python imports
python -c "import intellicenter; print('✅ IntelliCenter imports successfully')"

# Test Ollama connection
curl http://localhost:11434/api/tags

# Test frontend build
cd frontend && npm run build && cd ..
```

---

## Usage Examples

### Basic Usage

#### Starting the System
```bash
# Start the WebSocket server
python -m intellicenter.api.websocket_server

# In a separate terminal, start the agents
python -m intellicenter.agents.hvac_agent
python -m intellicenter.agents.power_agent
python -m intellicenter.agents.security_agent
python -m intellicenter.agents.network_agent
python -m intellicenter.agents.coordinator_agent

# Start the frontend
cd frontend && npm run dev
```

#### Running Scenarios
```bash
# Run cooling crisis scenario
python -m intellicenter.scenarios.cooling_crisis

# Run security breach scenario
python -m intellicenter.scenarios.security_breach

# Run energy optimization scenario
python -m intellicenter.scenarios.energy_optimization
```

### Advanced Usage

#### Custom Scenario Configuration
```python
from intellicenter.scenarios.scenario_orchestrator import ScenarioOrchestrator
from intellicenter.core.event_bus import EventBus

# Initialize event bus and orchestrator
event_bus = EventBus()
orchestrator = ScenarioOrchestrator(event_bus)

# Run custom scenario
await orchestrator.execute_scenario("cooling_crisis")
```

#### Manual Agent Control
```python
from intellicenter.agents.hvac_agent import HVACControlAgent
from intellicenter.core.event_bus import EventBus

# Initialize agent
event_bus = EventBus()
hvac_agent = HVACControlAgent(event_bus)

# Send temperature data
import json
temperature_data = {"temperature": 85.5, "timestamp": "2024-01-01T12:00:00"}
hvac_agent._handle_temperature_change(json.dumps(temperature_data), asyncio.get_event_loop())
```

#### Performance Monitoring
```python
# Get agent performance reports
hvac_report = hvac_agent.get_performance_report()
coordinator_report = coordinator_agent.get_performance_report()

# Get system metrics
metrics = orchestrator.get_performance_metrics()
print(f"Coordination events: {metrics['coordination_events']}")
print(f"Average response time: {metrics['avg_coordination_time']:.2f}s")
```

---

## API Documentation

### WebSocket API

#### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

#### Message Types

##### Agent Status Updates
```javascript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === 'agent_status_update') {
    console.log('Agent status:', message.data);
  }
  
  if (message.type === 'event_log') {
    console.log('Event:', message.data);
  }
  
  if (message.type === 'coordination_directive') {
    console.log('Coordinator directive:', message.data);
  }
};
```

##### Manual Override
```javascript
const overrideMessage = {
  type: 'manual_override',
  data: {
    agent: 'hvac',
    command: 'set_temperature',
    parameters: { target_temp: 72 }
  }
};
ws.send(JSON.stringify(overrideMessage));
```

#### Event Types

| Event Type | Description | Data Format |
|------------|-------------|-------------|
| `agent_status_update` | Agent status changes | `{agent, status, timestamp, details}` |
| `event_log` | System events | `{timestamp, agent, event, details}` |
| `coordination_directive` | Coordinator decisions | `{timestamp, directive, priority_event, coordinated_plan}` |
| `manual_override_response` | Override confirmation | `{agent, command, status, timestamp}` |

### Python API

#### Event Bus
```python
from intellicenter.core.event_bus import EventBus

# Create event bus
event_bus = EventBus()
await event_bus.start()

# Subscribe to events
event_bus.subscribe("hvac.cooling.decision", callback_function)

# Publish events
await event_bus.publish("hvac.temperature.changed", json.dumps(data))
```

#### Agent Interface
```python
from intellicenter.agents.hvac_agent import HVACControlAgent

# Initialize agent
agent = HVACControlAgent(event_bus)

# Test agent functionality
result = await agent.test_response_generation(temperature_data)
print(f"Test result: {result}")
```

#### Scenario Orchestration
```python
from intellicenter.scenarios.scenario_orchestrator import ScenarioOrchestrator

# Initialize orchestrator
orchestrator = ScenarioOrchestrator(event_bus)

# Execute scenario
result = await orchestrator.execute_scenario("cooling_crisis")
print(f"Scenario result: {result}")
```

---

## Configuration Options

### Agent Configuration

#### agents.yaml
```yaml
# Agent definitions
hvac_specialist:
  role: "HVAC Systems Specialist"
  goal: "Maintain optimal temperature and humidity levels throughout the data center while maximizing energy efficiency"
  backstory: |
    Expert thermal management specialist with deep knowledge of data center cooling requirements, 
    predictive maintenance, and energy optimization strategies.
  max_execution_time: 30

power_specialist:
  role: "Power Systems Engineer"
  goal: "Monitor and optimize power distribution, UPS systems, and energy consumption across all facility zones"
  backstory: |
    Electrical engineer specializing in data center power infrastructure, load balancing, 
    and backup power systems management.
  max_execution_time: 30

security_specialist:
  role: "Security Operations Specialist"
  goal: "Monitor facility access, surveillance systems, and threat detection to ensure physical security"
  backstory: |
    Certified security professional specializing in data center physical security, 
    access control systems, and incident response protocols.
  max_execution_time: 30

network_specialist:
  role: "Network Infrastructure Engineer"
  goal: "Ensure optimal network performance, connectivity, and security across the data center"
  backstory: |
    Network engineering expert specializing in data center networking, responsible for monitoring traffic,
    managing hardware, and responding to connectivity or security incidents.
  max_execution_time: 30

facility_coordinator:
  role: "Facility Coordinator"
  goal: "Orchestrate and coordinate actions between all specialized agents to ensure a holistic and efficient facility response to events"
  backstory: |
    The central command unit of the IntelliCenter. You receive high-level reports from all specialized agents
    and make strategic decisions that may require coordinating actions across multiple domains.
  max_execution_time: 30
```

#### tasks.yaml
```yaml
# Task definitions
hvac_analysis:
  description: |
    Analyze the temperature data: {temperature_data}. Your primary goal is to determine the appropriate cooling level 
    based on current temperature, humidity, and energy efficiency considerations. Consider the following factors:
    1. Current temperature and humidity levels
    2. Energy consumption implications
    3. System capacity and constraints
    4. Predictive maintenance needs
    Provide a cooling level recommendation (low, medium, high, emergency) with detailed reasoning.
  expected_output: |
    JSON with cooling_level, reasoning, confidence, and recommendations.

power_optimization:
  description: |
    Analyze the power consumption data: {power_data}. Your primary goal is to optimize power distribution while 
    maintaining system reliability. Consider:
    1. Current power consumption patterns
    2. Load balancing opportunities
    3. Energy efficiency improvements
    4. Backup power requirements
    Provide optimization recommendations with priority levels.
  expected_output: |
    JSON with optimization_level, reasoning, confidence, and load_balancing_plan.

security_assessment:
  description: |
    Analyze the security event data: {security_data}. Your primary goal is to assess security threats and 
    determine appropriate response levels. Consider:
    1. Threat severity and potential impact
    2. Current security posture
    3. Response protocols and procedures
    4. Coordination requirements with other systems
    Provide security assessment with recommended actions.
  expected_output: |
    JSON with security_level, reasoning, confidence, and response_actions.

network_assessment:
  description: |
    Analyze the network performance data: {network_data}. Your primary goal is to ensure optimal network 
    performance and security. Consider:
    1. Current network traffic patterns
    2. Performance bottlenecks
    3. Security vulnerabilities
    4. Optimization opportunities
    Provide network assessment with recommended actions.
  expected_output: |
    JSON with network_action, reasoning, confidence, and optimization_plan.

facility_coordination:
  description: |
    Analyze the combined facility status report: {facility_status_report}. The report contains summaries from 
    HVAC, Power, Security, and Network agents. Your primary goal is to identify inter-dependencies and potential 
    cascading effects. 1. Review all agent assessments. 2. Identify any conflicting recommendations 
    (e.g., HVAC needs more power, but Power agent wants to shed load). 3. Develop a coordinated action plan 
    that prioritizes overall facility stability and safety. 4. The plan should specify actions for each agent 
    if required. Provide a high-level coordination directive with: - overall_status: (green/yellow/red) 
    - priority_event: The most critical event to address. - coordinated_plan: A list of clear, actionable 
    directives for specific agents (e.g., "HVAC: Maintain current cooling. Power: Reroute non-essential load. 
    Security: Increase monitoring in Zone B."). - justification: A brief rationale for the plan.
  expected_output: |
    JSON with overall_status, priority_event, coordinated_plan, and justification.
```

### LLM Configuration

#### llm_config.py
```python
# LLM configuration for different agent types
LLM_CONFIG = {
    "hvac": {
        "model": "llama3.1:8b",
        "temperature": 0.1,
        "max_tokens": 1000,
        "priority": "HIGH"
    },
    "power": {
        "model": "llama3.1:8b", 
        "temperature": 0.1,
        "max_tokens": 1000,
        "priority": "HIGH"
    },
    "security": {
        "model": "llama3.1:8b",
        "temperature": 0.05,
        "max_tokens": 1000,
        "priority": "CRITICAL"
    },
    "network": {
        "model": "llama3.1:8b",
        "temperature": 0.1,
        "max_tokens": 1000,
        "priority": "HIGH"
    },
    "coordinator": {
        "model": "llama3.1:8b",
        "temperature": 0.2,
        "max_tokens": 1500,
        "priority": "CRITICAL"
    }
}
```

### Memory Management Configuration

#### Memory Optimization Settings
```python
# Memory management for RTX 4060 (8GB VRAM)
MEMORY_CONFIG = {
    "max_concurrent_models": 2,
    "memory_threshold_gb": 7,
    "eviction_policy": "LRU",
    "priority_levels": {
        "CRITICAL": 0,
        "HIGH": 1,
        "MEDIUM": 2,
        "LOW": 3
    },
    "cleanup_interval": 300,  # 5 minutes
    "memory_monitoring": True
}
```

---

## Development and Contribution

### Development Setup

#### Clone and Setup
```bash
# Clone the repository
git clone <repository-url>
cd intellicenter

# Create development environment
python -m venv dev-env
source dev-env/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install
```

#### Code Structure
```
intellicenter/
├── agents/                 # AI agent implementations
│   ├── hvac_agent.py
│   ├── power_agent.py
│   ├── security_agent.py
│   ├── network_agent.py
│   └── coordinator_agent.py
├── core/                  # Core system components
│   ├── event_bus.py
│   ├── async_crew.py
│   ├── memory_manager.py
│   ├── state_manager.py
│   └── fallback_responses.py
├── scenarios/             # Scenario implementations
│   ├── cooling_crisis.py
│   ├── security_breach.py
│   ├── energy_optimization.py
│   └── scenario_orchestrator.py
├── api/                   # API interfaces
│   └── websocket_server.py
├── llm/                  # LLM configuration
│   └── llm_config.py
├── config/               # Configuration files
│   ├── agents.yaml
│   ├── tasks.yaml
│   └── optimized_agents.yaml
└── tests/                # Test suites
    ├── agents/
    ├── core/
    ├── scenarios/
    ├── integration/
    └── compliance/
```

### Testing

#### Running Tests
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/agents/
pytest tests/scenarios/
pytest tests/integration/

# Run with coverage
pytest --cov=intellicenter

# Run specific test files
pytest tests/agents/test_hvac_agent.py
pytest tests/scenarios/test_cooling_crisis.py
```

#### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: Cross-component interaction testing
- **Scenario Tests**: End-to-end scenario execution
- **Performance Tests**: Response time and resource usage
- **Compliance Tests**: Security and regulatory compliance

### Code Quality

#### Linting and Formatting
```bash
# Run linting
flake8 intellicenter/
black intellicenter/
isort intellicenter/

# Run type checking
mypy intellicenter/

# Run security checks
bandit -r intellicenter/
```

#### Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run pre-commit manually
pre-commit run --all-files
```

### Contributing Guidelines

#### Pull Request Process
1. Fork the repository
2. Create a feature branch
3. Make changes with appropriate tests
4. Update documentation if needed
5. Run all tests and linting
6. Submit pull request with detailed description

#### Code Style
- Follow PEP 8 style guidelines
- Use type hints for all function signatures
- Write comprehensive docstrings
- Include unit tests for new features
- Update relevant documentation

#### Documentation Standards
- Update README.md for new features
- Add docstrings to all public functions
- Include usage examples in documentation
- Update CHANGELOG.md for version changes

---

## Performance Optimization

### Memory Management

#### RTX 4060 Optimization
```python
# Configure memory settings for 8GB VRAM
import os
os.environ['MAX_CONCURRENT_MODELS'] = '2'
os.environ['MEMORY_THRESHOLD_GB'] = '7'

# Use memory-efficient model loading
from intellicenter.llm.llm_config import get_llm
llm = get_llm("hvac", memory_efficient=True)
```

#### Performance Monitoring
```python
# Monitor memory usage
import psutil
memory_info = psutil.virtual_memory()
print(f"Memory usage: {memory_info.percent}%")

# Monitor GPU usage
import nvidia_ml_py3 as nvml
nvml.nvmlInit()
gpu_handle = nvml.nvmlDeviceGetHandleByIndex(0)
memory_info = nvml.nvmlDeviceGetMemoryInfo(gpu_handle)
print(f"GPU memory: {memory_info.used / 1024**3:.1f}GB / {memory_info.total / 1024**3:.1f}GB")
```

### Response Time Optimization

#### Async Processing
```python
# Use async/await for better performance
async def process_agent_requests():
    tasks = [
        process_hvac_data(),
        process_power_data(),
        process_security_data(),
        process_network_data()
    ]
    await asyncio.gather(*tasks)
```

#### Caching Strategies
```python
# Implement result caching
from functools import lru_cache

@lru_cache(maxsize=100)
def get_agent_response(agent_type, input_data):
    # Expensive computation here
    return compute_response(agent_type, input_data)
```

---

## Troubleshooting

### Common Issues

#### Agent Initialization Failures
```bash
# Check Ollama service
ollama list

# Verify model availability
ollama pull llama3.1:8b

# Check Python dependencies
pip list | grep -E "(crewai|fastapi|uvicorn)"
```

#### Memory Issues
```bash
# Monitor GPU memory
nvidia-smi

# Clear GPU memory
sudo nvidia-smi -gpu-reset -i 0

# Reduce concurrent models
export MAX_CONCURRENT_MODELS=1
```

#### WebSocket Connection Issues
```bash
# Test WebSocket server
curl http://localhost:8000/health

# Check port availability
netstat -tulpn | grep 8000

# Test frontend connection
curl http://localhost:5173
```

### Debug Mode

#### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set environment variable
export LOG_LEVEL=DEBUG
```

#### Debug Tools
```python
# Enable CrewAI debug mode
os.environ['CREWAI_DEBUG'] = 'true'

# Enable event bus debugging
from intellicenter.core.event_bus import EventBus
event_bus = EventBus()
event_bus.debug_mode = True
```

---

## Demo Operations

### Run order (final)
1. Start backend WebSocket server (port 8000)
   - Command:
     ```bash
     python -m intellicenter.api.websocket_server
     ```
   - Entry point: [intellicenter/api/websocket_server.py](intellicenter/api/websocket_server.py:1)
   - Endpoints: WS /ws, Health GET /health

2. Start frontend
   - Commands:
     ```bash
     cd frontend
     npm install
     npm run dev
     ```
   - Open http://localhost:5173
   - WebSocket target: ws://localhost:8000/ws (hook: [frontend/src/hooks/useWebSocket.ts](../frontend/src/hooks/useWebSocket.ts:1))

3. Run the demo
   - Fallback (recommended for first run; deterministic)
     ```bash
     python [run_demo.py](../run_demo.py:1) --mode fallback --scenario cooling_crisis --ws-port 8000 --speed 0.5 --timeout-s 12
     ```
   - Live example
     ```bash
     python [run_demo.py](../run_demo.py:1) --mode live --scenario routine_maintenance --ws-port 8000 --timeout-s 30
     ```
   - Scenarios: cooling_crisis, security_breach, energy_optimization, routine_maintenance

Tip: If the UI shows Disconnected, confirm the WebSocket server is running on 8000 and the frontend hook target matches ws://localhost:8000/ws (see [frontend/src/hooks/useWebSocket.ts](../frontend/src/hooks/useWebSocket.ts:1) and [docs/troubleshooting.md](troubleshooting.md:1)).

### Fallback vs Live

- Fallback mode
  - Deterministic playback from [dev-tools/responses](../dev-tools/responses/cooling_crisis.json:1)
  - Drive via [run_demo.py](../run_demo.py:1) with --mode fallback or directly with [dev-tools/demo_fallback.py](../dev-tools/demo_fallback.py:1)
  - Imports for fallback runner are re-exported from the Python package [dev_tools/demo_fallback.py](../dev_tools/demo_fallback.py:1) (used by [run_demo.py](../run_demo.py:1))
  - No LLM or heavy backends required

- Live mode
  - Real agents coordinate via scenario orchestrator [intellicenter/scenarios/scenario_orchestrator.py](../intellicenter/scenarios/scenario_orchestrator.py:1)
  - LLM configuration in [intellicenter/llm/llm_config.py](../intellicenter/llm/llm_config.py:1)
  - RTX 4060 constraints: default max concurrent models 2; memory threshold 7GB (see [intellicenter/core/memory_manager.py](../intellicenter/core/memory_manager.py:1))

### Reports

- The demo launcher saves a JSON report per run
  - Default path: generated by [get_default_report_path()](../run_demo.py:297) → ./demo-results/report_YYYYmmdd_HHMMSS.json
  - Override path: pass --report ./demo-results/my_report.json

- Example schema outline:
  ```json
  {
    "timestamp": "ISO-8601",
    "total_scenarios": 1,
    "successful_scenarios": 1,
    "failed_scenarios": 0,
    "scenarios": {
      "cooling_crisis": {
        "status": "success",
        "duration_seconds": 12.34,
        "timing_constraint_met": true
      }
    },
    "summary": {
      "total_duration_seconds": 12.34,
      "total_events": 42,
      "average_scenario_duration": 12.34,
      "success_rate": 1.0
    }
  }
  ```

- WebSocket port: 8000
- Frontend hook: [frontend/src/hooks/useWebSocket.ts](../frontend/src/hooks/useWebSocket.ts:1)
- Server: [intellicenter/api/websocket_server.py](../intellicenter/api/websocket_server.py:1)

## Support and Resources

### Documentation
- **Main Documentation**: [`docs/README.md`](README.md)
- **Demo Script**: [`docs/demo_script.md`](demo_script.md)
- **Architecture**: [`docs/ARCHITECTURE.md`](ARCHITECTURE.md)
- **Changelog**: [`CHANGELOG.md`](../CHANGELOG.md)

### Community
- **GitHub Issues**: Report bugs and request features
- **Discussions**: Share ideas and get help
- **Wiki**: Community knowledge base

### Additional Resources
- **CrewAI Documentation**: https://docs.crewai.com
- **Ollama Documentation**: https://github.com/ollama/ollama
- **FastAPI Documentation**: https://fastapi.tiangolo.com
- **WebSocket Documentation**: https://developer.mozilla.org/en-US/docs/Web/API/WebSocket

---

## License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.

---

*For the latest updates and documentation, please visit the [GitHub repository](https://github.com/your-repo/intellicenter).*