#!/usr/bin/env python3
"""
Quick script to fix all agents with async CrewAI integration
"""
import os
import re

def update_agent_file(filepath, agent_name, agent_type):
    """Update an agent file with async CrewAI integration"""
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Update imports
    old_imports = """import json
import asyncio
import threading
import yaml
from pathlib import Path
from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from intellicenter.core.event_bus import EventBus
from intellicenter.llm.llm_config import get_llm
from langchain_community.llms import Ollama"""

    new_imports = """import json
import asyncio
import yaml
from pathlib import Path
from crewai.tools import BaseTool
from intellicenter.core.event_bus import EventBus
from intellicenter.core.async_crew import AsyncCrewAI, create_optimized_crew, llm_manager"""

    content = content.replace(old_imports, new_imports)
    
    # Update _load_config method
    old_config_pattern = r'def _load_config\(self, file_name: str\):\s*config_path = Path\(f"intellicenter/config/\{file_name\}"\)\s*if config_path\.exists\(\):\s*with open\(config_path, "r"\) as file:\s*return yaml\.safe_load\(file\)\s*if "agents" in file_name:\s*return \{[^}]+\}\s*return \{\}'
    
    new_config = f'''def _load_config(self, file_name: str):
        # Try optimized config first
        optimized_path = Path(f"intellicenter/config/optimized_{{file_name}}")
        if optimized_path.exists():
            with open(optimized_path, "r") as file:
                return yaml.safe_load(file)
                
        # Fallback to regular config
        config_path = Path(f"intellicenter/config/{{file_name}}")
        if config_path.exists():
            with open(config_path, "r") as file:
                return yaml.safe_load(file)
                
        # Default fallback
        if "agents" in file_name:
            return {{"{agent_name}": {{
                "role": "{agent_name.replace('_', ' ').title()}", 
                "goal": "Optimize {agent_type} operations", 
                "backstory": "Expert {agent_type} specialist",
                "max_execution_time": 30
            }}}}
        return {{}}'''
    
    content = re.sub(old_config_pattern, new_config, content, flags=re.DOTALL)
    
    # Update _setup_crew method - this is more complex, so let's do a simple replacement
    if "_setup_crew" in content:
        # Find the _setup_crew method and replace it
        setup_pattern = r'def _setup_crew\(self\):.*?return Crew\([^}]+\)'
        
        new_setup = f'''def _setup_crew(self):
        """Setup optimized CrewAI crew for {agent_name.replace('_', ' ').title()} operations"""
        tools = []  # Add tools here
        
        crew = create_optimized_crew(
            agent_config=self.agents_config['{agent_name}'],
            task_config=self.tasks_config.get('{agent_type}_analysis', {{}}) or self.tasks_config.get('analysis', {{}}),
            agent_type="{agent_type}",
            tools=tools
        )
        
        # Wrap in async handler
        return AsyncCrewAI(crew, "{agent_name.replace('_', ' ').title()}")'''
        
        content = re.sub(setup_pattern, new_setup, content, flags=re.DOTALL)
    
    # Write back
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated {filepath}")

def main():
    """Update all agent files"""
    agents = [
        ('intellicenter/agents/network_agent.py', 'network_specialist', 'network'),
        ('intellicenter/agents/coordinator_agent.py', 'facility_coordinator', 'coordinator'),
    ]
    
    for filepath, agent_name, agent_type in agents:
        if os.path.exists(filepath):
            try:
                update_agent_file(filepath, agent_name, agent_type)
            except Exception as e:
                print(f"❌ Error updating {filepath}: {e}")
        else:
            print(f"⚠️  File not found: {filepath}")

if __name__ == "__main__":
    main()