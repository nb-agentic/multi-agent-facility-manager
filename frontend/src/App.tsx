import { useState, useEffect } from 'react';
import useWebSocket from './hooks/useWebSocket';
import FacilityLayout from './components/FacilityLayout';
import AgentStatus from './components/AgentStatus';
import PerformancePanel from './components/PerformancePanel';
import EventLog from './components/EventLog';
import ConnectionStatus from './components/ConnectionStatus';
import './App.css';

interface Agent {
  name: string;
  status: 'idle' | 'active' | 'warning' | 'error';
}

function App() {
  const { messages, connectionStatus } = useWebSocket('ws://localhost:8000/ws');
  const [agents, setAgents] = useState<Agent[]>([
    { name: 'HVAC', status: 'idle' },
    { name: 'Power', status: 'idle' },
    { name: 'Security', status: 'idle' },
    { name: 'Network', status: 'idle' },
    { name: 'Coordinator', status: 'idle' },
  ]);

  useEffect(() => {
    // This is a mock update based on incoming messages.
    // In a real application, you would parse the message and update the specific agent.
    if (messages.length > 0) {
      const updatedAgents = agents.map(agent => ({ ...agent, status: 'active' as 'active' }));
      setAgents(updatedAgents);
    }
  }, [messages]);

  return (
    <div className="App">
      <header className="App-header">
        <h1>IntelliCenter Dashboard</h1>
        <ConnectionStatus connectionStatus={connectionStatus} />
      </header>
      <div className="dashboard-container">
        <div className="main-content">
          <FacilityLayout messages={messages} />
        </div>
        <div className="sidebar">
          <AgentStatus agents={agents} messages={messages} />
          <PerformancePanel messages={messages} />
          <EventLog events={messages} />
        </div>
      </div>
    </div>
  );
}

export default App;
