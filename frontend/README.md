# IntelliCenter Frontend (React + TypeScript + Vite)

Real-time dashboard for IntelliCenter. Connects to the backend WebSocket server to visualize agent status, coordination directives, and event logs.

## Development

1) Install dependencies
```bash
cd frontend
npm install
```

2) Run the dev server
```bash
npm run dev
```

3) Open the dashboard
- http://localhost:5173

## WebSocket configuration

- Default target: ws://localhost:8000/ws
- Connection logic and reconnection/backoff live in [frontend/src/hooks/useWebSocket.ts](frontend/src/hooks/useWebSocket.ts:1)

If the backend port or host changes, update the target URL where the hook is called or adjust the hook implementation (or use environment configuration if your setup supports it). For local development, ensure the backend WebSocket server is running:
```bash
python -m intellicenter.api.websocket_server
# Health probe:
curl http://localhost:8000/health
```
Backend entry point: [intellicenter/api/websocket_server.py](../intellicenter/api/websocket_server.py:1)

## Troubleshooting

- UI shows Disconnected:
  - Confirm the WebSocket server is running on port 8000
  - Verify the hook target is ws://localhost:8000/ws in [frontend/src/hooks/useWebSocket.ts](frontend/src/hooks/useWebSocket.ts:1)
  - See the full guide: [docs/troubleshooting.md](../docs/troubleshooting.md:1)

## Scripts

- Start: `npm run dev`
- Build: `npm run build`
- Lint: `npm run lint`
- Test: `npm test` (if configured)
