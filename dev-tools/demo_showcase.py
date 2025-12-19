#!/usr/bin/env python3
"""
IntelliCenter Demo Showcase
Professional demonstration interface for datacenter industry professionals.
"""
import asyncio
import json
import time
import psutil
import logging
from datetime import datetime
from intellicenter.core.event_bus import EventBus
from intellicenter.core.async_crew import llm_manager

# Configure logging for real-time output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('demo.log')
    ]
)
logger = logging.getLogger(__name__)


class DatacenterDemo:
    def __init__(self):
        self.event_bus = EventBus()
        self.demo_scenarios = {
            'cooling_crisis': {
                'name': 'Cooling System Crisis Response',
                'description': 'Simulates server room overheating and multi-agent response',
                'steps': [
                    ('Temperature spike detected', 'hvac', {'temperature': 89.5}),
                    ('Emergency cooling activation', 'power', {'cooling_level': 'emergency'}),
                    ('Security lockdown protocol', 'security', {'event_type': 'environmental_emergency'}),
                    ('Network traffic rerouting', 'network', {'bandwidth_usage': 95.0}),
                    ('Facility coordination', 'coordinator', {})
                ]
            },
            'security_breach': {
                'name': 'Security Breach Response',
                'description': 'Unauthorized access attempt and coordinated response',
                'steps': [
                    ('Unauthorized access detected', 'security', {'event_type': 'unauthorized_access'}),
                    ('HVAC system lockdown', 'hvac', {'temperature': 72.0}),
                    ('Power systems secured', 'power', {'cooling_level': 'low'}),
                    ('Network isolation activated', 'network', {'bandwidth_usage': 45.0}),
                    ('Emergency coordination', 'coordinator', {})
                ]
            },
            'power_optimization': {
                'name': 'Energy Efficiency Optimization',
                'description': 'Peak load management and energy cost reduction',
                'steps': [
                    ('Peak demand detected', 'power', {'cooling_level': 'high'}),
                    ('Temperature adjustment', 'hvac', {'temperature': 76.0}),
                    ('Load balancing', 'network', {'bandwidth_usage': 80.0}),
                    ('Security monitoring', 'security', {'event_type': 'high_activity'}),
                    ('Efficiency coordination', 'coordinator', {})
                ]
            }
        }
        
        self.agent_responses = {}
        self.demo_stats = {
            'scenarios_run': 0,
            'total_responses': 0,
            'avg_response_time': 0,
            'success_rate': 0
        }
        
    async def setup(self):
        """Initialize demo environment"""
        logger.info("🎬 Initializing IntelliCenter Demo Environment...")
        print("🎬 Initializing IntelliCenter Demo Environment...")
        await self.event_bus.start()
        
        # Import and start actual agents
        from intellicenter.agents.hvac_agent import HVACControlAgent
        from intellicenter.agents.power_agent import PowerManagementAgent
        from intellicenter.agents.security_agent import SecurityOperationsAgent
        from intellicenter.agents.network_agent import NetworkMonitoringAgent
        from intellicenter.agents.coordinator_agent import CoordinatorAgent
        
        logger.info("🤖 Starting AI agents...")
        print("🤖 Starting AI agents...")
        
        # Initialize agents
        self.agents = {
            'hvac': HVACControlAgent(self.event_bus),
            'power': PowerManagementAgent(self.event_bus),
            'security': SecurityOperationsAgent(self.event_bus),
            'network': NetworkMonitoringAgent(self.event_bus),
            'coordinator': CoordinatorAgent(self.event_bus)
        }
        
        # Start all agents
        for name, agent in self.agents.items():
            asyncio.create_task(agent.run())
            logger.info(f"   ✅ {name.upper()} Agent started")
            print(f"   ✅ {name.upper()} Agent started")
        
        # Subscribe to all agent responses
        self.event_bus.subscribe("hvac.cooling.decision", self._capture_hvac_response)
        self.event_bus.subscribe("power.optimization.decision", self._capture_power_response)
        self.event_bus.subscribe("security.assessment.decision", self._capture_security_response)
        self.event_bus.subscribe("network.assessment.decision", self._capture_network_response)
        self.event_bus.subscribe("facility.coordination.directive", self._capture_coordinator_response)
        
        # Wait a moment for agents to initialize
        await asyncio.sleep(2)
        
        logger.info("✅ Demo environment ready for datacenter showcase")
        print("✅ Demo environment ready for datacenter showcase")
        
    def _capture_response(self, agent_type: str, message: str):
        """Capture and analyze agent responses"""
        try:
            data = json.loads(message)
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            self.agent_responses[agent_type] = {
                'timestamp': timestamp,
                'data': data,
                'status': 'success' if not data.get('error') else 'error'
            }
            
            # Log the response in real-time
            logger.info(f"📨 {agent_type} Agent Response: {message[:100]}...")
            print(f"📨 {agent_type} Agent Response at {timestamp}")
            
            # Update stats
            self.demo_stats['total_responses'] += 1
            
            if 'execution_time' in data:
                current_avg = self.demo_stats['avg_response_time']
                new_time = data['execution_time']
                count = self.demo_stats['total_responses']
                self.demo_stats['avg_response_time'] = ((current_avg * (count - 1)) + new_time) / count
            
            # Calculate success rate
            successful = sum(1 for r in self.agent_responses.values() if r['status'] == 'success')
            self.demo_stats['success_rate'] = (successful / len(self.agent_responses)) * 100 if self.agent_responses else 0
            
        except Exception as e:
            logger.error(f"❌ Error capturing {agent_type} response: {e}")
            print(f"❌ Error capturing {agent_type} response: {e}")
    
    def _capture_hvac_response(self, message):
        self._capture_response('HVAC', message)
    
    def _capture_power_response(self, message):
        self._capture_response('Power', message)
    
    def _capture_security_response(self, message):
        self._capture_response('Security', message)
    
    def _capture_network_response(self, message):
        self._capture_response('Network', message)
    
    def _capture_coordinator_response(self, message):
        self._capture_response('Coordinator', message)
    
    def show_system_overview(self):
        """Display professional system overview"""
        memory = psutil.virtual_memory()
        
        print("\n" + "="*100)
        print("🏢 INTELLICENTER - AI-POWERED DATACENTER MANAGEMENT SYSTEM")
        print("="*100)
        print("🎯 SYSTEM CAPABILITIES:")
        print("   • Real-time thermal management with predictive cooling optimization")
        print("   • Intelligent power distribution and energy efficiency optimization")
        print("   • Advanced security monitoring with automated threat response")
        print("   • Network performance optimization and traffic management")
        print("   • Multi-agent coordination for complex facility operations")
        print()
        print("🧠 AI ARCHITECTURE:")
        print("   • 5 Specialized AI Agents with domain expertise")
        print("   • Local LLM deployment (no cloud dependencies)")
        print("   • Sub-2 second response times for critical events")
        print("   • Memory-optimized for edge computing environments")
        print()
        print("📊 CURRENT SYSTEM STATUS:")
        print(f"   • Memory Usage: {memory.percent:.1f}% ({memory.used / 1024**3:.1f}GB / {memory.total / 1024**3:.1f}GB)")
        print(f"   • Active AI Models: {len(llm_manager.active_llms)}")
        print(f"   • Response Success Rate: {self.demo_stats['success_rate']:.1f}%")
        print(f"   • Average Response Time: {self.demo_stats['avg_response_time']:.2f}s")
        print("="*100)
    
    def show_agent_architecture(self):
        """Display agent architecture details"""
        print("\n🤖 AI AGENT ARCHITECTURE")
        print("-"*80)
        
        agents = {
            'HVAC Control Agent': {
                'model': 'Mistral 7B',
                'expertise': 'Thermal dynamics, ASHRAE standards, energy optimization',
                'responsibilities': 'Temperature control, cooling optimization, energy efficiency'
            },
            'Security Operations Agent': {
                'model': 'Gemma2 2B',
                'expertise': 'Threat assessment, access control, compliance frameworks',
                'responsibilities': 'Intrusion detection, access management, incident response'
            },
            'Power Management Agent': {
                'model': 'Gemma2 2B', 
                'expertise': 'Electrical systems, load balancing, energy optimization',
                'responsibilities': 'Power distribution, efficiency optimization, cost management'
            },
            'Network Infrastructure Agent': {
                'model': 'Qwen2.5VL 7B',
                'expertise': 'Network protocols, performance optimization, troubleshooting',
                'responsibilities': 'Bandwidth management, latency optimization, connectivity'
            },
            'Facility Coordinator Agent': {
                'model': 'Mistral 7B',
                'expertise': 'Multi-system coordination, emergency protocols, operations',
                'responsibilities': 'System integration, conflict resolution, emergency response'
            }
        }
        
        for agent_name, details in agents.items():
            print(f"🔹 {agent_name}")
            print(f"   Model: {details['model']}")
            print(f"   Expertise: {details['expertise']}")
            print(f"   Responsibilities: {details['responsibilities']}")
            print()
    
    async def run_scenario(self, scenario_name: str):
        """Run a complete demo scenario"""
        if scenario_name not in self.demo_scenarios:
            print(f"❌ Unknown scenario: {scenario_name}")
            return
        
        scenario = self.demo_scenarios[scenario_name]
        print(f"\n🎬 RUNNING SCENARIO: {scenario['name'].upper()}")
        print(f"📋 Description: {scenario['description']}")
        print("="*80)
        
        self.agent_responses.clear()
        start_time = time.time()
        
        for step_name, agent_type, event_data in scenario['steps']:
            print(f"\n🔄 {step_name}...")
            
            # Trigger appropriate event
            if agent_type == 'hvac':
                await self._trigger_hvac_event(event_data.get('temperature', 75.0))
            elif agent_type == 'power':
                await self._trigger_power_event(event_data.get('cooling_level', 'medium'))
            elif agent_type == 'security':
                await self._trigger_security_event(event_data.get('event_type', 'monitoring'))
            elif agent_type == 'network':
                await self._trigger_network_event(event_data.get('bandwidth_usage', 70.0))
            elif agent_type == 'coordinator':
                await self._trigger_coordinator_event()
            
            # Wait for response
            await asyncio.sleep(3)
            
            # Show response if available
            if agent_type.upper() in self.agent_responses:
                response = self.agent_responses[agent_type.upper()]
                print(f"   ✅ {agent_type.upper()} Agent responded in {response['timestamp']}")
            else:
                print(f"   ⏳ Waiting for {agent_type.upper()} Agent response...")
        
        total_time = time.time() - start_time
        self.demo_stats['scenarios_run'] += 1
        
        print(f"\n🏁 SCENARIO COMPLETE")
        print(f"   Total execution time: {total_time:.2f} seconds")
        print(f"   Agents responded: {len(self.agent_responses)}/5")
        print(f"   Success rate: {self.demo_stats['success_rate']:.1f}%")
    
    async def _trigger_hvac_event(self, temperature: float):
        """Trigger HVAC event"""
        event_data = {
            "facility_id": "datacenter-production",
            "sensor_id": f"temp-rack-{int(time.time())}",
            "timestamp": time.time(),
            "temperature": temperature,
            "zone": "server_room_alpha",
            "criticality": "high" if temperature > 85 else "normal"
        }
        logger.info(f"🌡️ Triggering HVAC event: Temperature {temperature}°F")
        await self.event_bus.publish("hvac.temperature.changed", json.dumps(event_data))
    
    async def _trigger_power_event(self, cooling_level: str):
        """Trigger Power event"""
        event_data = {
            "cooling_level": cooling_level,
            "timestamp": time.time(),
            "power_demand": "critical" if cooling_level == "emergency" else "normal",
            "cost_impact": "high" if cooling_level in ["high", "emergency"] else "medium"
        }
        logger.info(f"⚡ Triggering Power event: Cooling level {cooling_level}")
        await self.event_bus.publish("hvac.cooling.decision", json.dumps(event_data))
    
    async def _trigger_security_event(self, event_type: str):
        """Trigger Security event"""
        event_data = {
            "event_id": f"sec-{int(time.time())}",
            "event_type": event_type,
            "timestamp": time.time(),
            "location": "server_room_entrance_alpha",
            "severity": "critical" if "emergency" in event_type else "medium",
            "compliance_impact": True
        }
        logger.info(f"🛡️ Triggering Security event: {event_type}")
        await self.event_bus.publish("facility.security.event", json.dumps(event_data))
    
    async def _trigger_network_event(self, bandwidth_usage: float):
        """Trigger Network event"""
        event_data = {
            "bandwidth_usage": bandwidth_usage,
            "latency": 15.2 if bandwidth_usage > 90 else 8.5,
            "packet_loss": 0.3 if bandwidth_usage > 90 else 0.05,
            "timestamp": time.time(),
            "critical_services_affected": bandwidth_usage > 90
        }
        logger.info(f"🌐 Triggering Network event: {bandwidth_usage}% bandwidth usage")
        await self.event_bus.publish("facility.network.assessment", json.dumps(event_data))
    
    async def _trigger_coordinator_event(self):
        """Trigger Coordinator event"""
        event_data = {
            "facility_id": "datacenter-production",
            "overall_status": "alert",
            "active_incidents": len(self.agent_responses),
            "timestamp": time.time(),
            "emergency_protocols_active": True,
            "systems_affected": list(self.agent_responses.keys())
        }
        logger.info(f"🎯 Triggering Coordinator event: {len(self.agent_responses)} active incidents")
        await self.event_bus.publish("facility.status.update", json.dumps(event_data))
    
    def show_live_responses(self):
        """Show live agent responses"""
        print(f"\n📊 LIVE AGENT RESPONSES")
        print("-"*80)
        
        if not self.agent_responses:
            print("   No responses captured yet. Run a scenario to see agent activity.")
            return
        
        for agent, response in self.agent_responses.items():
            status_icon = "✅" if response['status'] == 'success' else "❌"
            print(f"{status_icon} {agent} Agent [{response['timestamp']}]")
            
            data = response['data']
            if 'execution_time' in data:
                print(f"   Response Time: {data['execution_time']:.2f}s")
            
            if data.get('error'):
                print(f"   Error: {data['error']}")
            elif agent == 'HVAC' and 'cooling_level' in data:
                print(f"   Decision: {data['cooling_level']} cooling recommended")
            elif agent == 'Power' and 'power_optimization' in data:
                print(f"   Optimization: {data['power_optimization'][:60]}...")
            elif agent == 'Security' and 'security_assessment' in data:
                print(f"   Assessment: {data['security_assessment'][:60]}...")
            elif agent == 'Network' and 'network_assessment' in data:
                print(f"   Assessment: {data['network_assessment'][:60]}...")
            elif agent == 'Coordinator' and 'directive' in data:
                print(f"   Directive: {data['directive'][:60]}...")
            
            print()

async def professional_demo():
    """Professional demo interface for datacenter professionals"""
    demo = DatacenterDemo()
    await demo.setup()
    
    while True:
        demo.show_system_overview()
        
        print("\n🎮 DEMO MENU - IntelliCenter Datacenter AI")
        print("-"*50)
        print("1. 🌡️  Cooling Crisis Response Demo")
        print("2. 🛡️  Security Breach Response Demo") 
        print("3. ⚡ Energy Optimization Demo")
        print("4. 🤖 Show AI Agent Architecture")
        print("5. 📊 Show Live Agent Responses")
        print("6. 🔄 Run All Scenarios (Full Demo)")
        print("7. 📈 System Performance Metrics")
        print("8. 🎬 Continuous Demo Mode (for recording)")
        print("9. ❌ Exit Demo")
        print("-"*50)
        
        try:
            choice = input("Select demo option (1-9): ").strip()
            
            if choice == '1':
                await demo.run_scenario('cooling_crisis')
            elif choice == '2':
                await demo.run_scenario('security_breach')
            elif choice == '3':
                await demo.run_scenario('power_optimization')
            elif choice == '4':
                demo.show_agent_architecture()
                input("\nPress Enter to continue...")
            elif choice == '5':
                demo.show_live_responses()
                input("\nPress Enter to continue...")
            elif choice == '6':
                print("\n🎬 RUNNING COMPLETE DEMO SUITE...")
                for scenario_name in demo.demo_scenarios.keys():
                    await demo.run_scenario(scenario_name)
                    await asyncio.sleep(2)
                print("\n🏁 All scenarios completed!")
                input("\nPress Enter to continue...")
            elif choice == '7':
                memory = psutil.virtual_memory()
                print(f"\n📈 SYSTEM PERFORMANCE METRICS")
                print(f"   Memory Usage: {memory.percent:.1f}%")
                print(f"   Scenarios Run: {demo.demo_stats['scenarios_run']}")
                print(f"   Total Responses: {demo.demo_stats['total_responses']}")
                print(f"   Average Response Time: {demo.demo_stats['avg_response_time']:.2f}s")
                print(f"   Success Rate: {demo.demo_stats['success_rate']:.1f}%")
                print(f"   Active AI Models: {len(llm_manager.active_llms)}")
                input("\nPress Enter to continue...")
            elif choice == '8':
                print("\n🎬 CONTINUOUS DEMO MODE - Perfect for screen recording!")
                print("This will run scenarios continuously. Press Ctrl+C to stop.")
                try:
                    while True:
                        for scenario_name in demo.demo_scenarios.keys():
                            await demo.run_scenario(scenario_name)
                            await asyncio.sleep(5)
                except KeyboardInterrupt:
                    print("\n🛑 Continuous demo stopped")
            elif choice == '9':
                print("👋 Demo session ended. Thank you!")
                break
            else:
                print("❌ Invalid choice. Please select 1-9.")
                
        except KeyboardInterrupt:
            print("\n👋 Demo session ended. Thank you!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🎬 Starting IntelliCenter Professional Demo...")
    print("📋 Real-time logs are being written to demo.log")
    print("💡 To watch logs in real-time: tail -f demo.log")
    asyncio.run(professional_demo())