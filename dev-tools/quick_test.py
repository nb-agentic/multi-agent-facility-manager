#!/usr/bin/env python3
"""
Quick test to verify agents are responding
"""
import asyncio
import json
import sys
sys.path.append('.')

from demo_showcase import DatacenterDemo

async def quick_test():
    """Quick test of agent responses"""
    print("🧪 Quick Agent Response Test")
    
    demo = DatacenterDemo()
    await demo.setup()
    
    print("\n🔥 Testing HVAC Agent...")
    await demo._trigger_hvac_event(88.0)
    await asyncio.sleep(5)
    
    print(f"\n📊 Results:")
    print(f"   Agents responded: {len(demo.agent_responses)}/5")
    for agent, response in demo.agent_responses.items():
        print(f"   ✅ {agent}: {response['status']}")
    
    return len(demo.agent_responses) > 0

if __name__ == "__main__":
    success = asyncio.run(quick_test())
    if success:
        print("\n🎉 Agents are responding! System is working!")
    else:
        print("\n❌ No agent responses detected")