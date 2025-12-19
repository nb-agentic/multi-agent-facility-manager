#!/usr/bin/env python3
"""
Manual Agent Testing and Monitoring Tool
Allows you to trigger agents manually and see their logs in real-time.
"""
import asyncio
import json
import time
from datetime import datetime
from intellicenter.core.event_bus import EventBus
from intellicenter.agents.hvac_agent import HVACControlAgent
from intellicenter.agents.power_agent import PowerAgent
from intellicenter.agents.security_agent import SecurityAgent
from intellicenter.agents.network_agent import NetworkAgent
from intellicenter.agents.coordinator_agent import CoordinatorAgent

class AgentTester:
    def __init__(self):
        self.event_bus = EventBus()
        self.agents = {}
        self.event_log = []
        
    async def setup(self):
        """Initialize event bus and agents"""
        print("🚀 Setting up Agent Testing Environment...")
        await self.event_bus.start()
        
        # Initialize agents
        self.agents = {
            'hvac': HVACControlAgent(self.event_bus),
            'power': PowerAgent(self.event_bus),
            'security': SecurityAgent(self.event_bus),
            'network': NetworkAgent(self.event_bus),
            'coordinator': CoordinatorAgent(self.event_bus)
        }
        
        # Subscribe to all agent responses for monitoring
        self.event_bus.subscribe("hvac.cooling.decision", self._log_event)
        self.event_bus.subscribe("power.optimization.decision", self._log_event)
        self.event_bus.subscribe("security.assessment.decision", self._log_event)
        self.event_bus.subscribe("network.assessment.decision", self._log_event)
        self.event_bus.subscribe("facility.coordination.directive", self._log_event)
        
        # Start all agents
        for name, agent in self.agents.items():
            asyncio.create_task(agent.run())
            print(f"✅ {name.upper()} Agent started")
            
        print("🎯 All agents ready for testing!\n")
    
    def _log_event(self, message):
        """Log all events for monitoring"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        try:
            data = json.loads(message)
            event_type = "Unknown"
            if "cooling" in message:
                event_type = "HVAC Decision"
            elif "power" in message:
                event_type = "Power Decision"
            elif "security" in message:
                event_type = "Security Decision"
            elif "network" in message:
                event_type = "Network Decision"
            elif "coordination" in message:
                event_type = "Coordinator Decision"
                
            self.event_log.append({
                'timestamp': timestamp,
                'type': event_type,
                'data': data
            })
            
            print(f"📨 [{timestamp}] {event_type}: {data.get('status', 'N/A')}")
            if 'error' in data:
                print(f"   ❌ Error: {data['error']}")
            
        except Exception as e:
            print(f"📨 [{timestamp}] Raw Event: {message[:100]}...")
    
    async def trigger_hvac_test(self, temperature=85.5):
        """Trigger HVAC agent with temperature data"""
        print(f"\n🌡️  TRIGGERING HVAC AGENT (Temperature: {temperature}°F)")
        print("=" * 60)
        
        temp_event = {
            "facility_id": "datacenter-01",
            "sensor_id": "temp-sensor-manual-test",
            "timestamp": time.time(),
            "temperature": temperature,
            "zone": "server_room_a"
        }
        
        await self.event_bus.publish("hvac.temperature.changed", json.dumps(temp_event))
        print(f"📤 Published temperature event: {temperature}°F")
        
        # Wait for response
        await asyncio.sleep(3)
        return self._get_recent_events("HVAC Decision")
    
    async def trigger_power_test(self, cooling_level="high"):
        """Trigger Power agent with cooling decision"""
        print(f"\n⚡ TRIGGERING POWER AGENT (Cooling Level: {cooling_level})")
        print("=" * 60)
        
        cooling_decision = {
            "cooling_level": cooling_level,
            "timestamp": time.time(),
            "agent_type": "hvac_specialist",
            "zone": "server_room_a"
        }
        
        await self.event_bus.publish("hvac.cooling.decision", json.dumps(cooling_decision))
        print(f"📤 Published cooling decision: {cooling_level}")
        
        # Wait for response
        await asyncio.sleep(3)
        return self._get_recent_events("Power Decision")
    
    async def trigger_security_test(self, event_type="access_attempt"):
        """Trigger Security agent with security event"""
        print(f"\n🛡️  TRIGGERING SECURITY AGENT (Event: {event_type})")
        print("=" * 60)
        
        security_event = {
            "event_id": f"sec-{int(time.time())}",
            "event_type": event_type,
            "timestamp": time.time(),
            "location": "server_room_entrance",
            "severity": "medium"
        }
        
        await self.event_bus.publish("facility.security.event", json.dumps(security_event))
        print(f"📤 Published security event: {event_type}")
        
        # Wait for response
        await asyncio.sleep(3)
        return self._get_recent_events("Security Decision")
    
    async def trigger_network_test(self, network_data=None):
        """Trigger Network agent with network assessment"""
        print(f"\n🌐 TRIGGERING NETWORK AGENT")
        print("=" * 60)
        
        if network_data is None:
            network_data = {
                "bandwidth_usage": 75.5,
                "latency": 12.3,
                "packet_loss": 0.1,
                "timestamp": time.time()
            }
        
        await self.event_bus.publish("facility.network.assessment", json.dumps(network_data))
        print(f"📤 Published network assessment: {network_data}")
        
        # Wait for response
        await asyncio.sleep(3)
        return self._get_recent_events("Network Decision")
    
    async def trigger_coordinator_test(self):
        """Trigger Coordinator agent with facility status"""
        print(f"\n📜 TRIGGERING COORDINATOR AGENT")
        print("=" * 60)
        
        facility_status = {
            "facility_id": "datacenter-01",
            "overall_status": "operational",
            "active_alerts": 2,
            "timestamp": time.time(),
            "systems": {
                "hvac": "active",
                "power": "optimal",
                "security": "monitoring",
                "network": "stable"
            }
        }
        
        await self.event_bus.publish("facility.status.update", json.dumps(facility_status))
        print(f"📤 Published facility status update")
        
        # Wait for response
        await asyncio.sleep(3)
        return self._get_recent_events("Coordinator Decision")
    
    def _get_recent_events(self, event_type, limit=5):
        """Get recent events of a specific type"""
        recent = [e for e in self.event_log if e['type'] == event_type][-limit:]
        return recent
    
    def show_event_log(self, limit=10):
        """Display recent event log"""
        print(f"\n📋 RECENT EVENT LOG (Last {limit} events)")
        print("=" * 80)
        
        recent_events = self.event_log[-limit:] if self.event_log else []
        
        if not recent_events:
            print("   No events recorded yet.")
            return
            
        for event in recent_events:
            print(f"[{event['timestamp']}] {event['type']}")
            if 'error' in event['data']:
                print(f"   ❌ Error: {event['data']['error']}")
            elif event['data'].get('status') == 'success':
                print(f"   ✅ Success")
            elif event['data'].get('fallback'):
                print(f"   ⚠️  Fallback response")
            else:
                print(f"   ℹ️  Status: {event['data'].get('status', 'Unknown')}")
    
    async def run_full_scenario(self):
        """Run a complete multi-agent scenario"""
        print(f"\n🎬 RUNNING FULL MULTI-AGENT SCENARIO")
        print("=" * 80)
        
        # 1. High temperature triggers HVAC
        print("\n1️⃣  High temperature detected...")
        await self.trigger_hvac_test(temperature=88.0)
        
        await asyncio.sleep(2)
        
        # 2. HVAC decision triggers Power optimization
        print("\n2️⃣  Power optimization needed...")
        await self.trigger_power_test(cooling_level="high")
        
        await asyncio.sleep(2)
        
        # 3. Security monitoring during high activity
        print("\n3️⃣  Security monitoring activated...")
        await self.trigger_security_test(event_type="high_activity")
        
        await asyncio.sleep(2)
        
        # 4. Network assessment for increased load
        print("\n4️⃣  Network assessment for increased load...")
        await self.trigger_network_test({
            "bandwidth_usage": 85.0,
            "latency": 15.2,
            "packet_loss": 0.2,
            "timestamp": time.time()
        })
        
        await asyncio.sleep(2)
        
        # 5. Coordinator oversight
        print("\n5️⃣  Coordinator oversight...")
        await self.trigger_coordinator_test()
        
        await asyncio.sleep(3)
        
        print(f"\n🏁 SCENARIO COMPLETE!")
        self.show_event_log(limit=15)

async def interactive_menu():
    """Interactive menu for manual agent testing"""
    tester = AgentTester()
    await tester.setup()
    
    while True:
        print(f"\n" + "="*60)
        print("🎮 INTELLICENTER AGENT TESTING MENU")
        print("="*60)
        print("1. Trigger HVAC Agent (Temperature Event)")
        print("2. Trigger Power Agent (Cooling Decision)")
        print("3. Trigger Security Agent (Security Event)")
        print("4. Trigger Network Agent (Network Assessment)")
        print("5. Trigger Coordinator Agent (Facility Status)")
        print("6. Run Full Multi-Agent Scenario")
        print("7. Show Event Log")
        print("8. Clear Event Log")
        print("9. Exit")
        print("-" * 60)
        
        try:
            choice = input("Select option (1-9): ").strip()
            
            if choice == '1':
                temp = input("Enter temperature (default 85.5): ").strip()
                temp = float(temp) if temp else 85.5
                await tester.trigger_hvac_test(temp)
                
            elif choice == '2':
                level = input("Enter cooling level (low/medium/high, default high): ").strip()
                level = level if level in ['low', 'medium', 'high'] else 'high'
                await tester.trigger_power_test(level)
                
            elif choice == '3':
                event = input("Enter event type (default access_attempt): ").strip()
                event = event if event else 'access_attempt'
                await tester.trigger_security_test(event)
                
            elif choice == '4':
                await tester.trigger_network_test()
                
            elif choice == '5':
                await tester.trigger_coordinator_test()
                
            elif choice == '6':
                await tester.run_full_scenario()
                
            elif choice == '7':
                limit = input("Number of events to show (default 10): ").strip()
                limit = int(limit) if limit.isdigit() else 10
                tester.show_event_log(limit)
                
            elif choice == '8':
                tester.event_log.clear()
                print("✅ Event log cleared")
                
            elif choice == '9':
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please select 1-9.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting IntelliCenter Agent Testing Tool...")
    asyncio.run(interactive_menu())