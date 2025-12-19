#!/usr/bin/env python3
"""
Visual Dashboard for Screenshots and Video Recording
Creates an attractive real-time display perfect for demonstrations.
"""
import asyncio
import json
import time
import psutil
import os
from datetime import datetime
from intellicenter.core.event_bus import EventBus
from intellicenter.core.async_crew import llm_manager


class VisualDashboard:
    def __init__(self):
        self.event_bus = EventBus()
        self.agent_status = {
            'HVAC': {'status': 'IDLE', 'last_action': 'Monitoring temperature', 'response_time': 0, 'color': '🟡'},
            'Power': {'status': 'IDLE', 'last_action': 'Optimizing energy usage', 'response_time': 0, 'color': '🟡'},
            'Security': {'status': 'IDLE', 'last_action': 'Scanning for threats', 'response_time': 0, 'color': '🟡'},
            'Network': {'status': 'IDLE', 'last_action': 'Monitoring bandwidth', 'response_time': 0, 'color': '🟡'},
            'Coordinator': {'status': 'IDLE', 'last_action': 'Coordinating systems', 'response_time': 0, 'color': '🟡'}
        }
        
        self.facility_metrics = {
            'temperature': 72.5,
            'power_usage': 65.2,
            'security_level': 'SECURE',
            'network_load': 45.8,
            'uptime': 0
        }
        
        self.recent_events = []
        self.start_time = time.time()
        
    async def setup(self):
        """Initialize visual dashboard"""
        await self.event_bus.start()
        
        # Subscribe to all events
        self.event_bus.subscribe("hvac.cooling.decision", self._update_hvac_status)
        self.event_bus.subscribe("power.optimization.decision", self._update_power_status)
        self.event_bus.subscribe("security.assessment.decision", self._update_security_status)
        self.event_bus.subscribe("network.assessment.decision", self._update_network_status)
        self.event_bus.subscribe("facility.coordination.directive", self._update_coordinator_status)
        
    def _update_agent_status(self, agent_name: str, message: str):
        """Update agent status from response"""
        try:
            data = json.loads(message)
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            if data.get('error'):
                self.agent_status[agent_name]['status'] = 'ERROR'
                self.agent_status[agent_name]['color'] = '🔴'
                self.agent_status[agent_name]['last_action'] = f"Error: {data['error'][:30]}..."
            elif data.get('fallback'):
                self.agent_status[agent_name]['status'] = 'FALLBACK'
                self.agent_status[agent_name]['color'] = '🟠'
                self.agent_status[agent_name]['last_action'] = "Using fallback response"
            else:
                self.agent_status[agent_name]['status'] = 'ACTIVE'
                self.agent_status[agent_name]['color'] = '🟢'
                
                # Set specific actions based on agent type
                if agent_name == 'HVAC':
                    cooling = data.get('cooling_level', 'unknown')
                    self.agent_status[agent_name]['last_action'] = f"Set cooling to {cooling}"
                    self.facility_metrics['temperature'] = data.get('target_temp', self.facility_metrics['temperature'])
                elif agent_name == 'Power':
                    self.agent_status[agent_name]['last_action'] = "Optimized power distribution"
                    self.facility_metrics['power_usage'] = min(95, self.facility_metrics['power_usage'] + 5)
                elif agent_name == 'Security':
                    self.agent_status[agent_name]['last_action'] = "Threat assessment completed"
                    self.facility_metrics['security_level'] = 'MONITORING'
                elif agent_name == 'Network':
                    self.agent_status[agent_name]['last_action'] = "Network optimization applied"
                    self.facility_metrics['network_load'] = data.get('bandwidth_usage', self.facility_metrics['network_load'])
                elif agent_name == 'Coordinator':
                    self.agent_status[agent_name]['last_action'] = "Systems coordinated"
            
            if 'execution_time' in data:
                self.agent_status[agent_name]['response_time'] = data['execution_time']
            
            # Add to recent events
            event = f"[{timestamp}] {agent_name}: {self.agent_status[agent_name]['last_action']}"
            self.recent_events.append(event)
            if len(self.recent_events) > 10:
                self.recent_events = self.recent_events[-10:]
                
        except Exception as e:
            print(f"Error updating {agent_name} status: {e}")
    
    def _update_hvac_status(self, message):
        self._update_agent_status('HVAC', message)
    
    def _update_power_status(self, message):
        self._update_agent_status('Power', message)
    
    def _update_security_status(self, message):
        self._update_agent_status('Security', message)
    
    def _update_network_status(self, message):
        self._update_agent_status('Network', message)
    
    def _update_coordinator_status(self, message):
        self._update_agent_status('Coordinator', message)
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def display_header(self):
        """Display professional header"""
        uptime = time.time() - self.start_time
        memory = psutil.virtual_memory()
        
        print("╔" + "="*98 + "╗")
        print("║" + " "*98 + "║")
        print("║" + "🏢 INTELLICENTER - AI-POWERED DATACENTER MANAGEMENT SYSTEM".center(98) + "║")
        print("║" + " "*98 + "║")
        print("║" + f"🕐 Uptime: {uptime:.0f}s  |  💾 Memory: {memory.percent:.1f}%  |  🧠 AI Models: {len(llm_manager.active_llms)}  |  🌐 Status: OPERATIONAL".center(98) + "║")
        print("║" + " "*98 + "║")
        print("╚" + "="*98 + "╝")
    
    def display_facility_metrics(self):
        """Display facility metrics"""
        temp_color = "🔴" if self.facility_metrics['temperature'] > 85 else "🟡" if self.facility_metrics['temperature'] > 80 else "🟢"
        power_color = "🔴" if self.facility_metrics['power_usage'] > 90 else "🟡" if self.facility_metrics['power_usage'] > 75 else "🟢"
        network_color = "🔴" if self.facility_metrics['network_load'] > 90 else "🟡" if self.facility_metrics['network_load'] > 75 else "🟢"
        
        print("\n┌─ FACILITY METRICS " + "─"*80 + "┐")
        print(f"│ {temp_color} Temperature: {self.facility_metrics['temperature']:.1f}°F     " +
              f"{power_color} Power Usage: {self.facility_metrics['power_usage']:.1f}%     " +
              f"🛡️  Security: {self.facility_metrics['security_level']}     " +
              f"{network_color} Network Load: {self.facility_metrics['network_load']:.1f}% │")
        print("└" + "─"*98 + "┘")
    
    def display_agent_status(self):
        """Display agent status grid"""
        print("\n┌─ AI AGENT STATUS " + "─"*79 + "┐")
        print("│" + " "*98 + "│")
        
        # Display agents in a grid
        agents = list(self.agent_status.items())
        for i in range(0, len(agents), 2):
            left_agent = agents[i]
            right_agent = agents[i+1] if i+1 < len(agents) else None
            
            left_name, left_data = left_agent
            left_line = f"│ {left_data['color']} {left_name:<12} │ {left_data['status']:<8} │ {left_data['last_action']:<35}"
            
            if right_agent:
                right_name, right_data = right_agent
                right_line = f" {right_data['color']} {right_name:<12} │ {right_data['status']:<8} │ {right_data['last_action']:<35} │"
                print(left_line + right_line)
            else:
                print(left_line + " "*49 + "│")
        
        print("│" + " "*98 + "│")
        print("└" + "─"*98 + "┘")
    
    def display_recent_events(self):
        """Display recent events log"""
        print("\n┌─ RECENT EVENTS " + "─"*81 + "┐")
        
        if not self.recent_events:
            print("│ No events recorded yet" + " "*75 + "│")
        else:
            for event in self.recent_events[-8:]:  # Show last 8 events
                event_text = event[:96] if len(event) > 96 else event
                padding = 98 - len(event_text)
                print(f"│ {event_text}" + " "*padding + "│")
        
        print("└" + "─"*98 + "┘")
    
    def display_ai_models(self):
        """Display active AI models"""
        print("\n┌─ ACTIVE AI MODELS " + "─"*78 + "┐")
        
        model_info = {
            'hvac': 'Mistral 7B - Thermal Dynamics Expert',
            'security': 'Gemma2 2B - Threat Assessment Specialist', 
            'power': 'Gemma2 2B - Energy Optimization Expert',
            'network': 'Qwen2.5VL 7B - Network Infrastructure Specialist',
            'coordinator': 'Mistral 7B - Multi-Agent Coordinator'
        }
        
        for agent_type, description in model_info.items():
            status = "🟢 LOADED" if agent_type in llm_manager.active_llms else "⚪ STANDBY"
            print(f"│ {status} {description:<85} │")
        
        print("└" + "─"*98 + "┘")
    
    def display_full_dashboard(self):
        """Display complete visual dashboard"""
        self.clear_screen()
        self.display_header()
        self.display_facility_metrics()
        self.display_agent_status()
        self.display_recent_events()
        self.display_ai_models()
        
        print(f"\n🎬 Perfect for screenshots and video recording!")
        print(f"📊 Dashboard updates in real-time as agents respond to events")
    
    async def trigger_demo_event(self, event_type: str):
        """Trigger demo events for visual demonstration"""
        timestamp = time.time()
        
        if event_type == 'temperature_spike':
            self.facility_metrics['temperature'] = 89.5
            event_data = {
                "facility_id": "datacenter-alpha",
                "sensor_id": "temp-rack-07",
                "timestamp": timestamp,
                "temperature": 89.5,
                "zone": "server_room_alpha",
                "alert_level": "critical"
            }
            await self.event_bus.publish("hvac.temperature.changed", json.dumps(event_data))
            
        elif event_type == 'security_breach':
            self.facility_metrics['security_level'] = 'ALERT'
            event_data = {
                "event_id": f"sec-{int(timestamp)}",
                "event_type": "unauthorized_access_attempt",
                "timestamp": timestamp,
                "location": "server_room_entrance",
                "severity": "high",
                "user_id": "unknown"
            }
            await self.event_bus.publish("facility.security.event", json.dumps(event_data))
            
        elif event_type == 'power_optimization':
            self.facility_metrics['power_usage'] = 85.2
            event_data = {
                "cooling_level": "high",
                "timestamp": timestamp,
                "power_demand": "peak",
                "efficiency_target": 0.85
            }
            await self.event_bus.publish("hvac.cooling.decision", json.dumps(event_data))
            
        elif event_type == 'network_congestion':
            self.facility_metrics['network_load'] = 92.3
            event_data = {
                "bandwidth_usage": 92.3,
                "latency": 25.7,
                "packet_loss": 0.8,
                "timestamp": timestamp,
                "critical_services_affected": True
            }
            await self.event_bus.publish("facility.network.assessment", json.dumps(event_data))

async def visual_demo():
    """Visual demo perfect for recording"""
    dashboard = VisualDashboard()
    await dashboard.setup()
    
    print("🎬 IntelliCenter Visual Demo - Perfect for Screenshots & Video!")
    print("This creates a professional-looking dashboard that updates in real-time.")
    print("\nDemo Options:")
    print("1. Static Dashboard (for screenshots)")
    print("2. Live Demo with Events (for video recording)")
    print("3. Continuous Auto-Demo (hands-free recording)")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == '1':
        # Static dashboard for screenshots
        dashboard.display_full_dashboard()
        input("\n📸 Perfect for screenshots! Press Enter when done...")
        
    elif choice == '2':
        # Interactive live demo
        dashboard.display_full_dashboard()
        
        print("\n🎮 Live Demo Controls:")
        print("Press 't' for temperature spike")
        print("Press 's' for security breach") 
        print("Press 'p' for power optimization")
        print("Press 'n' for network congestion")
        print("Press 'q' to quit")
        
        while True:
            try:
                # Update dashboard every 2 seconds
                await asyncio.sleep(2)
                dashboard.display_full_dashboard()
                
                print("\nPress key for demo event (t/s/p/n/q): ", end='', flush=True)
                
                # Non-blocking input simulation
                # In real use, you'd trigger events manually
                
            except KeyboardInterrupt:
                break
                
    elif choice == '3':
        # Continuous auto-demo
        print("\n🎬 Starting continuous auto-demo...")
        print("Perfect for hands-free video recording!")
        
        events = ['temperature_spike', 'security_breach', 'power_optimization', 'network_congestion']
        event_index = 0
        
        try:
            while True:
                dashboard.display_full_dashboard()
                
                # Trigger next event every 10 seconds
                await asyncio.sleep(10)
                
                event = events[event_index % len(events)]
                print(f"\n🔄 Triggering {event.replace('_', ' ').title()}...")
                await dashboard.trigger_demo_event(event)
                
                event_index += 1
                await asyncio.sleep(5)  # Wait for agent response
                
        except KeyboardInterrupt:
            print("\n🛑 Auto-demo stopped")

if __name__ == "__main__":
    asyncio.run(visual_demo())