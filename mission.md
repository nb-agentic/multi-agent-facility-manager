# IntelliCenter Mission

**Objective:** Build and maintain a collaborative multi-agent facility management system for data center operations.

## Description
IntelliCenter is an AI-powered multi-agent system that orchestrates facility management through specialized agents:

1. **HVAC Control Agent** - Thermal management and environmental control
2. **Power Management Agent** - Energy optimization and distribution
3. **Security Operations Agent** - Access control and threat detection
4. **Network Infrastructure Agent** - Network monitoring and optimization
5. **Facility Coordinator Agent** - Cross-system orchestration and decision aggregation

## Architecture
- **Backend**: Python asyncio + CrewAI framework
- **Frontend**: React + Vite + TypeScript dashboard
- **Communication**: Event-driven via EventBus
- **LLM**: Local inference optimized for RTX 4060

## Success Criteria
- Agent response time < 2 seconds for real-time decision making
- Memory usage < 8GB for stable operation on constrained hardware
- All 5 agents operating concurrently without memory overflow
- Complex facility scenarios handled autonomously
- Real-time coordination with < 500ms communication latency

## Current Focus
Refactoring and enhancement work to improve:
- Code quality and maintainability
- Test coverage and reliability
- Performance optimization
- Documentation completeness

## Key Files
- Entry points: `main.py`, `run_app.py`, `run_demo.py`
- Agents: `intellicenter/agents/`
- Event system: `intellicenter/core/event_bus.py`
- LLM config: `intellicenter/llm/llm_config.py`
- Frontend: `frontend/`
