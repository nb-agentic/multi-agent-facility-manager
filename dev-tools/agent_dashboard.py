#!/usr/bin/env python3
"""
IntelliCenter Agent Dashboard
Real-time agent monitoring and manual triggering interface.
"""
import asyncio
import json
import time
import psutil
from datetime import datetime
from intellicenter.core.event_bus import EventBus
from intellicenter.core.async_crew import llm_manager


class AgentDashboard:
    def __init__(self):
        self.event_bus = EventBus()
        self.agent_stats = {
            'hvac': {'responses': 0, 'avg_time': 0, 'last_response': None, 'status': 'idle'},
            'power': {'responses': 0, 'avg_time': 0, 'last_response': None, 'status': 'idle'},
            'security': {'responses': 0, 'avg_time': 0, 'last_response': None, 'status': 'idle'},
            'network': {'responses': 0, 'avg_time': 0, 'last_response': None, 'status': 'idle'},
            'coordinator': {'responses': 0, 'avg_time': 0, 'last_response': None, 'status': 'idle'}
        }
        self.event_log = []
        self.start_time = time.time()
        
    async def setup(self):
        """Initialize dashboard"""
        print("🚀 Starting IntelliCenter Agent Dashboard...")
        await self.event_bus.start()
        
        # Subscribe to all agent events
        self.event_bus.subscribe("hvac.cooling.decision", self._log_hvac_response)
        self.event_bus.subscribe("power.optimization.decision", self._log_power_response)
        self.event_bus.subscribe("security.assessment.decision", self._log_security_response)
        self.event_bus.subscribe("network.assessment.decision", self._log_network_response)
        self.event_bus.subscribe("facility.coordination.directive", self._log_coordinator_response)
        
        print("✅ Dashboard monitoring all agent channels")
        
    def _log_response(self, agent_type: str, message: str):
        """Log agent response and update stats"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        try:
            data = json.loads(message)
            
            # Update stats
            self.agent_stats[agent_type]['responses'] += 1
            self.agent_stats[agent_type]['last_response'] = timestamp
            
            if 'execution_time' in data:
                current_avg = self.agent_stats[agent_type]['avg_time']
                new_time = data['execution_time']
                count = self.agent_stats[agent_type]['responses']
                self.agent_stats[agent_type]['avg_time'] = ((current_avg * (count - 1)) + new_time) / count
            
            # Determine status
            if data.get('error'):
                self.agent_stats[agent_type]['status'] = 'error'
                status_icon = "❌"
            elif data.get('fallback'):
                self.agent_stats[agent_type]['status'] = 'fallback'
                status_icon = "⚠️"
            else:
                self.agent_stats[agent_type]['status'] = 'success'
                status_icon = "✅"
            
            # Log event
            log_entry = {
                'timestamp': timestamp,
                'agent': agent_type.upper(),
                'status': self.agent_stats[agent_type]['status'],
                'data': data
            }
            self.event_log.append(log_entry)
            
            # Keep only last 50 events
            if len(self.event_log) > 50:
                self.event_log = self.event_log[-50:]
            
            # Print real-time update
            print(f"{status_icon} [{timestamp}] {agent_type.upper()}: {self.agent_stats[agent_type]['status']}")
            
        except Exception as e:
            print(f"❌ [{timestamp}] Error parsing {agent_type} response: {e}")
    
    def _log_hvac_response(self, message):
        self._log_response('hvac', message)
    
    def _log_power_response(self, message):
        self._log_response('power', message)
    
    def _log_security_response(self, message):
        self._log_response('security', message)
    
    def _log_network_response(self, message):
        self._log_response('network', message)
    
    def _log_coordinator_response(self, message):
        self._log_response('coordinator', message)
    
    async def trigger_hvac_event(self, temperature: float = 85.0):
        """Trigger HVAC agent with temperature event"""
        print(f"\n🌡️  TRIGGERING HVAC: Temperature {temperature}°F")
        
        event_data = {
            "facility_id": "datacenter-01",
            "sensor_id": f"temp-{int(time.time())}",
            "timestamp": time.time(),
            "temperature": temperature,
            "zone": "server_room_main"
        }
        
        await self.event_bus.publish("hvac.temperature.changed", json.dumps(event_data))
        print(f"📤 Published temperature event")
    
    async def trigger_power_event(self, cooling_level: str = "high"):
        """Trigger Power agent with cooling decision"""
        print(f"\n⚡ TRIGGERING POWER: Cooling level {cooling_level}")
        
        event_data = {
            "cooling_level": cooling_level,
            "timestamp": time.time(),
            "agent_type": "hvac_specialist",
            "zone": "server_room_main",
            "energy_impact": "high" if cooling_level == "high" else "medium"
        }
        
        await self.event_bus.publish("hvac.cooling.decision", json.dumps(event_data))
        print(f"📤 Published cooling decision")
    
    async def trigger_security_event(self, event_type: str = "access_attempt"):
        """Trigger Security agent with security event"""
        print(f"\n🛡️  TRIGGERING SECURITY: {event_type}")
        
        event_data = {
            "event_id": f"sec-{int(time.time())}",
            "event_type": event_type,
            "timestamp": time.time(),
            "location": "server_room_entrance",
            "severity": "medium",
            "user_id": "unknown"
        }
        
        await self.event_bus.publish("facility.security.event", json.dumps(event_data))
        print(f"📤 Published security event")
    
    async def trigger_network_event(self, bandwidth: float = 75.0):
        """Trigger Network agent with network metrics"""
        print(f"\n🌐 TRIGGERING NETWORK: Bandwidth {bandwidth}%")
        
        event_data = {
            "bandwidth_usage": bandwidth,
            "latency": 12.5,
            "packet_loss": 0.1,
            "timestamp": time.time(),
            "interface": "eth0"
        }
        
        await self.event_bus.publish("facility.network.assessment", json.dumps(event_data))
        print(f"📤 Published network assessment")
    
    async def trigger_coordinator_event(self):
        """Trigger Coordinator agent with facility status"""
        print(f"\n📜 TRIGGERING COORDINATOR: Facility status update")
        
        event_data = {
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
        
        await self.event_bus.publish("facility.status.update", json.dumps(event_data))
        print(f"📤 Published facility status")
    
    def show_dashboard(self):
        """Display current dashboard status"""
        uptime = time.time() - self.start_time
        memory = psutil.virtual_memory()
        
        print(f"\n" + "="*80)
        print(f"🎛️  INTELLICENTER AGENT DASHBOARD")
        print("="*80)
        print(f"⏱️  Uptime: {uptime:.1f}s | 💾 Memory: {memory.percent:.1f}% | 📊 Events: {len(self.event_log)}")
        print(f"🧠 {llm_manager.get_memory_report()}")
        print("-"*80)
        
        # Agent status table
        print(f"{'AGENT':<12} {'STATUS':<10} {'RESPONSES':<10} {'AVG TIME':<10} {'LAST SEEN':<10}")
        print("-"*80)
        
        for agent, stats in self.agent_stats.items():
            status_icon = {
                'idle': '⏸️',
                'success': '✅',
                'error': '❌', 
                'fallback': '⚠️'
            }.get(stats['status'], '❓')
            
            print(f"{agent.upper():<12} {status_icon} {stats['status']:<8} {stats['responses']:<10} "
                  f"{stats['avg_time']:<10.2f} {stats['last_response'] or 'Never':<10}")
        
        print("="*80)
    
    def show_recent_events(self, limit: int = 10):
        """Show recent events"""
        print(f"\n📋 RECENT EVENTS (Last {limit})")
        print("-"*60)
        
        recent = self.event_log[-limit:] if self.event_log else []
        
        if not recent:
            print("   No events recorded yet")
            return
        
        for event in recent:
            status_icon = {
                'success': '✅',
                'error': '❌',
                'fallback': '⚠️'
            }.get(event['status'], '❓')
            
            print(f"[{event['timestamp']}] {status_icon} {event['agent']}: {event['status']}")
            
            if event['data'].get('error'):
                print(f"   Error: {event['data']['error']}")
            elif 'execution_time' in event['data']:
                print(f"   Execution: {event['data']['execution_time']:.2f}s")

async def interactive_dashboard():
    """Interactive dashboard interface"""
    dashboard = AgentDashboard()
    await dashboard.setup()
    
    print(f"\n🎮 INTERACTIVE AGENT DASHBOARD")
    print("Commands:")
    print("  1. hvac [temp] - Trigger HVAC (default: 85°F)")
    print("  2. power [level] - Trigger Power (low/medium/high)")
    print("  3. security [event] - Trigger Security")
    print("  4. network [bandwidth] - Trigger Network")
    print("  5. coordinator - Trigger Coordinator")
    print("  6. status - Show dashboard status")
    print("  7. events [count] - Show recent events")
    print("  8. scenario - Run full scenario")
    print("  9. clear - Clear event log")
    print("  0. quit - Exit dashboard")
    
    while True:
        try:
            print(f"\n" + "-"*40)
            command = input("Dashboard> ").strip().lower().split()
            
            if not command:
                continue
                
            cmd = command[0]
            
            if cmd == "quit" or cmd == "0":
                print("👋 Goodbye!")
                break
                
            elif cmd == "hvac" or cmd == "1":
                temp = float(command[1]) if len(command) > 1 else 85.0
                await dashboard.trigger_hvac_event(temp)
                await asyncio.sleep(2)
                
            elif cmd == "power" or cmd == "2":
                level = command[1] if len(command) > 1 and command[1] in ['low', 'medium', 'high'] else 'high'
                await dashboard.trigger_power_event(level)
                await asyncio.sleep(2)
                
            elif cmd == "security" or cmd == "3":
                event_type = command[1] if len(command) > 1 else 'access_attempt'
                await dashboard.trigger_security_event(event_type)
                await asyncio.sleep(2)
                
            elif cmd == "network" or cmd == "4":
                bandwidth = float(command[1]) if len(command) > 1 else 75.0
                await dashboard.trigger_network_event(bandwidth)
                await asyncio.sleep(2)
                
            elif cmd == "coordinator" or cmd == "5":
                await dashboard.trigger_coordinator_event()
                await asyncio.sleep(2)
                
            elif cmd == "status" or cmd == "6":
                dashboard.show_dashboard()
                
            elif cmd == "events" or cmd == "7":
                limit = int(command[1]) if len(command) > 1 else 10
                dashboard.show_recent_events(limit)
                
            elif cmd == "scenario" or cmd == "8":
                print("\n🎬 Running full multi-agent scenario...")
                await dashboard.trigger_hvac_event(88.0)
                await asyncio.sleep(3)
                await dashboard.trigger_power_event("high")
                await asyncio.sleep(3)
                await dashboard.trigger_security_event("high_activity")
                await asyncio.sleep(3)
                await dashboard.trigger_network_event(85.0)
                await asyncio.sleep(3)
                await dashboard.trigger_coordinator_event()
                await asyncio.sleep(3)
                print("🏁 Scenario complete!")
                
            elif cmd == "clear" or cmd == "9":
                dashboard.event_log.clear()
                print("✅ Event log cleared")
                
            else:
                print("❓ Unknown command. Type 'quit' to exit.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting IntelliCenter Agent Dashboard...")
    asyncio.run(interactive_dashboard())