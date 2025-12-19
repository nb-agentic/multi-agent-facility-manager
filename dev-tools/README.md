# Dev Tools (scripts and assets)

This directory contains helper scripts, utilities, and pre-recorded response JSONs used for demos and development. It is separate from the Python package re-export named dev_tools (underscore).

- Scripts live here under dev-tools/ (hyphen)
- Importable helpers are exposed via the Python package dev_tools/ (underscore), e.g., [dev_tools/demo_fallback.py](../dev_tools/demo_fallback.py:1)

## Contents

- Integrated demo runner script: [dev-tools/integrated_demo.py](integrated_demo.py:1)
- Fallback demo direct runner: [dev-tools/demo_fallback.py](demo_fallback.py:1)
- Pre-recorded responses: [dev-tools/responses](responses/cooling_crisis.json:1)
  - cooling_crisis.json
  - security_breach.json
  - energy_optimization.json
  - routine_maintenance.json
- Additional utilities: test clients, monitors, and preparation scripts

## How to use

1) Start the WebSocket server (port 8000)
```bash
python -m intellicenter.api.websocket_server
```
Server entry point: [intellicenter/api/websocket_server.py](../intellicenter/api/websocket_server.py:1)

2) Start the frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 (WebSocket target: ws://localhost:8000/ws), hook at [frontend/src/hooks/useWebSocket.ts](../frontend/src/hooks/useWebSocket.ts:1)

3) Run an integrated showcase
```bash
python dev-tools/integrated_demo.py --scenario cooling_crisis --speed 0.5
```
Script: [dev-tools/integrated_demo.py](integrated_demo.py:1)

4) Run fallback demo directly (deterministic)
```bash
python dev-tools/demo_fallback.py --scenario cooling_crisis --ws-port 8000 --speed 0.5
```
Script: [dev-tools/demo_fallback.py](demo_fallback.py:1), responses from [dev-tools/responses](responses/cooling_crisis.json:1)

5) Single-command launcher (preferred)
```bash
python [run_demo.py](../run_demo.py:1) --mode fallback --scenario cooling_crisis --ws-port 8000 --speed 0.5 --timeout-s 12
```
Live example:
```bash
python [run_demo.py](../run_demo.py:1) --mode live --scenario routine_maintenance --ws-port 8000 --timeout-s 30
```
Report path:
- Default via [get_default_report_path()](../run_demo.py:297) → ./demo-results/report_YYYYmmdd_HHMMSS.json
- Override with --report ./demo-results/my_report.json

## Import path guidance

- Do not import from dev-tools (hyphen) in Python
- Use the Python package re-export:
  - from [dev_tools.demo_fallback](../dev_tools/demo_fallback.py:1) import FallbackDemoRunner

## Notes

- Ensure you run these scripts from the repository root so the dev_tools package is on the Python path
- For troubleshooting connectivity (UI Disconnected), see [docs/troubleshooting.md](../docs/troubleshooting.md:1)