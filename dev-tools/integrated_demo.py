#!/usr/bin/env python3
"""
Integrated Demo with Real Agent Responses
Starts actual agents and demonstrates real AI responses.
"""
import asyncio
import json
import time
import psutil
from datetime import datetime
from intellicenter.core.event_bus import EventBus
from intellicenter.core.async_crew import llm_manager
from intellicenter.agents.hvac_agent import HVACControlAgent


class IntegratedDemo:
    def __init__(self):
        self.event_bus = EventBus()
        self.agents = {}
        self.agent_responses = {}
        self.demo_active = False
        
    async def setup(self):
        """Initialize demo with real agents"""
        print("🚀 Starting Integrated IntelliCenter Demo...")
        print("🔧 Initializing event bus and agents...")
        
        await self.event_bus.start()
        
        # Initialize HVAC agent (the one that's working)
        print("   🌡️  Starting HVAC Agent...")
        try:
            self.agents['hvac'] = HVACControlAgent(self.event_bus)
            # Start HVAC agent in background
            asyncio.create_task(self.agents['hvac'].run())
            print("   ✅ HVAC Agent started successfully")
        except Exception as e:
            print(f"   ❌ HVAC Agent failed to start: {e}")
        
        # Subscribe to responses
        self.event_bus.subscribe("hvac.cooling.decision", self._capture_hvac_response)
        
        # For other agents, we'll simulate responses since they have CrewAI issues
        print("   ⚠️  Other agents will use simulated responses (CrewAI integration pending)")
        
        print("✅ Demo environment ready!")
        
    def _capture_hvac_response(self, message):
        """Capture HVAC agent response"""
        try:
            data = json.loads(message)
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            self.agent_responses['HVAC'] = {
                'timestamp': timestamp,
                'data': data,
                'status': 'success' if not data.get('error') else 'error'
            }
            
            print(f"✅ HVAC Agent responded at {timestamp}")
            if 'cooling_level' in data:
                print(f"   Decision: {data['cooling_level']} cooling level")
            if 'execution_time' in data:
                print(f"   Response time: {data['execution_time']:.2f}s")
                
        except Exception as e:
            print(f"❌ Error capturing HVAC response: {e}")
    
    async def simulate_other_agents(self, agent_type: str, scenario: str):
        """Simulate responses from other agents while CrewAI issues are resolved"""
        await asyncio.sleep(2)  # Simulate processing time
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        responses = {
            'power': {
                'power_optimization': f'Optimized power distribution for {scenario} scenario',
                'efficiency_rating': 0.87,
                'cost_savings': '$245/hour',
                'execution_time': 1.8,
                'status': 'success'
            },
            'security': {
                'security_assessment': f'Threat level assessed for {scenario}',
                'recommended_actions': ['Monitor access points', 'Increase surveillance'],
                'escalation_level': 'medium',
                'execution_time': 1.2,
                'status': 'success'
            },
            'network': {
                'network_assessment': f'Network optimized for {scenario} conditions',
                'bandwidth_optimization': '15% improvement',
                'latency_reduction': '8ms',
                'execution_time': 2.1,
                'status': 'success'
            },
            'coordinator': {
                'directive': f'Coordinated response for {scenario} implemented',
                'system_priorities': ['HVAC', 'Power', 'Security'],
                'emergency_status': 'managed',
                'execution_time': 1.5,
                'status': 'success'
            }
        }
        
        if agent_type in responses:
            self.agent_responses[agent_type.upper()] = {
                'timestamp': timestamp,
                'data': responses[agent_type],
                'status': 'success'
            }
            print(f"✅ {agent_type.upper()} Agent responded at {timestamp} (simulated)")
    
    async def run_cooling_crisis_demo(self):
        """Run cooling crisis scenario with real HVAC agent"""
        print("\n🎬 COOLING CRISIS RESPONSE DEMO")
        print("="*60)
        print("📋 Scenario: Server room temperature spike to 89.5°F")
        print("🎯 Expected: Multi-agent coordinated response")
        
        self.agent_responses.clear()
        start_time = time.time()
        
        # Step 1: Trigger real HVAC agent
        print("\n🔄 Step 1: Temperature spike detected (89.5°F)")
        temp_event = {
            "facility_id": "datacenter-alpha",
            "sensor_id": "temp-rack-07",
            "timestamp": time.time(),
            "temperature": 89.5,
            "zone": "server_room_alpha",
            "alert_level": "critical"
        }
        
        await self.event_bus.publish("hvac.temperature.changed", json.dumps(temp_event))
        print("📤 Published temperature event to HVAC Agent")
        
        # Wait for HVAC response
        print("⏳ Waiting for HVAC Agent response...")
        await asyncio.sleep(5)
        
        # Step 2-5: Simulate other agent responses
        print("\n🔄 Step 2: Power optimization triggered")
        await self.simulate_other_agents('power', 'cooling_crisis')
        
        print("\n🔄 Step 3: Security lockdown protocol")
        await self.simulate_other_agents('security', 'cooling_crisis')
        
        print("\n🔄 Step 4: Network traffic rerouting")
        await self.simulate_other_agents('network', 'cooling_crisis')
        
        print("\n🔄 Step 5: Facility coordination")
        await self.simulate_other_agents('coordinator', 'cooling_crisis')
        
        total_time = time.time() - start_time
        
        print(f"\n🏁 COOLING CRISIS DEMO COMPLETE")
        print(f"   Total time: {total_time:.1f} seconds")
        print(f"   Agents responded: {len(self.agent_responses)}/5")
        
        return len(self.agent_responses)
    
    async def test_hvac_agent_directly(self):
        """Test HVAC agent with different temperature scenarios"""
        print("\n🧪 HVAC AGENT DIRECT TESTING")
        print("="*50)
        
        test_scenarios = [
            {"temp": 75.0, "desc": "Normal temperature"},
            {"temp": 82.0, "desc": "Elevated temperature"},
            {"temp": 89.5, "desc": "Critical temperature"},
            {"temp": 95.0, "desc": "Emergency temperature"}
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n🔄 Test {i}: {scenario['desc']} ({scenario['temp']}°F)")
            
            self.agent_responses.clear()
            
            temp_event = {
                "facility_id": "datacenter-test",
                "sensor_id": f"temp-test-{i}",
                "timestamp": time.time(),
                "temperature": scenario['temp'],
                "zone": "test_room"
            }
            
            await self.event_bus.publish("hvac.temperature.changed", json.dumps(temp_event))
            
            # Wait for response
            await asyncio.sleep(4)
            
            if 'HVAC' in self.agent_responses:
                response = self.agent_responses['HVAC']
                print(f"   ✅ Response: {response['data'].get('cooling_level', 'unknown')}")
                if 'execution_time' in response['data']:
                    print(f"   ⏱️  Time: {response['data']['execution_time']:.2f}s")
            else:
                print(f"   ❌ No response received")
    
    def show_system_status(self):
        """Show current system status"""
        memory = psutil.virtual_memory()
        
        print(f"\n📊 SYSTEM STATUS")
        print("-"*40)
        print(f"💾 Memory: {memory.percent:.1f}% ({memory.used / 1024**3:.1f}GB / {memory.total / 1024**3:.1f}GB)")
        print(f"🧠 Active LLMs: {len(llm_manager.active_llms)}")
        print(f"🤖 Running Agents: {len(self.agents)}")
        print(f"📡 Event Bus: {'Active' if self.event_bus.is_running else 'Inactive'}")
        
        if llm_manager.active_llms:
            print(f"🔹 Loaded Models:")
            for agent_type, llm in llm_manager.active_llms.items():
                print(f"   • {agent_type}: {llm.model}")
    
    def show_recent_responses(self):
        """Show recent agent responses"""
        print(f"\n📋 RECENT AGENT RESPONSES")
        print("-"*50)
        
        if not self.agent_responses:
            print("   No responses captured yet")
            return
        
        for agent, response in self.agent_responses.items():
            status_icon = "✅" if response['status'] == 'success' else "❌"
            print(f"{status_icon} {agent} [{response['timestamp']}]")
            
            data = response['data']
            if 'execution_time' in data:
                print(f"   ⏱️  Response time: {data['execution_time']:.2f}s")
            
            # Show key response data
            if agent == 'HVAC' and 'cooling_level' in data:
                print(f"   🌡️  Cooling: {data['cooling_level']}")
            elif 'power_optimization' in data:
                print(f"   ⚡ Power: {data['power_optimization'][:40]}...")
            elif 'security_assessment' in data:
                print(f"   🛡️  Security: {data['security_assessment'][:40]}...")
            
            print()

async def main():
    """Main demo function"""
    demo = IntegratedDemo()
    await demo.setup()
    
    while True:
        demo.show_system_status()
        
        print(f"\n🎮 INTEGRATED DEMO MENU")
        print("-"*40)
        print("1. 🌡️  Run Cooling Crisis Demo")
        print("2. 🧪 Test HVAC Agent Directly")
        print("3. 📊 Show Recent Responses")
        print("4. 📈 Show System Status")
        print("5. 🔄 Test Single Temperature Event")
        print("6. ❌ Exit")
        
        try:
            choice = input("\nSelect option (1-6): ").strip()
            
            if choice == '1':
                responses = await demo.run_cooling_crisis_demo()
                print(f"\n📊 Demo completed with {responses} agent responses")
                input("Press Enter to continue...")
                
            elif choice == '2':
                await demo.test_hvac_agent_directly()
                input("Press Enter to continue...")
                
            elif choice == '3':
                demo.show_recent_responses()
                input("Press Enter to continue...")
                
            elif choice == '4':
                demo.show_system_status()
                input("Press Enter to continue...")
                
            elif choice == '5':
                print("\n🔄 Testing single temperature event...")
                temp = float(input("Enter temperature (°F): ") or "85.0")
                
                temp_event = {
                    "facility_id": "datacenter-manual",
                    "sensor_id": "manual-test",
                    "timestamp": time.time(),
                    "temperature": temp,
                    "zone": "manual_test"
                }
                
                await demo.event_bus.publish("hvac.temperature.changed", json.dumps(temp_event))
                print("📤 Event published, waiting for response...")
                await asyncio.sleep(4)
                demo.show_recent_responses()
                input("Press Enter to continue...")
                
            elif choice == '6':
                print("👋 Demo ended!")
                break
                
            else:
                print("❌ Invalid choice")
                
        except KeyboardInterrupt:
            print("\n👋 Demo ended!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())