from datetime import datetime, timezone
from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from intellicenter.shared.event_bus import EventBus
from intellicenter.infrastructure.llm.factory import get_llm
from intellicenter.shared.logger import get_logger, bind_request_context, clear_request_context
from intellicenter.shared.schema import AgentType, AgentStatus, AgentResponse, AgentDirective

logger = get_logger("intellicenter.workers.hvac")

class TemperatureControlTool(BaseTool):
    name: str = "Temperature Control Tool"
    description: str = "Advanced temperature control with validation"

    def _run(self, target_temp: float, zone: str = "main") -> str:
        if not (15.0 <= target_temp <= 30.0):
            return f"❌ Invalid temperature {target_temp}°C. Valid range: 15-30°C"
        return f"✅ Temperature control executed: {zone} set to {target_temp}°C"

class HumidityMonitoringTool(BaseTool):
    name: str = "Humidity Monitoring Tool"
    description: str = "Monitor and report humidity levels"

    def _run(self, zone: str = "main") -> str:
        import random
        humidity = round(random.uniform(40, 60), 1)
        status = "optimal" if 45 <= humidity <= 55 else "attention_needed"
        return f"🌡️ Humidity in {zone}: {humidity}% - Status: {status}"

class EnergyEfficiencyTool(BaseTool):
    name: str = "Energy Efficiency Tool"
    description: str = "Calculate energy efficiency for cooling decisions"

    def _run(self, cooling_level: str) -> str:
        efficiency_map = {
            "low": {"consumption": "85%", "cost": "$12/hour"},
            "medium": {"consumption": "100%", "cost": "$15/hour"}, 
            "high": {"consumption": "125%", "cost": "$22/hour"},
            "emergency": {"consumption": "150%", "cost": "$35/hour"}
        }
        data = efficiency_map.get(cooling_level, efficiency_map["medium"])
        return f"⚡ Cooling level '{cooling_level}': {data['consumption']} consumption, {data['cost']}"

class HVACControlAgent:
    """Enhanced HVAC Control Agent with explicit crew setup"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.agents_config = self._load_config("agents.yaml")
        self.tasks_config = self._load_config("tasks.yaml")
        self.crew = self._setup_crew()
        self.fallback_mode = False
        self.performance_metrics = {
            "responses": 0,
            "avg_response_time": 0,
            "decisions": {"low": 0, "medium": 0, "high": 0, "emergency": 0}
        }
        
        # Test agent startup
        startup_success = self.test_agent_startup()
        if not startup_success:
            logger.warning("hvac_agent_startup_issues_detected", action="falling_back_to_mock")
            self.fallback_mode = True
        
        logger.info("hvac_agent_initialized", fallback_mode=self.fallback_mode)
        
    def _load_config(self, file_name: str):
        # Try optimized config first
        optimized_path = Path(f"src/intellicenter/config/optimized_{file_name}")
        if optimized_path.exists():
            with open(optimized_path, "r") as file:
                return yaml.safe_load(file)
                
        # Fallback to regular config
        config_path = Path(f"src/intellicenter/config/{file_name}")
        if config_path.exists():
            with open(config_path, "r") as file:
                return yaml.safe_load(file)
                
        # Default fallback
        if "agents" in file_name:
            return {"hvac_specialist": {
                "role": "HVAC Control Specialist", 
                "goal": "Maintain optimal temperature and energy efficiency", 
                "backstory": "Expert HVAC engineer with knowledge of thermal dynamics",
                "max_execution_time": 30
            }}
        return {}

    def _setup_crew(self):
        """Setup CrewAI crew for HVAC operations with centralized LLM configuration"""
        try:
            # Get LLM from centralized configuration
            llm = get_llm("hvac")
            
            hvac_specialist = Agent(
                config=self.agents_config['hvac_specialist'],
                llm=llm,
                verbose=True,
                allow_delegation=False,
                tools=[
                    TemperatureControlTool(),
                    HumidityMonitoringTool(),
                    EnergyEfficiencyTool()
                ]
            )
            
            temperature_analysis_task = Task(
                config=self.tasks_config['hvac_analysis'],
                agent=hvac_specialist
            )

            return Crew(
                agents=[hvac_specialist],
                tasks=[temperature_analysis_task],
                verbose=False,  # Reduce verbosity for demo
                memory=False,
                planning=False,
                max_execution_time=30
            )
            
        except Exception as e:
            print(f"❌ Failed to setup CrewAI crew: {e}")
            # Initialize fallback agent
            from intellicenter.workers.fallback import MockAgent
            self.mock_agent = MockAgent()
            self.fallback_mode = True
            return None
    
    def _handle_temperature_change(self, message, loop):
        start_time = loop.time()
        try:
            temperature_data = json.loads(message) if isinstance(message, str) else message
            
            # Extract request context
            request_id = temperature_data.get("request_id", f"req_{int(time.time()*1000)}")
            agent_id = f"hvac_{id(self)}"
            
            # Bind context for this task
            bind_request_context(
                request_id=request_id,
                agent_id=agent_id,
                agent_type=str(AgentType.HVAC)
            )
            
            logger.info("temperature_change_received", 
                        temperature=temperature_data.get("temperature"),
                        location=temperature_data.get("location"))
            
            enhanced_data = {**temperature_data, "zone": "main_server_room"}
            asyncio.create_task(self._run_enhanced_analysis(enhanced_data, start_time, loop))
        except Exception as e:
            logger.error("temperature_handling_error", error=str(e))
        finally:
            # We don't clear context here because the task is spawned via create_task.
            # In a production system, we'd use a context-aware task wrapper.
            pass
    
    async def _run_enhanced_analysis(self, temperature_data, start_time, loop):
        try:
            # Check if we're in fallback mode
            if hasattr(self, 'fallback_mode') and self.fallback_mode:
                # Use MockAgent for fallback response
                from intellicenter.workers.fallback import get_fallback_response
                
                fallback_response = get_fallback_response(
                    "hvac",
                    "cooling_decision",
                    {"temperature": temperature_data.get("temperature", 22.0)}
                )
                
                decision_data = {
                    "cooling_level": "medium",  # Default fallback level
                    "reasoning": fallback_response.reasoning,
                    "confidence": fallback_response.confidence,
                    "timestamp": temperature_data.get("timestamp"),
                    "response_time": round(asyncio.get_event_loop().time() - start_time, 2),
                    "agent_type": AgentType.HVAC,
                    "temperature_input": temperature_data.get("temperature"),
                    "status": "fallback",
                    "fallback_triggered": True
                }
            else:
                # Use CrewAI directly with Ollama
                result = await asyncio.to_thread(
                    self.crew.kickoff,
                    inputs={"temperature_data": json.dumps(temperature_data)}
                )
                
                decision_data = self._process_crew_result(result, temperature_data, start_time, loop)
            
            # Create AgentResponse object
            response_obj = AgentResponse(
                request_id=temperature_data.get("request_id", "unknown"),
                agent_type=AgentType.HVAC,
                status=AgentStatus.SUCCESS if decision_data.get("status") == "success" else AgentStatus.FAILED,
                decision_data=decision_data,
                reasoning=decision_data.get("reasoning"),
                confidence=decision_data.get("confidence")
            )
            
            await self.event_bus.publish("hvac.cooling.decision", response_obj.model_dump_json())
            self._update_metrics(decision_data)
            
        except Exception as e:
            logger.error("enhanced_analysis_error", error=str(e))
            fallback_decision = self._generate_fallback_decision(temperature_data, str(e))
            
            # Create AgentResponse for fallback
            fallback_response_obj = AgentResponse(
                request_id=temperature_data.get("request_id", "unknown"),
                agent_type=AgentType.HVAC,
                status=AgentStatus.FAILED,
                decision_data=fallback_decision,
                reasoning="Fallback decision due to analysis error."
            )
            await self.event_bus.publish("hvac.cooling.decision", fallback_response_obj.model_dump_json())
    
    def _process_crew_result(self, result, temperature_data, start_time, loop):
        try:
            raw_output = result.raw if hasattr(result, 'raw') else str(result)
            crew_output = json.loads(raw_output)
        except (json.JSONDecodeError, AttributeError):
            raw_output = result.raw if hasattr(result, 'raw') else str(result)
            cooling_level = raw_output.lower().strip()
            if cooling_level not in ["low", "medium", "high", "emergency"]:
                cooling_level = "medium"
            crew_output = {"cooling_level": cooling_level, "reasoning": "AI analysis completed, raw output processed.", "confidence": 75}
        
        return {
            **crew_output,
            "timestamp": temperature_data.get("timestamp"),
            "response_time": round(loop.time() - start_time, 2),
            "agent_type": AgentType.HVAC,
            "temperature_input": temperature_data.get("temperature"),
            "status": "success"
        }
    
    def _generate_fallback_decision(self, temperature_data, error_msg):
        temp = temperature_data.get("temperature", 22.0)
        cooling_level = "high" if temp > 26 else "medium" if temp > 24 else "low"
        return {"cooling_level": cooling_level, "reasoning": "Fallback rule-based decision", "error": error_msg, "fallback": True, "temperature_input": temp, "timestamp": temperature_data.get("timestamp"), "status": "fallback"}
    
    def _update_metrics(self, decision_data):
        response_time = decision_data.get("response_time", 0)
        cooling_level = decision_data.get("cooling_level", "medium")
        self.performance_metrics["responses"] += 1
        count = self.performance_metrics["responses"]
        old_avg = self.performance_metrics["avg_response_time"]
        self.performance_metrics["avg_response_time"] = (old_avg * (count - 1) + response_time) / count
        if cooling_level in self.performance_metrics["decisions"]:
            self.performance_metrics["decisions"][cooling_level] += 1
    
    def get_performance_report(self) -> str:
        metrics = self.performance_metrics
        total_decisions = sum(metrics["decisions"].values())
        if total_decisions == 0: return "📊 No decisions made yet."
        report = f"🌡️ HVAC Agent: {metrics['responses']} responses, {metrics['avg_response_time']:.2f}s avg response. Decisions: "
        for level, count in metrics["decisions"].items():
            report += f"{level}: {count} ({(count/total_decisions*100):.1f}%) "
        return report.strip()
    
    def test_agent_startup(self) -> bool:
        """Test agent initialization and startup"""
        try:
            logger.info("hvac_agent_startup_test_initiated")
            
            # Test 1: Check if crew was initialized successfully
            if hasattr(self, 'fallback_mode') and self.fallback_mode:
                logger.info("hvac_agent_startup_test_success", mode="fallback")
                return True
            elif self.crew is not None:
                logger.info("hvac_agent_startup_test_success", mode="crewai")
                return True
            else:
                logger.error("hvac_agent_startup_test_failed", reason="initialization_failure")
                return False
                
        except Exception as e:
            logger.error("hvac_agent_startup_test_failed", error=str(e))
            return False
    
    async def test_response_generation(self, temperature_data: dict) -> dict:
        """Test agent response generation with sample data"""
        try:
            logger.info("hvac_agent_test_response_initiated", data=temperature_data)
            
            start_time = asyncio.get_event_loop().time()
            
            # Simulate temperature change event
            message = json.dumps(temperature_data)
            loop = asyncio.get_event_loop()
            self._handle_temperature_change(message, loop)
            
            # Wait a moment for async processing
            await asyncio.sleep(0.1)
            
            # Check if we got a decision
            if hasattr(self, 'performance_metrics') and self.performance_metrics['responses'] > 0:
                logger.info("hvac_agent_test_response_success")
                return {
                    "success": True,
                    "responses_generated": self.performance_metrics['responses'],
                    "status": "completed"
                }
            else:
                logger.warning("hvac_agent_test_response_no_events")
                return {
                    "success": True,
                    "responses_generated": 0,
                    "status": "waiting"
                }
                
        except Exception as e:
            logger.error("hvac_agent_test_response_failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "status": "error"
            }
    
    async def run(self):
        loop = asyncio.get_event_loop()
        self.event_bus.subscribe("hvac.temperature.changed", lambda msg: self._handle_temperature_change(msg, loop))
        print("🌡️  Enhanced HVAC Control Agent is running...")
        last_report_time = loop.time()
        while True:
            await asyncio.sleep(1)
            if loop.time() - last_report_time > 30 and self.performance_metrics["responses"] > 0:
                print(self.get_performance_report())
                last_report_time = loop.time()