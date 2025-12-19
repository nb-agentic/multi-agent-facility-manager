#!/usr/bin/env python3
"""
Simple WebSocket client test to verify the connection works.
"""
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Send a ping message
            ping_message = {"type": "ping"}
            await websocket.send(json.dumps(ping_message))
            print("📤 Sent ping message")
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            print(f"📥 Received: {response}")
            
            # Wait for agent status updates
            print("🔄 Waiting for agent status updates...")
            for i in range(3):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)
                    print(f"📨 Message {i+1}: {data.get('type', 'unknown')} - {data}")
                except asyncio.TimeoutError:
                    print(f"⏰ Timeout waiting for message {i+1}")
                    
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())