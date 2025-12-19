import asyncio
import json
import random
import time
from uuid import uuid4

from intellicenter.shared.event_bus import EventBus


class FacilitySimulator:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.is_running = False

    async def run(self):
        self.is_running = True
        while self.is_running:
            temperature = round(random.uniform(18.0, 26.0), 2)
            payload = {
                "sensor_id": f"temp-sensor-{uuid4()}",
                "timestamp": time.time(),
                "temperature": temperature,
            }
            await self.event_bus.publish("hvac.temperature.changed", json.dumps(payload))
            await asyncio.sleep(0.1)

    def stop(self):
        self.is_running = False