import asyncio
import websockets
import json
import time

async def trigger_event(websocket, event_type, details):
    print(f"--- Triggering '{event_type}' incident ---")
    await websocket.send(json.dumps({
        "event": "trigger_incident",
        "payload": {
            "incident_type": event_type,
            "details": details
        }
    }))
    response = await websocket.recv()
    print(f"Server response: {response}\n")
    await asyncio.sleep(2) # Wait for 2 seconds before the next event

async def interact():
    uri = "ws://127.0.0.1:8000/ws"
    async with websockets.connect(uri) as websocket:
        print("--- Starting Full Agent Demo ---")

        # 1. Trigger a power outage event
        await trigger_event(websocket, "power_outage", "Main power grid failure in Sector A.")

        # 2. Trigger an unauthorized access event
        await trigger_event(websocket, "unauthorized_access", "Unauthorized access detected at entrance 3.")

        # 3. Trigger a network failure event
        await trigger_event(websocket, "network_failure", "Core network switch unresponsive.")

        print("--- Full Agent Demo Complete ---")


if __name__ == "__main__":
    asyncio.run(interact())