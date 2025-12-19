#!/usr/bin/env python3
"""
Real-time Agent Activity Monitor
Shows live logs and metrics from all agents.
"""
import asyncio
import json
import time
import psutil
from datetime import datetime
from intellicenter.core.event_bus import EventBus

class AgentMonitor:
    def __init__(self):
        self.event_bus = EventBus()
        self.metrics = {
            'hvac_responses': 0,
            'power_responses': 0,
            'security_responses': 0,
            'network_responses': 0,
            'coordinator_responses': 0,
            'total_events': 0,
            'errors': 0,
            'start_time': time.time()
        }
        
    async def setup(self):
        """Initialize monitoring"""
        print("🔍 Starting Agent Activity Monitor...")
        await self.event_bus.start()
        
        # Subscribe to all agent events
        self.event_bus.subscribe("hvac.temperature.changed", self._monitor_hvac_input)
        self.event_bus.subscribe("hvac.cooling.decision", self._monitor_hvac_output)
        self.event_bus.subscribe("power.optimization.decision", self._monitor_power_output)
        self.event_bus.subscribe("security.assessment.decision", self._monitor_security_output)
        self.event_bus.subscribe("network.assessment.decision", self._monitor_network_output)
        self.event_bus.subscribe("facility.coordination.directive", self._monitor_coordinator_output)
        
        print("✅ Monitoring all agent channels...")
        print("📊 Use Ctrl+C to stop monitoring\n")
        
    def _get_timestamp(self):
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    def _monitor_hvac_input(self, message):
        """Monitor HVAC input events"""
        try:
            data = json.loads(message)
            temp = data.get('temperature', 'N/A')
            print(f"🌡️  [{self._get_timestamp()}] HVAC INPUT: Temperature {temp}°F")
        except Exception as e:
            print(f"❌ [{self._get_timestamp()}] HVAC INPUT ERROR: {e}")
    
    def _monitor_hvac_output(self, message):
        """Monitor HVAC responses"""
        try:
            data = json.loads(message)
            self.metrics['hvac_responses'] += 1
            self.metrics['total_events'] += 1
            
            if data.get('error'):
                self.metrics['errors'] += 1
                print(f"❌ [{self._get_timestamp()}] HVAC ERROR: {data['error']}")
            elif data.get('fallback'):
                print(f"⚠️  [{self._get_timestamp()}] HVAC FALLBACK: {data.get('cooling_level', 'N/A')}")
            else:
                cooling = data.get('cooling_level', 'N/A')
                print(f"✅ [{self._get_timestamp()}] HVAC DECISION: {cooling} cooling")
                
        except Exception as e:
            self.metrics['errors'] += 1
            print(f"❌ [{self._get_timestamp()}] HVAC PARSE ERROR: {e}")
    
    def _monitor_power_output(self, message):
        """Monitor Power agent responses"""
        try:
            data = json.loads(message)
            self.metrics['power_responses'] += 1
            self.metrics['total_events'] += 1
            
            if data.get('error'):
                self.metrics['errors'] += 1
                print(f"❌ [{self._get_timestamp()}] POWER ERROR: {data['error']}")
            elif data.get('fallback'):
                print(f"⚠️  [{self._get_timestamp()}] POWER FALLBACK: Maintain current distribution")
            else:
                optimization = data.get('power_optimization', 'N/A')[:50]
                print(f"⚡ [{self._get_timestamp()}] POWER DECISION: {optimization}...")
                
        except Exception as e:
            self.metrics['errors'] += 1
            print(f"❌ [{self._get_timestamp()}] POWER PARSE ERROR: {e}")
    
    def _monitor_security_output(self, message):
        """Monitor Security agent responses"""
        try:
            data = json.loads(message)
            self.metrics['security_responses'] += 1
            self.metrics['total_events'] += 1
            
            if data.get('error'):
                self.metrics['errors'] += 1
                print(f"❌ [{self._get_timestamp()}] SECURITY ERROR: {data['error']}")
            elif data.get('fallback'):
                print(f"⚠️  [{self._get_timestamp()}] SECURITY FALLBACK: Escalate to human operator")
            else:
                assessment = data.get('security_assessment', 'N/A')[:50]
                print(f"🛡️  [{self._get_timestamp()}] SECURITY DECISION: {assessment}...")
                
        except Exception as e:
            self.metrics['errors'] += 1
            print(f"❌ [{self._get_timestamp()}] SECURITY PARSE ERROR: {e}")
    
    def _monitor_network_output(self, message):
        """Monitor Network agent responses"""
        try:
            data = json.loads(message)
            self.metrics['network_responses'] += 1
            self.metrics['total_events'] += 1
            
            if data.get('error'):
                self.metrics['errors'] += 1
                print(f"❌ [{self._get_timestamp()}] NETWORK ERROR: {data['error']}")
            elif data.get('fallback'):
                print(f"⚠️  [{self._get_timestamp()}] NETWORK FALLBACK: Maintain current configuration")
            else:
                assessment = data.get('network_assessment', 'N/A')[:50]
                print(f"🌐 [{self._get_timestamp()}] NETWORK DECISION: {assessment}...")
                
        except Exception as e:
            self.metrics['errors'] += 1
            print(f"❌ [{self._get_timestamp()}] NETWORK PARSE ERROR: {e}")
    
    def _monitor_coordinator_output(self, message):
        """Monitor Coordinator agent responses"""
        try:
            data = json.loads(message)
            self.metrics['coordinator_responses'] += 1
            self.metrics['total_events'] += 1
            
            if data.get('error'):
                self.metrics['errors'] += 1
                print(f"❌ [{self._get_timestamp()}] COORDINATOR ERROR: {data['error']}")
            else:
                directive = data.get('directive', 'N/A')[:50]
                print(f"📜 [{self._get_timestamp()}] COORDINATOR DIRECTIVE: {directive}...")
                
        except Exception as e:
            self.metrics['errors'] += 1
            print(f"❌ [{self._get_timestamp()}] COORDINATOR PARSE ERROR: {e}")
    
    def print_metrics(self):
        """Print current metrics"""
        uptime = time.time() - self.metrics['start_time']
        memory = psutil.virtual_memory()
        
        print(f"\n" + "="*60)
        print(f"📊 AGENT MONITORING METRICS")
        print("="*60)
        print(f"⏱️  Uptime: {uptime:.1f}s")
        print(f"💾 Memory: {memory.percent:.1f}% used ({memory.used / 1024**3:.1f}GB / {memory.total / 1024**3:.1f}GB)")
        print(f"📈 Total Events: {self.metrics['total_events']}")
        print(f"❌ Errors: {self.metrics['errors']}")
        print("-" * 60)
        print(f"🌡️  HVAC Responses: {self.metrics['hvac_responses']}")
        print(f"⚡ Power Responses: {self.metrics['power_responses']}")
        print(f"🛡️  Security Responses: {self.metrics['security_responses']}")
        print(f"🌐 Network Responses: {self.metrics['network_responses']}")
        print(f"📜 Coordinator Responses: {self.metrics['coordinator_responses']}")
        
        if self.metrics['total_events'] > 0:
            error_rate = (self.metrics['errors'] / self.metrics['total_events']) * 100
            print(f"📊 Error Rate: {error_rate:.1f}%")
            
        print("="*60 + "\n")
    
    async def run_monitoring(self):
        """Run continuous monitoring"""
        await self.setup()
        
        try:
            # Print metrics every 30 seconds
            while True:
                await asyncio.sleep(30)
                self.print_metrics()
                
        except KeyboardInterrupt:
            print(f"\n🛑 Monitoring stopped by user")
            self.print_metrics()

if __name__ == "__main__":
    monitor = AgentMonitor()
    asyncio.run(monitor.run_monitoring())