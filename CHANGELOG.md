# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### 0.1.0 Demo-Ready Summary
- feat(demo): Single-command launcher [run_demo.py](run_demo.py:1) with fallback and live modes; default report path via [get_default_report_path()](run_demo.py:297)
- feat(ui): WebSocket reconnection and status, core dashboard components [frontend/src/components/FacilityLayout.tsx](frontend/src/components/FacilityLayout.tsx:1), [frontend/src/components/AgentStatus.tsx](frontend/src/components/AgentStatus.tsx:1), [frontend/src/components/PerformancePanel.tsx](frontend/src/components/PerformancePanel.tsx:1)
- feat(core): Event bus [intellicenter/core/event_bus.py](intellicenter/core/event_bus.py:1), Scenario orchestrator [intellicenter/scenarios/scenario_orchestrator.py](intellicenter/scenarios/scenario_orchestrator.py:1), memory manager tweaks [intellicenter/core/memory_manager.py](intellicenter/core/memory_manager.py:1)
- feat(api): WebSocket server [intellicenter/api/websocket_server.py](intellicenter/api/websocket_server.py:1) broadcasting bus events to /ws with /health probe (port 8000)
- docs: Finalized quick start, demo operations, architecture flow, demo script, troubleshooting with package re-export [dev_tools/demo_fallback.py](dev_tools/demo_fallback.py:1) and responses under [dev-tools/responses](dev-tools/responses/cooling_crisis.json:1)

### Added
- **spec(intellicenter-demo-readiness): task 29 — Add fallback demo mode with pre-recorded responses and CLI runner**: Implemented emergency fallback demo mode that plays pre-recorded, deterministic responses without requiring LLMs. Created dev-tools/demo_fallback.py with comprehensive CLI interface supporting all four scenarios (cooling_crisis, security_breach, energy_optimization, routine_maintenance), speed control, repeat functionality, and WebSocket server integration. Added dev-tools/responses/ directory with JSON event sequences for each scenario, comprehensive test suite with pytest-asyncio, and updated documentation with fallback mode usage instructions and quick links.
- **spec(intellicenter-demo-readiness): task 27 — Add demo troubleshooting documentation and enhance demo script**: Created comprehensive troubleshooting guide with fast-lookup sections for backend startup, WebSocket issues, scenario failures, LLM problems, memory issues, and frontend problems. Enhanced demo script to cover all four scenarios (Routine Maintenance, Cooling Crisis, Security Breach, Energy Optimization) with proper timing, added "If It Breaks Live" recovery section, and cross-linked troubleshooting documentation. Updated both docs/README.md and top-level README.md with demo quick links for easy access during live demonstrations.
- **spec(intellicenter-demo-readiness): task 26 — Add recovery manager tests**: Added deterministic, CI-friendly test suite validating RecoveryManager behavior: agent failure detection, restart within the 30-second SLA, fallback activation on repeated failures, proper event emissions, and no infinite restart loops. Uses monkeypatching to avoid real waits and avoids relying on GPUs or external services.
- **spec(intellicenter-demo-readiness): task 24 — Implement WebSocket stability tests**: Added comprehensive integration tests to validate WebSocket stability, reconnection behavior, and message delivery reliability over prolonged sessions using accelerated timing for CI compatibility; includes tests for long-running connection stability (simulated 30-minute session), automatic reconnection with multiple disconnect/reconnect cycles, message delivery reliability under high churn (100-500 message bursts), heartbeat/ping-pong handling, and deterministic cleanup with proper resource management
- **spec(intellicenter-demo-readiness): task 23 — Add end-to-end test for Energy Optimization scenario**: Implemented comprehensive end-to-end test that executes the full Energy Optimization scenario through the real scenario orchestrator and event bus, verifies key multi-agent coordination (Power, HVAC, Network), and enforces the 3-minute timing constraint with fallback resilience for LLM unavailability
- **spec(intellicenter-demo-readiness): task 22 — Add end-to-end test for Security Breach scenario**: Implemented comprehensive end-to-end test that executes the full Security Breach scenario through the real scenario orchestrator and event bus, verifies key agent responses, and enforces the 90-second timing constraint with fallback resilience for LLM unavailability
- **spec(intellicenter-demo-readiness): task 21 — Add end-to-end test for Cooling Crisis scenario**: Implemented comprehensive end-to-end test that executes the full Cooling Crisis scenario through the real scenario orchestrator and event bus, verifies key agent responses, and enforces the 2-minute timing constraint with fallback resilience for LLM unavailability
- **Final integration testing and performance validation**: Comprehensive testing of all system components including unit tests (406 tests, 125 failures identified), integration tests (8 tests, async support added), and scenario validation for all three demo scenarios
- **Demo test script fixes**: Fixed parameter passing issues in demo test script for Security Breach scenario, ensuring proper string literal handling for location and severity parameters
- **Memory validation testing**: Tested memory management system against RTX 4060 constraints (8GB limit, 7GB trigger), identified memory usage exceeding limits (8.3-8.5GB observed during testing)
- **Performance benchmarking**: Executed performance benchmarks for all three scenarios with timing constraints validation, response time monitoring, and memory usage tracking
- **Scenario execution validation**: Successfully validated all three demo scenarios (Cooling Crisis, Security Breach, Energy Optimization) with proper initialization, execution, and status reporting
- **Test artifact generation**: Generated comprehensive test results including scenario results, performance benchmarks, memory validation reports, and demo readiness reports
- **Comprehensive demo script and documentation**: Complete 15-minute demo script with timing breakdown, step-by-step scenario instructions, technical talking points, troubleshooting guide, and hardware setup instructions for Cooling Crisis, Security Breach, and Energy Optimization scenarios
- **Project documentation hub**: Created comprehensive README.md with installation, usage, API documentation, configuration options, development guidelines, LLM & memory configuration, and contribution guidelines
- **Architecture documentation**: Added system architecture overview with component interaction patterns, event flow diagrams, memory/performance considerations, and scenario orchestration design patterns
- **Demo-ready status**: Updated main README.md with demo-ready banner, quick start guide, documentation links, and system requirements/compatibility notes
- **Energy Optimization scenario implementation**: Complete energy efficiency scenario with Power-HVAC-Coordinator multi-agent coordination, 3-minute completion constraint, and step-by-step execution workflow
- **Energy efficiency triggers**: Implemented high consumption pattern detection including price drop monitoring, energy arbitrage opportunity identification, and pre-cooling strategy activation
- **Power-HVAC-Coordinator coordination**: Enhanced multi-agent coordination for energy optimization with event bus integration for power optimization decisions, HVAC cooling responses, and facility coordination directives
- **3-minute timing constraint**: Implemented strict 180-second completion window with step-by-step timing coordination, deadline monitoring, and automatic failure handling for timeout scenarios
- **Step-by-step scenario execution**: Added 5-step energy optimization workflow (normal operation, price drop detection, optimization opportunity, pre-cooling initiation, coordination response) with proper timing and agent coordination
- **Energy arbitrage logic**: Implemented smart energy optimization strategies including price-based decision making, pre-cooling temperature targets, and estimated savings calculations
- **Performance metrics tracking**: Added comprehensive energy optimization metrics including response times, agent coordination success rates, energy savings achievements, and pre-cooling success rates
- **Energy Optimization scenario integration**: Integrated with existing scenario orchestrator for seamless demo execution and orchestrator event handling with test trigger functionality
- **Comprehensive Energy Optimization unit tests**: Added 20+ unit tests covering energy efficiency triggers, multi-agent coordination, timing constraints, step execution, performance metrics, and end-to-end scenario execution
- Centralized LLM configuration management with `OptimizedOllama` class
- Memory optimization features for RTX 4060 constraints
- Automatic model selection based on agent type
- Memory cleanup and monitoring mechanisms
- Fallback response handling for LLM failures
- Global LLM manager with model caching and memory management
- Support for multiple agent types: critical, standard, coordinator
- Enhanced error handling and logging for LLM operations
- Comprehensive fallback response generator with `MockAgent` class
- Contextual response selection logic for all agent types (HVAC, Power, Security, Network, Coordinator)
- Structured fallback responses with confidence scoring and reasoning
- Performance metrics tracking for fallback response generation
- Convenience functions for easy fallback response integration
- **Comprehensive memory management system** with `MemoryOptimizer` class for RTX 4060 constraints (8GB limit, 7GB trigger)
- **LRU cache implementation** (`LRUModelCache`) for efficient model management with automatic eviction
- **Dynamic model loading/unloading** with context manager support and memory checks before loading
- **Memory monitoring and cleanup triggers** with background monitoring thread and automatic cleanup
- **Priority-based model management** with `MemoryPriority` enum (CRITICAL, HIGH, MEDIUM, LOW) for intelligent eviction
- **RTX 4060 optimized configuration** with max 2 concurrent models and 7GB memory threshold
- **Memory statistics and reporting** with comprehensive memory usage reports and GPU memory tracking
- **Emergency cleanup mechanisms** for critical memory situations with non-critical model removal
- **Thread-safe operations** with proper locking for concurrent model access and management
- **Comprehensive unit tests** for memory management system with 33 test cases covering all functionality
- **Production-ready CI/CD pipeline configuration**: Complete GitHub Actions workflow for demo readiness validation including Python testing with pytest (unit, integration, scenario tests), frontend testing with npm/vitest, memory management validation, performance benchmarking for all three scenarios, code quality checks (linting, type checking), security scanning and dependency checks, and comprehensive artifact generation and reporting
- **Pull request validation pipeline**: Fast feedback loop development pipeline with essential tests and quality checks that integrates seamlessly with the demo-ready pipeline for efficient code review and merge processes
- **CI/CD environment setup script**: Comprehensive environment configuration script with dependency installation, environment variable setup, testing tools configuration, validation tools setup, and monitoring tools integration for both local and CI environments
- **Demo-specific test execution script**: Automated scenario validation and performance testing script that runs comprehensive tests for all three demo scenarios (Cooling Crisis, Security Breach, Energy Optimization) with memory validation, performance benchmarking, and detailed reporting
- **Enhanced .gitignore patterns**: Added comprehensive CI/CD related ignore patterns for artifacts, build outputs, test results, coverage reports, security scan outputs, and temporary files to ensure clean repository management
- **Simple and lightweight Routine Maintenance demo scenario**: Added fourth demo scenario with HVAC-Network agent coordination, 60-second completion constraint, and 3-phase execution (detection, HVAC check, network check, completion) for lightweight demonstrations
- **Routine Maintenance scenario integration**: Integrated with existing scenario orchestrator from Task 13 with event bus integration, timing constraints, and success criteria evaluation for reliable demo execution
- **Comprehensive Routine Maintenance unit tests**: Added 30+ unit tests covering scenario initialization, step execution, agent coordination, timing constraints, performance metrics, and end-to-end scenario validation
- **Demo script updates**: Updated comprehensive 15-minute demo script to include fourth scenario with 1-minute timing allocation, technical talking points, and step-by-step execution instructions
- **spec(intellicenter-demo-readiness): task 20 — Enhance dashboard real-time visualization (FacilityLayout, AgentStatus, PerformancePanel)**: Implemented SVG-based facility layout with animated agent zones, real-time status animations with pulsing effects for active/warning/error states, and performance metrics panel showing messages per second, average latency, and recent events

### Changed
- Updated all agent imports to use centralized LLM configuration
- Replaced direct Ollama imports with `get_llm()` function calls
- Standardized model configurations across all agents
- Added memory usage tracking and reporting
- Improved error handling with graceful degradation

### Fixed
- **Demo test script parameter passing**: Fixed Security Breach scenario test script to properly pass string literals for location and severity parameters, resolving "name 'server_room_main' is not defined" error
- **Integration test async support**: Added pytest-asyncio plugin support to enable proper execution of async integration tests that were previously failing with "async def functions are not natively supported" errors
- **Scenario initialization issues**: Fixed scenario class initialization by ensuring proper event_bus and orchestrator parameters are passed to all scenario constructors
- **Memory validation reporting**: Enhanced memory validation test reporting to provide detailed memory usage statistics and validation results
- **Performance benchmark reporting**: Fixed performance benchmark reporting to include proper success rate calculations and response time metrics
- Import errors for `llm_manager` from `async_crew.py`
- Agent class name mismatches in test imports
- Missing imports in test infrastructure modules
- Power agent configuration to use centralized LLM management
- HVAC agent initialization with CrewAI integration
- Model specification at line 84 in HVAC agent
- Added error handling and fallback activation using MockAgent
- Fixed method signature for `_process_crew_result` to include loop parameter
- Updated HVAC agent tests to properly test initialization and response generation
- Power agent initialization with correct model specification at line 81
- Added error handling and fallback activation using MockAgent for power agent
- Implemented coordination logic with HVAC agent through event bus subscription
- Added performance metrics tracking and fallback decision generation
- Fixed event bus subscription to occur during initialization rather than runtime
- Added comprehensive helper methods for metrics, fallback decisions, and testing
- Security agent initialization with complete CrewAI integration and fallback mode
- Implemented comprehensive security tools: Camera Surveillance, Access Control, and Incident Response
- Added performance metrics tracking for security agent responses and decision quality
- Enhanced security event handling with proper async processing and error management
- Fixed security agent tests to work with actual CrewAI implementation and mock scenarios
- Added security agent configuration loading with proper fallback mechanisms
- Network agent initialization with complete CrewAI integration and fallback support
- Implemented comprehensive network monitoring tools: Traffic Analysis, Latency Check, Device Status, and Security Scan
- Added network performance metrics tracking and fallback decision generation with MockAgent integration
- Enhanced network event handling with proper async processing using asyncio.to_thread for crew execution
- Fixed network agent tests with comprehensive coverage including initialization, fallback modes, and tool functionality
- Coordinator agent initialization with complete multi-agent coordination logic and orchestration patterns
- Implemented priority-based decision making with PriorityScoringTool, ConflictResolutionTool, and ScenarioOrchestrationTool
- Added comprehensive facility coordination workflow with automatic analysis triggering when all subsystems report
- Enhanced coordinator agent with LLM integration using centralized get_llm("coordinator") and robust MockAgent fallback
- Integrated coordinator agent with event bus for multi-agent communication and conflict resolution
- Added performance metrics tracking, decision history, and coordination reporting capabilities
- Fixed coordinator agent configuration loading to support both optimized_tasks.yaml and tasks.yaml key formats
- Enhanced coordinator agent tests to validate initialization, configuration loading, and coordination functionality
- **WebSocket server real event bus integration**: Replaced simulation code with actual event bus integration for real-time agent status updates
- **WebSocket event handlers**: Implemented dedicated event handlers for HVAC, Power, Security, Network, and Coordinator agent events
- **WebSocket manual override integration**: Enhanced manual override functionality to publish events to the event bus instead of simulation
- **WebSocket error handling**: Added comprehensive error handling for event bus failures and connection issues
- **WebSocket server lifecycle management**: Added proper startup/shutdown procedures for event bus integration
- **Frontend WebSocket reconnection logic**: Implemented comprehensive WebSocket reconnection with heartbeat mechanism, exponential backoff, connection status tracking, and fallback to polling
- **WebSocket connection status indicator**: Added real-time connection status component with visual feedback for connected, reconnecting, disconnected, and fallback states including progress indicators and error messages
- **Memory manager integration with agent initialization**: Integrated MemoryOptimizer with AsyncCrewAI for memory checks before CrewAI initialization and automatic cleanup triggers
- **LLM configuration memory management**: Enhanced LLMManager with MemoryOptimizer integration for model loading constraints, max concurrent models (2 for RTX 4060), and cleanup triggers when memory exceeds 7GB
- **Agent initialization memory constraints**: Added memory validation before crew creation and model loading with automatic cleanup and error handling for insufficient memory conditions
- **Memory-aware model loading**: Implemented memory estimation for different model sizes and integrated can_load_model checks with the MemoryOptimizer before LLM instantiation
- **Enhanced memory reporting**: Updated memory reporting to include MemoryOptimizer statistics alongside LLM manager metrics for comprehensive memory visibility
- **Scenario orchestrator for demo scenarios**: Implemented comprehensive scenario orchestrator with event bus integration, state management, timing constraints, and reset functionality for three built-in demo scenarios (Cooling Crisis, Security Breach, Energy Optimization)
- **Scenario lifecycle management**: Added complete scenario state management (IDLE, INITIALIZING, RUNNING, PAUSED, COMPLETED, FAILED, RESETTING) with pause/resume/stop functionality
- **Event-driven scenario coordination**: Integrated scenario orchestrator with existing event bus for agent coordination, subscribing to agent decision events and publishing scenario lifecycle events
- **Scenario timing and completion tracking**: Implemented per-scenario and per-step timeout handling, agent response tracking, and success criteria evaluation with 80% response coverage heuristic
- **Comprehensive scenario orchestrator tests**: Added 25 unit tests covering initialization, execution, state management, reset functionality, pause/resume operations, event handling, and performance metrics
- **Cooling Crisis scenario implementation**: Implemented standalone cooling crisis scenario logic with 89.5°F (32°C) temperature threshold detection, HVAC-Power-Security coordination, and 2-minute completion constraint
- **Step-by-step crisis response execution**: Added 5-step crisis response workflow (HVAC emergency response, power coordination, security lockdown, multi-agent coordination, crisis resolution verification) with proper timing coordination
- **Temperature event monitoring and triggers**: Implemented temperature threshold monitoring with automatic crisis triggering when 89.5°F threshold is exceeded, including Fahrenheit/Celsius conversion utilities
- **Multi-agent coordination during crisis**: Enhanced agent coordination with event bus integration for HVAC cooling decisions, power optimization responses, security assessment decisions, and facility coordination directives
- **Crisis performance metrics and tracking**: Added comprehensive performance metrics tracking including crisis completion rates, response times, agent coordination success rates, and step-by-step execution monitoring
- **Cooling Crisis scenario integration**: Integrated cooling crisis scenario with existing scenario orchestrator for seamless demo execution and orchestrator event handling
- **Comprehensive Cooling Crisis unit tests**: Added 20+ unit tests covering temperature threshold detection, crisis event creation, step execution timing, agent response handling, performance metrics, and end-to-end scenario execution
- **Security Breach scenario implementation**: Implemented comprehensive security breach scenario logic with unauthorized access triggers, Security-Network-Coordinator multi-agent coordination, and 90-second completion constraint
- **Step-by-step breach response execution**: Added 5-step breach response workflow (security assessment, network analysis, lockdown initiation, coordination response, containment verification) with proper timing coordination and security action execution
- **Unauthorized access monitoring and triggers**: Implemented suspicious access attempt detection with threshold-based breach triggering, access attempt tracking, and severity escalation from medium to critical levels
- **Multi-layered security response coordination**: Enhanced agent coordination with event bus integration for security assessment decisions, network assessment responses, facility coordination directives, and scenario orchestration
- **Security action execution and tracking**: Implemented comprehensive security actions including camera surveillance, access control, network isolation, door lockdown, access revocation, emergency protocol activation, resource allocation, containment verification, system integrity checks, and threat elimination
- **Breach performance metrics and tracking**: Added comprehensive performance metrics tracking including breach resolution rates, response times, agent coordination success rates, security actions taken, lockdown initiations, and network isolations
- **Security Breach scenario integration**: Integrated security breach scenario with existing scenario orchestrator for seamless demo execution and orchestrator event handling with test breach trigger functionality
- **90-second timing constraint enforcement**: Implemented strict 90-second completion window with step-by-step timing coordination, deadline monitoring, and automatic failure handling for timeout scenarios

## [0.1.0] - 2025-08-21

### Added
- Initial project structure and core components
- Multi-agent facility management system
- Event-driven architecture with EventBus
- AsyncCrewAI wrapper for CrewAI integration
- Basic agent implementations for HVAC, Security, Network, and Power
- Test infrastructure for validation and compliance
- Configuration management system
- WebSocket server for real-time communication