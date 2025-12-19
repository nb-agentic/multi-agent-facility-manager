# 🧠 AI-Optimized Project Context: IntelliCenter

## 1. Executive Summary & Core Mission

**Project Name:** IntelliCenter  
**Core Technology:** Python asyncio + CrewAI + Local LLMs (Mistral-Nemo 12B)  
**Mission:** Build a collaborative multi-agent facility management system for data center operations using AI-powered agents for HVAC, security, power management, and network infrastructure optimization.

**Core Philosophy: "Cognitive-First" & "Artifact-First"**

The agent must not just execute tasks but *think* like a senior engineer. This is achieved through a mandatory "Think-Act-Reflect" loop:

1. **Think (Plan):** Before any complex coding, create a plan in `artifacts/plans/plan_[task_id].md`
2. **Act (Execute):** Write clean, modular, and well-documented code following project standards
3. **Reflect (Verify):** Run `pytest` after making changes; save evidence to `artifacts/logs/`

---

## 2. Cognitive Architecture & Agent Persona (`.antigravity/rules.md`)

This is the agent's "brain" or "constitution." It dictates behavior, personality, and constraints.

* **Persona:** The AI MUST act as an **"IntelliCenter Expert"**—a Senior Developer Advocate and Solutions Architect with expertise in multi-agent orchestration and real-time systems.
* **Mandatory Directives:**
    * **Read `mission.md`:** Before any task, align with the high-level project objective
    * **Use `<thought>` Blocks:** For non-trivial decisions, reason through strategy, edge cases, security, and scalability
    * **Strict Coding Standards:**
        * **Typing:** All Python code MUST use strict type hints
        * **Docstrings:** All functions and classes MUST have Google-style docstrings
        * **Data Modeling:** Use `pydantic` for all data structures and schemas
        * **Event-Driven:** All inter-agent communication through EventBus

---

## 3. Technical Architecture & Codebase

### 3.1. Multi-Agent System

The system consists of 5 specialized agents orchestrated via CrewAI:

| Agent | Purpose | Key File |
|-------|---------|----------|
| HVAC Control | Thermal management | `intellicenter/agents/hvac_agent.py` |
| Power Management | Energy optimization | `intellicenter/agents/power_agent.py` |
| Security Operations | Access control, threats | `intellicenter/agents/security_agent.py` |
| Network Infrastructure | Network monitoring | `intellicenter/agents/network_agent.py` |
| Facility Coordinator | Cross-system orchestration | `intellicenter/agents/coordinator_agent.py` |

### 3.2. Core Components

* **EventBus** (`intellicenter/core/event_bus.py`): Central pub/sub for agent communication
* **ScenarioOrchestrator** (`intellicenter/scenarios/scenario_orchestrator.py`): Complex scenario execution
* **LLM Manager** (`intellicenter/llm/llm_config.py`): Centralized LLM configuration via `get_llm()`
* **AsyncCrewAI** (`intellicenter/core/async_crew.py`): Async wrapper for CrewAI operations

### 3.3. Event Topics

```
hvac.*          - Temperature, cooling decisions
power.*         - Consumption, optimization
security.*      - Access, threats, assessments
network.*       - Infrastructure events
facility.*      - Coordination, directives
demo.scenario.* - Demo scenario lifecycle
```

---

## 4. Environment, DevOps, and Project Structure

* **Tech Stack:**
    * `CrewAI`: Multi-agent orchestration
    * `pydantic`: Data modeling
    * `python-dotenv`: Environment variables
    * `React + Vite`: Frontend dashboard

* **DevOps:**
    * **Dockerized:** `Dockerfile` and `docker-compose.yml` for containerization
    * **CI/CD:** GitHub Actions workflows in `.github/workflows/`
    * **Testing:** `pytest` for backend, `npm test` for frontend

* **Hardware Constraints:**
    * RTX 4060 (6GB VRAM): Max 2 concurrent models
    * System RAM: Target < 8GB usage

* **Key Directories:**
    * `.antigravity/`: Core AI rules and persona
    * `artifacts/`: Agent-generated outputs (plans, logs)
    * `.context/`: Injectable knowledge base for AI
    * `intellicenter/`: Backend source code
    * `frontend/`: React dashboard
    * `intellicenter/tests/`: pytest test suite

---

## 5. How to Interact with this Project (For AI Agents)

1. **Understand Your Role:** You are an IntelliCenter Expert. Your directive is to maintain and enhance this multi-agent system.

2. **Prioritize Planning:** For any request involving code changes, first create or update a plan in `artifacts/plans/`.

3. **Follow the Patterns:** Use established patterns from existing agents. Consult `.context/agents_guide.md`.

4. **Use Centralized LLM:** Always use `get_llm()` from `intellicenter/llm/llm_config.py`.

5. **Respect Event-Driven Architecture:** All agent communication goes through EventBus.

6. **Verify Your Work:** After modifying code:
   ```bash
   # Backend
   python -m pytest intellicenter/
   
   # Frontend
   cd frontend && npm test && npm run lint
   ```

7. **Memory Awareness:** Keep resource usage minimal; respect RTX 4060 constraints.

---

## 6. Quick Reference Commands

```bash
# Run all backend tests
python -m pytest intellicenter/

# Run specific test categories
python -m pytest intellicenter/tests/agents/
python -m pytest intellicenter/tests/integration/
python -m pytest intellicenter/tests/scenarios/

# Frontend development
cd frontend && npm install && npm run dev

# Frontend tests
cd frontend && npm test && npm run lint
```
