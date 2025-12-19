import React, { useState, useEffect } from 'react';
import './AgentStatus.css';

interface Agent {
  name: string;
  status: 'idle' | 'active' | 'warning' | 'error';
}

interface AgentStatusProps {
  agents: Agent[];
  messages?: any[];
}

const AgentStatus: React.FC<AgentStatusProps> = ({ agents, messages = [] }) => {
  const [animatedAgents, setAnimatedAgents] = useState<Record<string, 'idle' | 'active' | 'warning' | 'error'>>({});

  // Process messages to update agent status with animations
  useEffect(() => {
    const newAnimatedAgents: Record<string, 'idle' | 'active' | 'warning' | 'error'> = {};
    
    messages.forEach((message) => {
      const agentName = message.type?.split('.')[0];
      if (!agentName || !['hvac', 'power', 'security', 'network'].includes(agentName)) return;
      
      // Update status based on message
      if (message.type === 'hvac.status' || message.type === 'power.status' ||
          message.type === 'security.status' || message.type === 'network.status') {
        if (message.payload?.state && ['idle', 'active', 'warning', 'error'].includes(message.payload.state)) {
          newAnimatedAgents[agentName] = message.payload.state;
        }
      }
      
      // Handle coordination and scenario events - set to active temporarily
      if (message.type?.startsWith('coordination.') || message.type?.startsWith('scenario.')) {
        if (message.payload?.agents?.includes(agentName)) {
          newAnimatedAgents[agentName] = 'active';
          
          // Reset to idle after 2 seconds
          setTimeout(() => {
            setAnimatedAgents(prev => {
              const updated = { ...prev };
              if (updated[agentName] === 'active') {
                updated[agentName] = 'idle';
              }
              return updated;
            });
          }, 2000);
        }
      }
      
      // Handle scenario completion - reset all to idle
      if (message.type === 'scenario.complete') {
        newAnimatedAgents.hvac = 'idle';
        newAnimatedAgents.power = 'idle';
        newAnimatedAgents.security = 'idle';
        newAnimatedAgents.network = 'idle';
      }
    });

    // Merge with existing agents
    agents.forEach(agent => {
      if (!newAnimatedAgents[agent.name]) {
        newAnimatedAgents[agent.name] = agent.status;
      }
    });

    setAnimatedAgents(newAnimatedAgents);
  }, [messages, agents]);

  // Get status display text
  const getStatusText = (status: string) => {
    const statusMap = {
      idle: 'Idle',
      active: 'Active',
      warning: 'Warning',
      error: 'Error',
    };
    return statusMap[status as keyof typeof statusMap] || status;
  };

  // Get status icon
  const getStatusIcon = (status: string) => {
    const icons = {
      idle: '○',
      active: '●',
      warning: '⚠',
      error: '✕',
    };
    return icons[status as keyof typeof icons] || '○';
  };

  return (
    <div className="agent-status-container">
      <h2>Agent Status</h2>
      {agents.length === 0 ? (
        <div className="no-agents">
          <p>No agents to display</p>
        </div>
      ) : (
        <div className="agents-grid">
          {agents.map((agent) => {
            const currentStatus = animatedAgents[agent.name] || agent.status;
          const statusClass = currentStatus.toLowerCase();
          
          return (
            <div
              key={agent.name}
              className={`agent-card ${statusClass}`}
              role="status"
              aria-label={`${agent.name} status: ${getStatusText(currentStatus)}`}
            >
              <div className="agent-header">
                <span className="agent-icon">{getStatusIcon(currentStatus)}</span>
                <h3>{agent.name.toUpperCase()}</h3>
              </div>
              <div className="agent-status">
                <span className="status-text">{getStatusText(currentStatus)}</span>
                <div className={`status-indicator ${statusClass}`}></div>
              </div>
              <div className="agent-details">
                <span className="last-update">Last updated: Just now</span>
              </div>
            </div>
          );
        })}
        </div>
      )}
    </div>
  );
};

export default AgentStatus;