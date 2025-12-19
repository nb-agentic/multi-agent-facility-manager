# IntelliCenter Troubleshooting Guide

**Quick Reference for Live Demo Recovery**

This guide provides fast, actionable solutions for common issues during IntelliCenter demonstrations. Each section includes a "one-minute recovery" cheatsheet for quick problem resolution.

---

## Known issues (demo-ready)

- ModuleNotFoundError: No module named 'dev_tools'
  - Ensure the Python package exists and is importable:
    - File present: [dev_tools/__init__.py](../dev_tools/__init__.py:1)
    - Run: `python -c "import dev_tools, sys; print('ok', sys.path[0])"`
  - Execute from repository root so the package is on PYTHONPATH.

- UI shows Disconnected
  - Verify WebSocket server is running on port 8000:
    - `curl http://localhost:8000/health`
    - Start if needed: `python -m intellicenter.api.websocket_server`
    - Server code: [intellicenter/api/websocket_server.py](../intellicenter/api/websocket_server.py:1)
  - Confirm frontend hook target matches ws://localhost:8000/ws:
    - Hook: [frontend/src/hooks/useWebSocket.ts](../frontend/src/hooks/useWebSocket.ts:1)

- Fallback scripts or responses missing
  - Check the responses under [dev-tools/responses](../dev-tools/responses/cooling_crisis.json:1)
  - Direct runner: [dev-tools/demo_fallback.py](../dev-tools/demo_fallback.py:1)
  - Note: [run_demo.py](../run_demo.py:1) imports fallback utilities from the Python package [dev_tools/demo_fallback.py](../dev_tools/demo_fallback.py:1)

### Quick restart commands
```bash
# Restart WebSocket server (port 8000)
pkill -f websocket_server || true
python -m intellicenter.api.websocket_server &

# Restart frontend dev server
pkill -f "vite" || true
cd frontend && npm run dev & cd ..

# Rehearse demo with fallback (cooling crisis)
python run_demo.py --mode fallback --scenario cooling_crisis --ws-port 8000 --speed 0.5 --timeout-s 12
```

## 1. Backend Startup and Agents

### Common Issues
- **Missing .env file**: Agents fail to initialize
- **Port conflicts**: WebSocket server won't start
- **Dependency issues**: Import errors or module not found
- **Ollama connection**: LLM service unavailable

### Quick Checks
```bash
# Test Python imports
python -c "import intellicenter; print('✅ Backend imports OK')"

# Check Ollama connection
curl http://localhost:11434/api/tags

# Test WebSocket server startup
python -m intellicenter.api.websocket_server --help

# Run specific agent tests
python -m pytest intellicenter/tests/agents/ -v
```

### Fix Flows

#### Missing .env File
```bash
# Create basic .env file
cat > .env << EOF
OLLAMA_HOST=http://localhost:11434
MAX_CONCURRENT_MODELS=2
MEMORY_THRESHOLD_GB=7
WEBSOCKET_HOST=localhost
WEBSOCKET_PORT=8000
LOG_LEVEL=INFO
EOF
```

#### Port Conflicts
```bash
# Check port 8000 usage
netstat -tulpn | grep 8000

# Kill conflicting process
sudo kill -9 <PID>

# Or change port in .env
echo "WEBSOCKET_PORT=8001" >> .env
```

#### Dependency Issues
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check specific packages
pip list | grep -E "(crewai|fastapi|uvicorn|pydantic)"

# Install missing packages
pip install crewai fastapi uvicorn websockets
```

### One-Minute Recovery
- [ ] Check `ollama list` for model availability
- [ ] Verify `.env` file exists with correct settings
- [ ] Run `python -m intellicenter.api.websocket_server` to test backend
- [ ] Run `python -m pytest intellicenter/tests/agents/ -q` for agent health
- [ ] Restart services if needed

---

## 2. WebSocket Connection Issues

### Common Issues
- **Client cannot connect**: Frontend shows "disconnected"
- **Frequent disconnects**: Connection instability
- **CORS errors**: Browser blocks WebSocket connection
- **Event bus not initialized**: No messages flowing

### Quick Checks
```bash
# Test WebSocket server health
curl http://localhost:8000/health

# Check WebSocket endpoint
curl -I http://localhost:8000/ws

# Monitor server logs
tail -f logs/websocket_server.log

# Test event bus initialization
python -c "from intellicenter.core.event_bus import EventBus; eb = EventBus(); print('✅ Event bus OK')"
```

### Fixes

#### Connection Issues
```bash
# Restart WebSocket server
pkill -f websocket_server
python -m intellicenter.api.websocket_server

# Check firewall settings
sudo ufw status
sudo ufw allow 8000

# Verify frontend WebSocket URL
# Should be: ws://localhost:8000/ws
```

#### Event Bus Problems
```bash
# Reset event bus state
python -c "
from intellicenter.core.event_bus import EventBus
eb = EventBus()
eb.reset()
print('✅ Event bus reset')
"

# Check event bus subscriptions
python -c "
from intellicenter.core.event_bus import EventBus
eb = EventBus()
print('Subscribers:', len(eb.subscribers))
"
```

#### CORS Configuration
```bash
# Check CORS settings in websocket_server.py
# Look for CORS middleware configuration
# Should allow: http://localhost:5173 (Vite dev server)
```

### One-Minute Recovery
- [ ] Check WebSocket server with `curl http://localhost:8000/health`
- [ ] Verify frontend WebSocket URL matches backend port
- [ ] Restart WebSocket server: `pkill -f websocket_server && python -m intellicenter.api.websocket_server`
- [ ] Check browser console for WebSocket errors
- [ ] Verify event bus has subscribers: `python -c "from intellicenter.core.event_bus import EventBus; print(len(EventBus().subscribers))"`

---

## 3. Scenarios Failing to Start or Complete

### Common Issues
- **Scenario not triggering**: No response to demo triggers
- **Timing violations**: Scenarios exceed time constraints
- **Agent coordination failures**: Multi-agent responses not working
- **Event bus communication**: Messages not reaching agents

### Quick Checks
```bash
# Test scenario orchestrator
python -c "
from intellicenter.scenarios.scenario_orchestrator import ScenarioOrchestrator
from intellicenter.core.event_bus import EventBus
eb = EventBus()
orchestrator = ScenarioOrchestrator(eb)
print('✅ Scenario orchestrator OK')
"

# Check scenario logs
tail -f logs/scenario_orchestrator.log

# Run specific scenario tests
python -m pytest intellicenter/tests/scenarios/test_cooling_crisis_e2e.py -v
```

### Fixes

#### Scenario Not Triggering
```bash
# Check orchestrator status
python -c "
from intellicenter.scenarios.scenario_orchestrator import ScenarioOrchestrator
from intellicenter.core.event_bus import EventBus
eb = EventBus()
orchestrator = ScenarioOrchestrator(eb)
print('Current state:', orchestrator.current_state)
print('Available scenarios:', orchestrator.available_scenarios)
"

# Manually trigger scenario
python -c "
from intellicenter.scenarios.scenario_orchestrator import ScenarioOrchestrator
from intellicenter.core.event_bus import EventBus
eb = EventBus()
orchestrator = ScenarioOrchestrator(eb)
import asyncio
asyncio.run(orchestrator.execute_scenario('cooling_crisis'))
"
```

#### Timing Violations
```bash
# Check timing constraints in scenario files
# Look for TIMEOUT constants and step durations
# Cooling Crisis: 120 seconds
# Security Breach: 90 seconds  
# Energy Optimization: 180 seconds
# Routine Maintenance: 60 seconds

# Enable debug logging
export LOG_LEVEL=DEBUG
```

#### Agent Coordination Issues
```bash
# Check agent subscriptions
python -c "
from intellicenter.core.event_bus import EventBus
eb = EventBus()
print('Agent subscriptions:')
for event, callbacks in eb.subscribers.items():
    print(f'  {event}: {len(callbacks)} subscribers')
"

# Test individual agent responses
python -m intellicenter.agents.hvac_agent --test
```

### One-Minute Recovery
- [ ] Check orchestrator state: `python -c "from intellicenter.scenarios.scenario_orchestrator import ScenarioOrchestrator; from intellicenter.core.event_bus import EventBus; print(ScenarioOrchestrator(EventBus()).current_state)"`
- [ ] Run fallback mode: `export FALLBACK_MODE=true`
- [ ] Verify agents are registered on event bus
- [ ] Check scenario logs for error messages
- [ ] Manually trigger test scenario

---

## 4. LLM and Fallback Behavior

### Common Issues
- **Ollama not running**: Service unavailable
- **Models not present**: Required models not loaded
- **LLM timeouts**: Slow or unresponsive models
- **Fallback not activating**: System doesn't degrade gracefully

### Quick Checks
```bash
# Check Ollama service
ollama list

# Test model availability
ollama pull llama3.1:8b

# Check LLM configuration
python -c "
from intellicenter.llm.llm_config import LLM_CONFIG
print('Available models:', list(LLM_CONFIG.keys()))
"

# Test fallback mode
python -c "
from intellicenter.core.fallback_responses import MockAgent
ma = MockAgent('hvac')
response = ma.generate_response('test input')
print('✅ Fallback working:', response)
"
```

### Fixes

#### Ollama Service Issues
```bash
# Start Ollama service
ollama serve

# Check if service is running
ps aux | grep ollama

# Test Ollama API
curl http://localhost:11434/api/tags
```

#### Model Loading Issues
```bash
# Pull required models
ollama pull llama3.1:8b

# Verify model loading
ollama list

# Check model sizes
ollama show llama3.1:8b
```

#### Force Fallback Mode
```bash
# Enable fallback mode
export FALLBACK_MODE=true

# Or modify agent initialization
python -c "
from intellicenter.core.fallback_responses import MockAgent
# Use MockAgent instead of real LLM
"
```

#### LLM Timeout Configuration
```bash
# Check timeout settings
python -c "
from intellicenter.llm.llm_config import LLM_CONFIG
for agent, config in LLM_CONFIG.items():
    print(f'{agent}: timeout={config.get(\"max_tokens\", \"N/A\")}')
"

# Reduce timeout for demo
export MAX_LLM_TIMEOUT=30
```

### One-Minute Recovery
- [ ] Check Ollama service: `ollama list`
- [ ] Pull missing models: `ollama pull llama3.1:8b`
- [ ] Enable fallback mode: `export FALLBACK_MODE=true`
- [ ] Test MockAgent: `python -c "from intellicenter.core.fallback_responses import MockAgent; print(MockAgent('hvac').generate_response('test'))"`
- [ ] Reduce model complexity if needed

---

## 5. Memory and Performance Issues

### Common Issues
- **Over 8GB usage**: RTX 4060 memory exceeded
- **7GB cleanup not firing**: Memory threshold not working
- **Slow response times**: Performance degradation
- **High CPU usage**: System overloaded

### Quick Checks
```bash
# Monitor GPU memory
nvidia-smi

# Check system memory
free -h

# Monitor CPU usage
htop

# Run memory compliance tests
python -m pytest intellicenter/tests/performance/test_memory_compliance.py -v

# Check memory optimizer logs
tail -f logs/memory_optimizer.log
```

### Fixes

#### Memory Management
```bash
# Check memory usage
nvidia-smi

# Clear GPU memory
sudo nvidia-smi -gpu-reset -i 0

# Reduce concurrent models
export MAX_CONCURRENT_MODELS=1

# Lower memory threshold
export MEMORY_THRESHOLD_GB=6
```

#### Performance Optimization
```bash
# Check memory optimizer integration
python -c "
from intellicenter.core.memory_manager import MemoryOptimizer
mo = MemoryOptimizer()
print('Memory usage:', mo.get_memory_usage())
print('Cleanup threshold:', mo.memory_threshold_gb)
"

# Enable memory monitoring
export MEMORY_MONITORING=true

# Check optimizer logs
tail -f logs/memory_optimizer.log
```

#### Concurrency Issues
```bash
# Reduce concurrent operations
export MAX_CONCURRENT_MODELS=1
export MAX_CONCURRENT_REQUESTS=2

# Enable memory-efficient mode
export MEMORY_EFFICIENT_MODE=true

# Check for memory leaks
python -c "
import psutil
import time
for i in range(5):
    mem = psutil.virtual_memory()
    print(f'Memory: {mem.percent}%')
    time.sleep(2)
"
```

### One-Minute Recovery
- [ ] Check GPU memory: `nvidia-smi`
- [ ] Clear GPU memory: `sudo nvidia-smi -gpu-reset -i 0`
- [ ] Reduce concurrency: `export MAX_CONCURRENT_MODELS=1`
- [ ] Run memory tests: `python -m pytest intellicenter/tests/performance/test_memory_compliance.py -q`
- [ ] Check memory optimizer logs

---

## 6. Frontend Issues

### Common Issues
- **Build errors**: Frontend fails to compile
- **Failing tests**: Test suite failures
- **Blank dashboard**: No UI displayed
- **WebSocket connection issues**: Real-time updates not working

### Quick Checks
```bash
# Test frontend build
cd frontend && npm run build && cd ..

# Run frontend tests
cd frontend && npm test && cd ..

# Check development server
cd frontend && npm run dev & cd ..

# Check console errors
# Open browser DevTools > Console
```

### Fixes

#### Build Errors
```bash
# Clear node modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
cd ..

# Check TypeScript errors
cd frontend && npm run typecheck && cd ..

# Check ESLint errors
cd frontend && npm run lint && cd ..
```

#### Test Failures
```bash
# Run specific tests
cd frontend && npm test -- --watchAll=false && cd ..

# Check test output
cd frontend && npm test -- --verbose && cd ..

# Update test dependencies
cd frontend && npm update && cd ..
```

#### Dashboard Issues
```bash
# Check Vite dev server
cd frontend && npm run dev & cd ..

# Verify WebSocket URL in App.tsx
# Should be: ws://localhost:8000/ws

# Check browser console for errors
# Look for WebSocket connection errors
```

#### WebSocket Frontend Issues
```bash
# Check useWebSocket hook
cat frontend/src/hooks/useWebSocket.ts

# Verify connection status handling
# Should show: connected, reconnecting, disconnected, fallback

# Test WebSocket connection manually
# Open browser DevTools > Console, run:
# new WebSocket('ws://localhost:8000/ws')
```

### One-Minute Recovery
- [ ] Test frontend build: `cd frontend && npm run build && cd ..`
- [ ] Run frontend tests: `cd frontend && npm test --silent && cd ..`
- [ ] Check browser console for errors
- [ ] Verify WebSocket URL configuration
- [ ] Restart frontend dev server: `cd frontend && pkill -f "vite" && npm run dev & cd ..`

---

## Emergency Quick Reference

### If Everything Breaks During Demo
```bash
# 1. Check basic services
ollama list
curl http://localhost:8000/health

# 2. Enable fallback mode
export FALLBACK_MODE=true

# 3. Restart critical services
pkill -f websocket_server
python -m intellicenter.api.websocket_server

# 4. Check memory
nvidia-smi
free -h

# 5. Run quick test
python -m pytest intellicenter/tests/agents/ -q
```

### System Health Check Script
```bash
#!/bin/bash
# Quick system health check

echo "=== IntelliCenter Health Check ==="
echo "1. Ollama Service:"
ollama list || echo "❌ Ollama not running"

echo "2. WebSocket Server:"
curl -s http://localhost:8000/health || echo "❌ WebSocket down"

echo "3. GPU Memory:"
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk '{printf "GPU: %.0f/%.0f MB\n", $1, $2}'

echo "4. System Memory:"
free -h | grep Mem | awk '{printf "RAM: %s/%s (%.0f%%)\n", $3, $2, $3/$2*100}'

echo "5. Backend Tests:"
python -m pytest intellicenter/tests/agents/ -q --tb=short

echo "=== Health Check Complete ==="
```

---

## Related Files

- [`intellicenter/api/websocket_server.py`](intellicenter/api/websocket_server.py:1) - WebSocket server implementation
- [`intellicenter/core/event_bus.py`](intellicenter/core/event_bus.py:1) - Event bus for agent communication
- [`frontend/src/hooks/useWebSocket.ts`](frontend/src/hooks/useWebSocket.ts:1) - Frontend WebSocket hook
- [`intellicenter/core/memory_manager.py`](intellicenter/core/memory_manager.py:1) - Memory optimization for RTX 4060
- [`intellicenter/scenarios/scenario_orchestrator.py`](intellicenter/scenarios/scenario_orchestrator.py:1) - Scenario execution logic
- [`intellicenter/core/fallback_responses.py`](intellicenter/core/fallback_responses.py:1) - Fallback response generation

---

*For comprehensive demo instructions, see [docs/demo_script.md](demo_script.md).*