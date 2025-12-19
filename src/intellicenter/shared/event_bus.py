import asyncio
from collections import defaultdict
import json

class EventBus:
    def __init__(self):
        self.subscribers = defaultdict(list)
        self.message_queue = asyncio.Queue()
        self.is_running = False
        self.worker_task = None

    async def start(self):
        if not self.is_running:
            self.is_running = True
            self.worker_task = asyncio.create_task(self._process_queue())

    def subscribe(self, event_type, callback):
        self.subscribers[event_type].append(callback)

    async def publish(self, event_type, message):
        await self.message_queue.put((event_type, message))

    async def _process_queue(self):
        while self.is_running:
            try:
                event_type, message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                if event_type in self.subscribers:
                    for callback in self.subscribers[event_type]:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(message)
                        else:
                            callback(message)
            except asyncio.TimeoutError:
                continue

    async def stop(self):
        self.is_running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass