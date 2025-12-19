import os
os.environ['OTEL_SDK_DISABLED'] = 'true'
import asyncio
from intellicenter.core.event_bus import EventBus
from intellicenter.simulation.facility_simulator import FacilitySimulator
from intellicenter.agents.hvac_agent import HVACControlAgent

async def main():
    """
    Main function to run the facility simulator and HVAC control agent.
    """
    print("Starting services...")

    # Instantiate the services
    event_bus = EventBus()
    await event_bus.start()  # Start the event bus
    simulator = FacilitySimulator(event_bus)
    agent = HVACControlAgent(event_bus)

    # Start the services concurrently
    simulator_task = asyncio.create_task(simulator.run())
    agent_task = asyncio.create_task(agent.run())

    print("FacilitySimulator and HVACControlAgent are running.")

    # Wait for both tasks to complete
    await asyncio.gather(simulator_task, agent_task)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Services stopped.")