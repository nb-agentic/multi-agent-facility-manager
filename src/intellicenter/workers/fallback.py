"""
Fallback Response Generator for LLM Failures

Provides mock responses when LLM services are unavailable or when agents fail to generate proper responses.
Ensures system continuity and graceful degradation during service interruptions.
"""

import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class AgentType(Enum):
    """Supported agent types for fallback responses"""
    HVAC = "hvac"
    POWER = "power"
    SECURITY = "security"
    NETWORK = "network"
    COORDINATOR = "coordinator"


@dataclass
class FallbackResponse:
    """Structured fallback response with metadata"""
    agent_type: AgentType
    response: str
    confidence: float
    reasoning: str
    timestamp: float
    fallback_triggered: bool = True
    context: Optional[Dict[str, Any]] = None


class MockAgent:
    """Mock agent that provides fallback responses when LLM services fail"""
    
    def __init__(self):
        self.response_templates = self._initialize_response_templates()
        self.performance_metrics = {
            "total_requests": 0,
            "fallback_responses": 0,
            "avg_confidence": 0.0,
            "response_times": []
        }
    
    def _initialize_response_templates(self) -> Dict[AgentType, Dict[str, Any]]:
        """Initialize comprehensive response templates for each agent type"""
        return {
            AgentType.HVAC: {
                "temperature_control": {
                    "response": "🌡️ Temperature control activated: Maintaining optimal range (20-24°C). Using fallback rule-based system.",
                    "confidence": 0.75,
                    "reasoning": "Rule-based temperature control activated due to LLM unavailability"
                },
                "cooling_decision": {
                    "response": "❄️ Cooling decision: Medium cooling level activated. System operating in safe fallback mode.",
                    "confidence": 0.80,
                    "reasoning": "Default cooling strategy applied based on temperature thresholds"
                },
                "emergency_cooling": {
                    "response": "🚨 Emergency cooling activated: High cooling level engaged. System in emergency fallback mode.",
                    "confidence": 0.90,
                    "reasoning": "Emergency protocols triggered due to high temperature detection"
                },
                "energy_efficiency": {
                    "response": "⚡ Energy efficiency analysis: Current consumption at 100% baseline. Fallback optimization applied.",
                    "confidence": 0.70,
                    "reasoning": "Standard efficiency metrics applied without AI analysis"
                }
            },
            AgentType.POWER: {
                "power_monitoring": {
                    "response": "⚡ Power monitoring: 75% load detected (75kW/100kW capacity). Status: Optimal operation.",
                    "confidence": 0.85,
                    "confidence": 0.85,
                    "reasoning": "Standard power monitoring with predefined thresholds"
                },
                "ups_status": {
                    "response": "🔋 UPS Status: 95% battery, 30 minutes runtime at current load. Backup systems operational.",
                    "confidence": 0.95,
                    "reasoning": "UPS monitoring with standard battery level checks"
                },
                "cost_analysis": {
                    "response": "💰 Cost analysis: Medium consumption level = $1100/day. Fallback cost estimation applied.",
                    "confidence": 0.75,
                    "reasoning": "Standard cost model applied without real-time optimization"
                },
                "power_optimization": {
                    "response": "⚡ Power optimization: Maintaining current distribution. Fallback mode activated.",
                    "confidence": 0.80,
                    "reasoning": "Conservative power management strategy applied"
                }
            },
            AgentType.SECURITY: {
                "surveillance": {
                    "response": "📷 Surveillance: All camera feeds operational. No anomalies detected in monitored zones.",
                    "confidence": 0.90,
                    "reasoning": "Standard surveillance monitoring with baseline threat detection"
                },
                "access_control": {
                    "response": "🔐 Access control: All access points secured. Standard authentication protocols active.",
                    "confidence": 0.95,
                    "reasoning": "Default access control measures in fallback mode"
                },
                "threat_assessment": {
                    "response": "🛡️ Threat assessment: Low threat level detected. Standard security protocols engaged.",
                    "confidence": 0.75,
                    "reasoning": "Baseline threat analysis applied without AI enhancement"
                },
                "incident_response": {
                    "response": "🚨 Incident response: Standard protocols activated. Security team notified for manual review.",
                    "confidence": 0.85,
                    "reasoning": "Escalation to human operators due to AI unavailability"
                }
            },
            AgentType.NETWORK: {
                "traffic_analysis": {
                    "response": "📈 Network traffic: Core segment at 45% utilization. Within normal operating parameters.",
                    "confidence": 0.80,
                    "reasoning": "Standard traffic monitoring with predefined thresholds"
                },
                "latency_check": {
                    "response": "⏱️ Latency: External gateway at 15ms response time. Network performance optimal.",
                    "confidence": 0.85,
                    "reasoning": "Standard latency monitoring with baseline performance checks"
                },
                "device_status": {
                    "response": "✅ Network devices: All critical devices online and operational. No issues detected.",
                    "confidence": 0.95,
                    "reasoning": "Standard device health monitoring in fallback mode"
                },
                "routing_optimization": {
                    "response": "🌐 Routing optimization: Maintaining current routing configuration. Fallback routing active.",
                    "confidence": 0.75,
                    "reasoning": "Conservative routing strategy applied without AI optimization"
                }
            },
            AgentType.COORDINATOR: {
                "facility_coordination": {
                    "response": "📜 Facility coordination: All systems operational. Standard coordination protocols engaged.",
                    "confidence": 0.80,
                    "reasoning": "Standard facility coordination without AI optimization"
                },
                "system_integration": {
                    "response": "🔗 System integration: All agent reports synchronized. Fallback coordination mode active.",
                    "confidence": 0.85,
                    "reasoning": "Basic system integration without advanced AI coordination"
                },
                "emergency_coordination": {
                    "response": "🚨 Emergency coordination: Standard emergency protocols activated. Manual oversight required.",
                    "confidence": 0.90,
                    "reasoning": "Emergency coordination protocols engaged due to AI unavailability"
                },
                "performance_monitoring": {
                    "response": "📊 Performance monitoring: All agents operational. Standard performance metrics collected.",
                    "confidence": 0.75,
                    "reasoning": "Basic performance monitoring without AI analysis"
                }
            }
        }
    
    def generate_fallback_response(self, agent_type, scenario: str,
                                 context: Optional[Dict[str, Any]] = None) -> FallbackResponse:
        """Generate a fallback response based on agent type and scenario"""
        start_time = time.time()
        self.performance_metrics["total_requests"] += 1
        
        try:
            # Handle invalid agent type - convert to string for comparison
            if isinstance(agent_type, str):
                if agent_type not in [at.value for at in AgentType]:
                    # Use generic response for invalid agent type
                    response = f"🚨 Invalid agent type '{agent_type}'. System error in fallback response."
                    confidence = 0.20
                    reasoning = "Invalid agent type provided"
                    agent_type_enum = AgentType.COORDINATOR  # Default for error response
                else:
                    agent_type_enum = AgentType(agent_type)
                    # Get the appropriate template for the scenario
                    if scenario in self.response_templates[agent_type_enum]:
                        template = self.response_templates[agent_type_enum][scenario]
                        response = template["response"]
                        confidence = template["confidence"]
                        reasoning = template["reasoning"]
                    else:
                        # Generic fallback response
                        response = self._get_generic_fallback(agent_type_enum, scenario)
                        confidence = 0.60
                        reasoning = "Generic fallback response applied due to unknown scenario"
            else:
                agent_type_enum = agent_type
                # Get the appropriate template for the scenario
                if scenario in self.response_templates[agent_type_enum]:
                    template = self.response_templates[agent_type_enum][scenario]
                    response = template["response"]
                    confidence = template["confidence"]
                    reasoning = template["reasoning"]
                else:
                    # Generic fallback response
                    response = self._get_generic_fallback(agent_type_enum, scenario)
                    confidence = 0.60
                    reasoning = "Generic fallback response applied due to unknown scenario"
            
            # Enhance response with context if provided
            if context:
                response = self._enhance_response_with_context(response, context, agent_type_enum)
            
            # Create fallback response object
            fallback_response = FallbackResponse(
                agent_type=agent_type_enum,
                response=response,
                confidence=confidence,
                reasoning=reasoning,
                timestamp=time.time(),
                fallback_triggered=True,
                context=context
            )
            
            # Update performance metrics
            response_time = time.time() - start_time
            self.performance_metrics["response_times"].append(response_time)
            self.performance_metrics["fallback_responses"] += 1
            
            # Update average confidence
            total_confidence = self.performance_metrics["avg_confidence"] * (self.performance_metrics["fallback_responses"] - 1)
            self.performance_metrics["avg_confidence"] = (total_confidence + confidence) / self.performance_metrics["fallback_responses"]
            
            return fallback_response
            
        except Exception as e:
            # Emergency fallback
            emergency_response = FallbackResponse(
                agent_type=agent_type,
                response=f"🚨 System error in fallback generator: {str(e)}. Emergency protocols activated.",
                confidence=0.30,
                reasoning="Emergency fallback due to generator error",
                timestamp=time.time(),
                fallback_triggered=True,
                context=context
            )
            self.performance_metrics["fallback_responses"] += 1
            return emergency_response
    
    def _get_generic_fallback(self, agent_type: AgentType, scenario: str) -> str:
        """Generate generic fallback response when specific template is not found"""
        base_responses = {
            AgentType.HVAC: "🌡️ HVAC system: Operating in fallback mode. Standard temperature control engaged.",
            AgentType.POWER: "⚡ Power system: Operating in fallback mode. Standard power management engaged.",
            AgentType.SECURITY: "🛡️ Security system: Operating in fallback mode. Standard security protocols engaged.",
            AgentType.NETWORK: "🌐 Network system: Operating in fallback mode. Standard network monitoring engaged.",
            AgentType.COORDINATOR: "📜 Coordinator system: Operating in fallback mode. Standard coordination engaged."
        }
        
        return base_responses.get(agent_type, "🔄 System: Operating in fallback mode. Standard protocols engaged.")
    
    def _enhance_response_with_context(self, response: str, context: Dict[str, Any],
                                     agent_type: AgentType) -> str:
        """Enhance fallback response with contextual information"""
        try:
            # Always try to add context information regardless of agent type
            if context:
                context_parts = []
                for key, value in context.items():
                    if key == "temperature" and agent_type == AgentType.HVAC:
                        context_parts.append(f"Current temperature: {value}°C")
                    elif key == "load" and agent_type == AgentType.POWER:
                        context_parts.append(f"Current load: {value}%")
                    elif key == "event_type" and agent_type == AgentType.SECURITY:
                        context_parts.append(f"Event type: {value}")
                    elif key == "segment" and agent_type == AgentType.NETWORK:
                        context_parts.append(f"Segment: {value}")
                    elif key == "status" and agent_type == AgentType.COORDINATOR:
                        context_parts.append(f"Overall status: {value}")
                    else:
                        # Generic context addition for other cases
                        context_parts.append(f"{key}: {value}")
                
                if context_parts:
                    response += " " + "; ".join(context_parts) + "."
            
            return response
            
        except Exception:
            return response  # Return original response if context enhancement fails
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance metrics for the fallback response generator"""
        avg_response_time = (
            sum(self.performance_metrics["response_times"]) / len(self.performance_metrics["response_times"])
            if self.performance_metrics["response_times"] else 0.0
        )
        
        return {
            "total_requests": self.performance_metrics["total_requests"],
            "fallback_responses": self.performance_metrics["fallback_responses"],
            "fallback_rate": (
                self.performance_metrics["fallback_responses"] / self.performance_metrics["total_requests"]
                if self.performance_metrics["total_requests"] > 0 else 0.0
            ),
            "avg_confidence": self.performance_metrics["avg_confidence"],
            "avg_response_time": avg_response_time,
            "last_update": time.time()
        }
    
    def get_available_scenarios(self, agent_type: AgentType) -> List[str]:
        """Get list of available scenarios for a specific agent type"""
        if agent_type in self.response_templates:
            return list(self.response_templates[agent_type].keys())
        return []
    
    def is_scenario_supported(self, agent_type: AgentType, scenario: str) -> bool:
        """Check if a specific scenario is supported for an agent type"""
        return (
            agent_type in self.response_templates and 
            scenario in self.response_templates[agent_type]
        )


# Global fallback response generator instance
fallback_generator = MockAgent()


def get_fallback_response(agent_type: str, scenario: str, 
                         context: Optional[Dict[str, Any]] = None) -> FallbackResponse:
    """
    Convenience function to get a fallback response
    
    Args:
        agent_type: Type of agent (hvac, power, security, network, coordinator)
        scenario: Specific scenario requiring fallback response
        context: Optional contextual information
    
    Returns:
        FallbackResponse object with structured response data
    """
    try:
        agent_enum = AgentType(agent_type.lower())
        return fallback_generator.generate_fallback_response(agent_enum, scenario, context)
    except ValueError:
        # Handle invalid agent type
        return FallbackResponse(
            agent_type=AgentType.COORDINATOR,  # Default to coordinator
            response=f"🚨 Invalid agent type '{agent_type}'. System error in fallback response.",
            confidence=0.20,
            reasoning="Invalid agent type provided",
            timestamp=time.time(),
            fallback_triggered=True,
            context={"error": "Invalid agent type"}
        )


def get_fallback_response_json(agent_type: str, scenario: str, 
                              context: Optional[Dict[str, Any]] = None) -> str:
    """
    Convenience function to get fallback response as JSON string
    
    Args:
        agent_type: Type of agent
        scenario: Specific scenario
        context: Optional contextual information
    
    Returns:
        JSON string representation of the fallback response
    """
    response = get_fallback_response(agent_type, scenario, context)
    return json.dumps({
        "response": response.response,
        "confidence": response.confidence,
        "reasoning": response.reasoning,
        "timestamp": response.timestamp,
        "fallback_triggered": response.fallback_triggered,
        "agent_type": response.agent_type.value,
        "context": response.context
    }, indent=2)


if __name__ == "__main__":
    # Test the fallback response generator
    print("🧪 Testing Fallback Response Generator...")
    
    # Test different agent types and scenarios
    test_cases = [
        ("hvac", "temperature_control", {"temperature": 25.5}),
        ("power", "power_monitoring", {"load": 80}),
        ("security", "threat_assessment", {"event_type": "suspicious_activity"}),
        ("network", "traffic_analysis", {"segment": "core"}),
        ("coordinator", "facility_coordination", {"status": "degraded"})
    ]
    
    for agent_type, scenario, context in test_cases:
        response = get_fallback_response(agent_type, scenario, context)
        print(f"\n📋 {agent_type.upper()} - {scenario}:")
        print(f"Response: {response.response}")
        print(f"Confidence: {response.confidence}")
        print(f"Reasoning: {response.reasoning}")
    
    # Test performance report
    print(f"\n📊 Performance Report:")
    print(json.dumps(fallback_generator.get_performance_report(), indent=2))
    
    # Test JSON output
    print(f"\n📄 JSON Output Example:")
    json_response = get_fallback_response_json("hvac", "cooling_decision")
    print(json_response)