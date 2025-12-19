# IntelliCenter AGENT.md (Token-Efficient)

Goal
- Minimal, predictable guide for LLM agents and developers to work safely and fast on IntelliCenter.
- Inspired by OpenAI AGENTS.md; CrewAI best practices sourced via Context7.

Scope
- Backend: Python asyncio + CrewAI
- Frontend: React + Vite
- Orchestration: [EventBus](intellicenter/core/event_bus.py:5), [ScenarioOrchestrator](intellicenter/scenarios/scenario_orchestrator.py:91)
- Agents: [HVAC](intellicenter/agents/hvac_agent.py:43), [Power](intellicenter/agents/power_agent.py:40), [Security](intellicenter/agents/security_agent.py:41), [Network](intellicenter/agents/network_agent.py:67), [Coordinator](intellicenter/agents/coordinator_agent.py:162)
- LLM + Memory: [get_llm()](intellicenter/llm/llm_config.py:231), [AsyncCrewAI](intellicenter/core/async_crew.py:17), [create_optimized_crew()](intellicenter/core/async_crew.py:142)
- Config: agents/tasks in YAML under intellicenter/config/

-------------------------------------------------------------------------------

TL;DR Commands

Backend (tests)
- python -m pytest intellicenter/
- python -m pytest intellicenter/tests/core/
- python -m pytest intellicenter/tests/integration/

Frontend (dev)
- cd frontend
- npm install
- npm run dev
- Open http://localhost:5173

Focused checks
- Event bus perf: python -m pytest intellicenter/tests/core/test_event_performance.py
- Memory guardrails: python -m pytest intellicenter/tests/core/test_memory_manager.py

-------------------------------------------------------------------------------

Minimal Repo Map (Agents + Orchestration)

- Bus: [EventBus](intellicenter/core/event_bus.py:5)
- Orchestrator: [ScenarioOrchestrator](intellicenter/scenarios/scenario_orchestrator.py:91)
- LLM Manager: [get_llm()](intellicenter/llm/llm_config.py:231)
- Crew wrapper/factory: [AsyncCrewAI](intellicenter/core/async_crew.py:17), [create_optimized_crew()](intellicenter/core/async_crew.py:142)
- Agents:
  - [HVACControlAgent](intellicenter/agents/hvac_agent.py:43)
  - [PowerManagementAgent](intellicenter/agents/power_agent.py:40)
  - [SecurityOperationsAgent](intellicenter/agents/security_agent.py:41)
  - [NetworkMonitoringAgent](intellicenter/agents/network_agent.py:67)
  - [CoordinatorAgent](intellicenter/agents/coordinator_agent.py:162)
- Config:
  - [agents.yaml](intellicenter/config/agents.yaml)
  - [tasks.yaml](intellicenter/config/tasks.yaml)
  - [optimized_agents.yaml](intellicenter/config/optimized_agents.yaml)
  - [optimized_tasks.yaml](intellicenter/config/optimized_tasks.yaml)
- Architecture: docs/ARCHITECTURE.md, architecture.md

-------------------------------------------------------------------------------

How It Works (Super Short)

- Event-driven: Agents subscribe/publish via [EventBus](intellicenter/core/event_bus.py:5).
- Coordinator aggregates subsystem decisions and issues directives.
- Scenarios: [ScenarioOrchestrator](intellicenter/scenarios/scenario_orchestrator.py:91) triggers steps, waits for expected responses, evaluates success.

Key topics (examples)
- HVAC: hvac.temperature.changed, hvac.cooling.decision
- Power: power.consumption.changed, power.optimization.decision
- Security: security.access.suspicious, security.breach.detected, security.assessment.decision
- Network: facility.network.event, network.assessment.decision
- Coordination: facility.coordination.directive, facility.coordination.scenario_orchestration
- Scenario: demo.scenario.initialized/completed/failed

CrewAI Pattern (per agent)
- Centralized LLM selection: [get_llm()](intellicenter/llm/llm_config.py:231)
- Task schemas: [tasks.yaml](intellicenter/config/tasks.yaml) (prefer JSON/structured outputs)
- Fallbacks ensure continuity on LLM failure (see agents for examples)

-------------------------------------------------------------------------------

Token-Efficient Best Practices

Do
- Keep allow_delegation=False for specialists; only enable for Coordinator if needed.
- Use low verbosity by default; increase only in tests or debugging.
- Enforce max_execution_time from YAML.
- Prefer structured, short JSON outputs (no verbose chain-of-thought).
- Keep toolsets minimal and deterministic; add tests for edge cases.
- Reuse [get_llm()](intellicenter/llm/llm_config.py:231) and avoid direct LLM instantiation.
- Respect memory limits (RTX 4060): keep concurrent models ≤ 2; rely on optimizer in [AsyncCrewAI](intellicenter/core/async_crew.py:17).
- Publish idempotent events; validate payload shapes in tests.

Don’t
- Don’t change event names/payloads without updating subscribers, orchestrator, and tests.
- Don’t increase model sizes/concurrency without updating memory guardrails.
- Don’t log secrets or sensitive data.
- Don’t block the main asyncio loop; offload with asyncio.to_thread as done in agents.

-------------------------------------------------------------------------------

Runbook (Common)

- All agent tests: python -m pytest intellicenter/tests/agents/
- Scenarios: python -m pytest intellicenter/tests/scenarios/
- Integration: python -m pytest intellicenter/tests/integration/
- Frontend tests: cd frontend && npm test
- Lint (frontend): cd frontend && npm run lint

-------------------------------------------------------------------------------

Additions (Minimal Steps)

New agent
- Copy an existing pattern (e.g., [HVACControlAgent](intellicenter/agents/hvac_agent.py:43)).
- Add role/task to [agents.yaml](intellicenter/config/agents.yaml)/[tasks.yaml](intellicenter/config/tasks.yaml).
- Wire events via [EventBus](intellicenter/core/event_bus.py:5).
- Use [get_llm()](intellicenter/llm/llm_config.py:231).
- Add unit tests.

New scenario
- Extend in [ScenarioOrchestrator](intellicenter/scenarios/scenario_orchestrator.py:91) with steps, expected responses, cleanup, and timeouts.
- Add tests under intellicenter/tests/scenarios/.

-------------------------------------------------------------------------------

PR Rules (Brief)
- Title: [IntelliCenter] Short description
- All tests green (backend and frontend where applicable).
- Note memory/security implications if any.

-------------------------------------------------------------------------------

Pointers
- Bus: [EventBus](intellicenter/core/event_bus.py:5)
- Orchestrator: [ScenarioOrchestrator](intellicenter/scenarios/scenario_orchestrator.py:91)
- LLM + Memory: [get_llm()](intellicenter/llm/llm_config.py:231), [AsyncCrewAI](intellicenter/core/async_crew.py:17)
- Coordinator: [CoordinatorAgent](intellicenter/agents/coordinator_agent.py:162)
- Agents: [HVAC](intellicenter/agents/hvac_agent.py:43), [Power](intellicenter/agents/power_agent.py:40), [Security](intellicenter/agents/security_agent.py:41), [Network](intellicenter/agents/network_agent.py:67)
- Config: [agents.yaml](intellicenter/config/agents.yaml), [tasks.yaml](intellicenter/config/tasks.yaml)