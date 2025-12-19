# IntelliCenter Demo Script

## Overview
This document provides a comprehensive 15-minute demo script for showcasing the IntelliCenter multi-agent facility management system. The demo demonstrates real-time coordination between AI-powered agents for HVAC, security, power, and network infrastructure management in a data center environment.

**Demo Duration:** 15 minutes  
**Target Audience:** Technical stakeholders, potential clients, development teams  
**Key Focus:** Multi-agent coordination, real-time decision making, scenario orchestration

---

## Demo Setup

### Hardware Requirements
- **Development Machine:** Intel i7/i9 or AMD Ryzen 7/9 equivalent
- **GPU:** NVIDIA RTX 4060 (8GB VRAM) or higher for optimal LLM performance
- **RAM:** 16GB minimum, 32GB recommended
- **Storage:** 20GB free space
- **Network:** Stable internet connection for Ollama model access

### Software Requirements
- **Python 3.10+** with pip
- **Ollama** with Llama 3.1 8B model installed
- **Node.js 18+** for frontend
- **Web Browser:** Chrome, Firefox, or Edge (latest version)

### Environment Setup
```bash
# Clone and setup the repository
git clone <repository-url>
cd intellicenter

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies for frontend
cd frontend
npm install
cd ..

# Start Ollama service (if not already running)
ollama serve

# Pull required models
ollama pull llama3.1:8b
```

### Pre-Demo Checklist (Final)
- [ ] WebSocket server running on port 8000
  - Command:
    - `python -m intellicenter.api.websocket_server`
  - Entry point: [intellicenter/api/websocket_server.py](intellicenter/api/websocket_server.py:1)
- [ ] Frontend running at http://localhost:5173
  - Commands:
    - `cd frontend && npm install && npm run dev`
  - WebSocket target: `ws://localhost:8000/ws` (hook: [frontend/src/hooks/useWebSocket.ts](frontend/src/hooks/useWebSocket.ts:1))
- [ ] Quick rehearsal using fallback mode
  - Command:
    - `python [run_demo.py](run_demo.py:1) --mode fallback --scenario cooling_crisis --ws-port 8000 --speed 0.5 --timeout-s 12`
- [ ] Optional live check (after rehearsal)
  - Command:
    - `python [run_demo.py](run_demo.py:1) --mode live --scenario routine_maintenance --ws-port 8000 --timeout-s 30`
- [ ] Confirm dashboard shows Connected status; if Disconnected, see [docs/troubleshooting.md](docs/troubleshooting.md:1)

Note: If the UI shows Disconnected, verify the WebSocket server is running on port 8000 and that the frontend is targeting `ws://localhost:8000/ws` via [frontend/src/hooks/useWebSocket.ts](frontend/src/hooks/useWebSocket.ts:1). See the troubleshooting guide: [docs/troubleshooting.md](docs/troubleshooting.md:1).

---

## Demo Flow (15-Minute Timeline)

### 0:00 - 0:02: Introduction (2 minutes)
**Talking Points:**
- Welcome and overview of IntelliCenter
- Explain the multi-agent architecture
- Highlight key capabilities: real-time coordination, scenario orchestration, AI-powered decision making

**Actions:**
- Open the main README.md to show project structure
- Navigate to the frontend dashboard
- Show the agent status panel (should show all agents as "offline" initially)

**Technical Talking Points:**
- "IntelliCenter uses a distributed multi-agent architecture with specialized AI agents for each facility domain"
- "Each agent operates independently but coordinates through a centralized event bus"
- "The system supports real-time scenario orchestration with strict timing constraints"

### 0:02 - 0:05: System Architecture Overview (3 minutes)
**Talking Points:**
- Explain the agent roles and responsibilities
- Show the event-driven communication pattern
- Demonstrate the coordinator agent's role in conflict resolution

**Actions:**
- Navigate to `docs/ARCHITECTURE.md` (once created)
- Show the agent configuration files
- Demonstrate the event bus visualization (if available)

**Technical Talking Points:**
- "HVAC Agent: Manages temperature, humidity, and energy efficiency for cooling systems"
- "Power Agent: Optimizes power distribution and monitors energy consumption"
- "Security Agent: Handles access control, surveillance, and threat detection"
- "Network Agent: Ensures optimal network performance and connectivity"
- "Coordinator Agent: Orchestrates multi-agent responses and resolves conflicts"

### 0:05 - 0:10: Scenario Demonstrations (5 minutes)
**Focus:** Show all four scenarios with their unique characteristics

#### Scenario 1: Routine Maintenance (1 minute) - "Sanity Check"
**Trigger:** Scheduled maintenance window detected
**Timing:** 60-second completion constraint (lightweight and quick)
**Agents Involved:** HVAC, Network, Coordinator

**Demo Flow:**
1. Trigger routine maintenance scenario
2. Show HVAC agent's system status check
3. Display network agent's connectivity validation
4. Demonstrate coordinator's maintenance completion
5. Show successful maintenance verification

**Expected Timeline:**
- 0:05-0:06: Maintenance window detected
- 0:06-0:07: HVAC system status check
- 0:07-0:08: Network connectivity validation
- 0:08-0:09: Coordinator maintenance completion
- 0:09-0:10: Maintenance verification and success

**Technical Talking Points:**
- "Routine Maintenance scenario demonstrates lightweight coordination for quick demonstrations"
- "HVAC agent performs system status checks and validation"
- "Network agent validates connectivity and performance metrics"
- "Coordinator orchestrates maintenance completion and verification"
- "Scenario completes within 60-second constraint for fast, reliable demos"

#### Scenario 2: Cooling Crisis (1.5 minutes)
**Trigger:** Temperature exceeds 89.5°F (32°C)
**Timing:** 2-minute completion constraint
**Agents Involved:** HVAC, Power, Security, Coordinator

**Demo Flow:**
1. Trigger cooling crisis scenario
2. Show HVAC agent's emergency cooling response
3. Display power agent's optimization decisions
4. Demonstrate security agent's increased monitoring
5. Show coordinator's orchestration of all responses

**Expected Timeline:**
- 0:10-0:11: Crisis triggered (temperature spike)
- 0:11-0:12: HVAC emergency response
- 0:12-0:13: Power optimization decisions
- 0:13-0:14: Security monitoring increase
- 0:14-0:15: Coordinator orchestration and resolution

**Technical Talking Points:**
- "Cooling Crisis scenario demonstrates emergency response coordination"
- "HVAC agent implements emergency cooling protocols"
- "Power agent supports with optimized power allocation"
- "Security agent increases monitoring during emergency"
- "Coordinator ensures all actions work together harmoniously"

#### Scenario 3: Security Breach (1.5 minutes)
**Trigger:** Unauthorized access attempt detected
**Timing:** 90-second completion constraint
**Agents Involved:** Security, Network, Coordinator

**Demo Flow:**
1. Trigger security breach scenario
2. Show security agent's threat assessment
3. Display network agent's isolation response
4. Demonstrate coordinator's lockdown coordination
5. Show breach containment verification

**Expected Timeline:**
- 0:15-0:16: Breach detected (unauthorized access)
- 0:16-0:17: Security threat assessment
- 0:17-0:18: Network isolation initiated
- 0:18-0:19: Coordinator lockdown coordination
- 0:19-0:20: Containment verification

**Technical Talking Points:**
- "Security Breach scenario shows rapid threat response"
- "Security agent implements access control and surveillance"
- "Network agent isolates affected systems"
- "Coordinator orchestrates facility-wide lockdown"
- "All actions completed within 90-second constraint"

#### Scenario 4: Energy Optimization (2 minutes)
**Trigger:** Energy price drop detected
**Timing:** 3-minute completion constraint
**Agents Involved:** Power, HVAC, Coordinator

**Demo Flow:**
1. Trigger energy optimization scenario
2. Show power agent's price-based optimization
3. Display HVAC agent's pre-cooling response
4. Demonstrate coordinator's energy coordination
5. Show optimization results and savings

**Expected Timeline:**
- 0:20-0:21: Price drop detected
- 0:21-0:22: Power optimization decisions
- 0:22-0:23: HVAC pre-cooling initiation
- 0:23-0:24: Coordinator energy coordination
- 0:24-0:25: Optimization results and savings calculation

**Technical Talking Points:**
- "Energy Optimization scenario demonstrates cost-saving coordination"
- "Power agent identifies energy arbitrage opportunities"
- "HVAC agent implements pre-cooling strategies"
- "Coordinator ensures optimal energy utilization"
- "System achieves significant cost savings while maintaining performance"

#### Scenario 4: Routine Maintenance (1 minute)
**Trigger:** Scheduled maintenance window detected
**Timing:** 60-second completion constraint (lightweight and quick)
**Agents Involved:** HVAC, Network, Coordinator

**Demo Flow:**
1. Trigger routine maintenance scenario
2. Show HVAC agent's system status check
3. Display network agent's connectivity validation
4. Demonstrate coordinator's maintenance completion
5. Show successful maintenance verification

**Expected Timeline:**
- 0:20-0:21: Maintenance window detected
- 0:21-0:22: HVAC system status check
- 0:22-0:23: Network connectivity validation
- 0:23-0:24: Coordinator maintenance completion
- 0:24-0:25: Maintenance verification and success

**Technical Talking Points:**
- "Routine Maintenance scenario demonstrates lightweight coordination for quick demonstrations"
- "HVAC agent performs system status checks and validation"
- "Network agent validates connectivity and performance metrics"
- "Coordinator orchestrates maintenance completion and verification"
- "Scenario completes within 60-second constraint for fast, reliable demos"

### 0:25 - 0:28: Interactive Demonstration (3 minutes)
**Talking Points:**
- Show manual override capabilities
- Demonstrate real-time monitoring
- Highlight performance metrics and analytics

**Actions:**
- Use frontend dashboard to trigger scenarios manually
- Show agent status updates in real-time
- Display performance metrics and response times
- Demonstrate manual override functionality

**Technical Talking Points:**
- "Manual override capabilities allow human intervention when needed"
- "Real-time monitoring provides complete visibility into agent operations"
- "Performance metrics track response times and decision quality"
- "WebSocket integration ensures seamless real-time communication"

### 0:28 - 0:30: Conclusion and Q&A (2 minutes)
**Talking Points:**
- Summarize key capabilities and benefits
- Discuss technical architecture and scalability
- Address questions and next steps

**Actions:**
- Review demo highlights
- Show documentation and resources
- Provide contact information for follow-up

**Technical Talking Points:**
- "IntelliCenter demonstrates enterprise-grade multi-agent coordination"
- "System scales to support additional agent types and scenarios"
- "Comprehensive documentation and testing ensure reliability"
- "Ready for production deployment with proper infrastructure"

---

## Detailed Scenario Breakdowns

### Cooling Crisis Scenario
**Objective:** Respond to temperature emergency in data center
**Time Constraint:** 2 minutes (120 seconds)
**Success Criteria:** Temperature stabilized below 85°F, all systems operational

**Step-by-Step Execution:**
1. **Trigger (0s):** Temperature exceeds 89.5°F threshold
2. **HVAC Response (10s):** Emergency cooling activated, maximum cooling level
3. **Power Coordination (30s):** Power optimization for cooling support
4. **Security Monitoring (60s):** Increased surveillance during emergency
5. **Coordination (90s):** Multi-agent coordination and resolution verification
6. **Completion (120s):** Temperature stabilized, systems normal

**Key Features to Highlight:**
- Emergency cooling protocols
- Cross-system coordination
- Real-time temperature monitoring
- Automated response escalation

### Security Breach Scenario
**Objective:** Respond to unauthorized access attempt
**Time Constraint:** 90 seconds
**Success Criteria:** Breach contained, systems secured, threat eliminated

**Step-by-Step Execution:**
1. **Trigger (0s):** Unauthorized access attempt detected
2. **Security Assessment (15s):** Threat level evaluation and response planning
3. **Network Isolation (30s):** Affected systems isolated from network
4. **Lockdown Coordination (60s):** Facility-wide security lockdown
5. **Containment Verification (75s):** Breach contained and threat eliminated
6. **Completion (90s):** Systems secured, normal operations resumed

**Key Features to Highlight:**
- Multi-layered security response
- Network isolation capabilities
- Real-time threat assessment
- Automated security protocols

### Energy Optimization Scenario
**Objective:** Optimize energy consumption based on price fluctuations
**Time Constraint:** 3 minutes (180 seconds)
**Success Criteria:** Energy costs reduced, performance maintained

**Step-by-Step Execution:**
1. **Trigger (0s):** Energy price drop detected
2. **Price Analysis (30s):** Optimization opportunity evaluation
3. **Power Optimization (60s):** Load balancing and arbitrage decisions
4. **HVAC Pre-cooling (120s):** Temperature optimization using cheap energy
5. **Coordination (150s):** Multi-agent energy coordination
6. **Completion (180s):** Optimization complete, savings calculated

**Key Features to Highlight:**
- Price-based energy optimization
- Pre-cooling strategies
- Energy arbitrage opportunities
- Cost savings calculations

### Routine Maintenance Scenario
**Objective:** Perform routine system checks and validation during maintenance windows
**Time Constraint:** 1 minute (60 seconds) - lightweight and quick for demonstrations
**Success Criteria:** Systems validated, maintenance completed successfully

**Step-by-Step Execution:**
1. **Trigger (0s):** Scheduled maintenance window detected
2. **HVAC Check (15s):** System status check and validation
3. **Network Validation (30s):** Connectivity and performance verification
4. **Coordination (45s):** Multi-agent coordination and completion
5. **Completion (60s):** Maintenance verification and success confirmation

**Key Features to Highlight:**
- Lightweight coordination for quick demonstrations
- Simple status checks rather than complex decision-making
- 60-second maximum duration for fast, reliable demos
- Clear success indicators for demonstration purposes

---

## Troubleshooting Guide

### Common Demo Issues and Solutions

#### 1. Agent Initialization Failures
**Symptoms:** Agents show "offline" status, no responses generated
**Possible Causes:**
- Ollama service not running
- Models not properly loaded
- Memory constraints
- Network connectivity issues

**Solutions:**
```bash
# Check Ollama service status
ollama list

# Ensure models are loaded
ollama pull llama3.1:8b

# Check memory usage
nvidia-smi

# Restart services
ollama serve
```

#### 2. Slow Response Times
**Symptoms:** Agents take too long to respond, demo timing affected
**Possible Causes:**
- High system load
- Insufficient GPU memory
- Network latency
- Model loading delays

**Solutions:**
```bash
# Monitor system resources
htop
nvidia-smi

# Clear GPU memory
sudo nvidia-smi -gpu-reset -i 0

# Check network connectivity
ping ollama.local
```

#### 3. WebSocket Connection Issues
**Symptoms:** Frontend cannot connect to WebSocket server
**Possible Causes:**
- Port 8000 already in use
- Firewall blocking connections
- CORS configuration issues
- Event bus not properly initialized

**Solutions:**
```bash
# Check port usage
netstat -tulpn | grep 8000

# Test WebSocket connection
curl -I http://localhost:8000/health

# Check event bus status
python -c "from intellicenter.core.event_bus import EventBus; print(EventBus())"
```

#### 4. Scenario Execution Failures
**Symptoms:** Scenarios don't trigger or complete properly
**Possible Causes:**
- Event bus subscriptions not set up
- Agent communication issues
- Timing constraint violations
- Configuration errors

**Solutions:**
```bash
# Check event bus subscriptions
python -c "from intellicenter.core.event_bus import EventBus; eb = EventBus(); print(eb.subscribers)"

# Test individual agents
python -m intellicenter.agents.hvac_agent

# Validate configuration
python -c "import yaml; print(yaml.safe_load(open('intellicenter/config/agents.yaml')))"
```

#### 5. Memory Management Issues
**Symptoms:** System becomes unresponsive, memory errors
**Possible Causes:**
- RTX 4060 memory constraints (8GB limit)
- Too many concurrent models
- Memory leaks in agent operations
- Insufficient system RAM

**Solutions:**
```bash
# Monitor memory usage
nvidia-smi
free -h

# Clear GPU memory
sudo nvidia-smi -gpu-reset -i 0

# Reduce concurrent models
export MAX_CONCURRENT_MODELS=1

# Restart Python environment
source deactivate
source venv/bin/activate
```

### Performance Optimization Tips

#### For RTX 4060 (8GB VRAM)
```bash
# Set optimal memory limits
export MAX_CONCURRENT_MODELS=2
export MEMORY_THRESHOLD_GB=7

# Use memory-efficient model settings
export MODEL_SIZE="8b"
export QUANTIZATION="q4"
```

#### System-Level Optimizations
```bash
# Increase file descriptor limits
ulimit -n 65536

# Set optimal Python settings
export PYTHONUNBUFFERED=1
export PYTHONASYNCIODEBUG=0

# Disable unnecessary logging
export LOG_LEVEL=WARNING
```

---

## Demo Best Practices

### Preparation
1. **Test thoroughly** before presenting
2. **Have backup scenarios** ready
3. **Prepare talking points** for technical questions
4. **Test network connectivity** and system resources
5. **Prepare environment** in advance

### During Demo
1. **Speak clearly** and at moderate pace
2. **Explain technical concepts** in accessible terms
3. **Highlight key features** as they occur
4. **Maintain timing** for each scenario
5. **Be prepared** for technical questions

### Post-Demo
1. **Provide documentation** resources
2. **Collect feedback** on the demo
3. **Follow up** with interested parties
4. **Document lessons learned** for future demos
5. **Clean up test environment** and reset scenarios

## If It Breaks Live

🚨 **Quick Recovery Guide**

If you encounter issues during the demo, follow these steps:

1. **Check the troubleshooting guide**: [docs/troubleshooting.md](troubleshooting.md)
2. **Enable fallback mode**: `export FALLBACK_MODE=true`
3. **Restart WebSocket server**: `pkill -f websocket_server && python -m intellicenter.api.websocket_server`
4. **Check Ollama service**: `ollama list`
5. **Run quick health check**: See troubleshooting guide Section 1

**Emergency Commands** (have these ready):
```bash
# Quick system reset
pkill -f websocket_server
python -m intellicenter.api.websocket_server &

# Enable fallback mode
export FALLBACK_MODE=true

# Check basic services
ollama list && curl http://localhost:8000/health
```

**Fallback Demo Mode** - If it breaks live:
Use the pre-recorded fallback mode to continue your demo without LLM dependencies:

```bash
# Run cooling crisis scenario with 0.5x speed
python dev-tools/demo_fallback.py --scenario cooling_crisis --speed 0.5

# Run security breach scenario with WebSocket server
python dev-tools/demo_fallback.py --scenario security_breach --ws-port 8000 --host localhost

# Run energy optimization with faster timing
python dev-tools/demo_fallback.py --scenario energy_optimization --speed 0.2

# List available scenarios
python dev-tools/demo_fallback.py --list-scenarios

# Run custom script file
python dev-tools/demo_fallback.py --scenario custom --script /path/to/custom_script.json
```

The fallback mode publishes realistic event streams to the EventBus, so the dashboard will update as if live. No LLMs or heavy backends required!

**Remember**: The system is designed to degrade gracefully. If LLMs are unavailable, the fallback mode will provide realistic responses that demonstrate the coordination logic.

---

## Additional Resources

### Documentation
- [`docs/README.md`](README.md) - Comprehensive project documentation
- [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) - System architecture overview
- [`CHANGELOG.md`](../CHANGELOG.md) - Version history and updates

### Configuration
- [`intellicenter/config/agents.yaml`](../intellicenter/config/agents.yaml) - Agent configurations
- [`intellicenter/config/tasks.yaml`](../intellicenter/config/tasks.yaml) - Task definitions
- [`intellicenter/llm/llm_config.py`](../intellicenter/llm/llm_config.py) - LLM configuration

### Testing
- Run agent tests: `python -m pytest intellicenter/tests/agents/`
- Run scenario tests: `python -m pytest intellicenter/tests/scenarios/`
- Run integration tests: `python -m pytest intellicenter/tests/integration/`

### Support
- **GitHub Issues:** Report bugs and request features
- **Documentation:** Refer to comprehensive guides
- **Community:** Join discussions and share experiences

---

*This demo script is designed to showcase the IntelliCenter multi-agent facility management system's capabilities. Adjust timing and content based on specific audience interests and technical requirements.*