import React, { useState, useEffect } from 'react';
import './FacilityLayout.css';

interface AgentStatus {
  hvac: 'idle' | 'active' | 'warning' | 'error';
  power: 'idle' | 'active' | 'warning' | 'error';
  security: 'idle' | 'active' | 'warning' | 'error';
  network: 'idle' | 'active' | 'warning' | 'error';
}

interface CoordinationEvent {
  type: 'coordination' | 'scenario';
  agents: string[];
  timestamp: number;
}

interface FacilityLayoutProps {
  messages?: any[];
}

const FacilityLayout: React.FC<FacilityLayoutProps> = ({ messages = [] }) => {
  const [agentStatus, setAgentStatus] = useState<AgentStatus>({
    hvac: 'idle',
    power: 'idle',
    security: 'idle',
    network: 'idle',
  });
  
  const [coordinationEvents, setCoordinationEvents] = useState<CoordinationEvent[]>([]);
  const [containerSize, setContainerSize] = useState({ width: 800, height: 600 });

  // Handle window resize for responsive sizing
  useEffect(() => {
    const handleResize = () => {
      const container = document.querySelector('.facility-layout svg');
      if (container) {
        const rect = container.getBoundingClientRect();
        setContainerSize({
          width: rect.width,
          height: rect.height,
        });
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Process messages to update agent status
  useEffect(() => {
    const newAgentStatus = { ...agentStatus };
    const newCoordinationEvents: CoordinationEvent[] = [];

    messages.forEach((message) => {
      const timestamp = message.timestamp || Date.now();
      
      // Handle agent status events
      if (message.type === 'hvac.status' || message.type === 'power.status' ||
          message.type === 'security.status' || message.type === 'network.status') {
        const agentType = message.type.split('.')[0] as keyof AgentStatus;
        if (message.payload?.state && ['idle', 'active', 'warning', 'error'].includes(message.payload.state)) {
          newAgentStatus[agentType] = message.payload.state;
        }
      }

      // Handle coordination events
      if (message.type?.startsWith('coordination.') || message.type?.startsWith('scenario.')) {
        const agents = message.payload?.agents || [];
        if (agents.length > 0) {
          newCoordinationEvents.push({
            type: message.type.startsWith('coordination.') ? 'coordination' : 'scenario',
            agents,
            timestamp,
          });
        }
      }

      // Handle scenario lifecycle events
      if (message.type === 'scenario.complete') {
        newAgentStatus.hvac = 'idle';
        newAgentStatus.power = 'idle';
        newAgentStatus.security = 'idle';
        newAgentStatus.network = 'idle';
      }
    });

    setAgentStatus(newAgentStatus);
    
    // Add new coordination events and remove old ones (keep last 5 seconds)
    setCoordinationEvents(prev => {
      const cutoff = Date.now() - 5000;
      const filtered = prev.filter(event => event.timestamp > cutoff);
      return [...filtered, ...newCoordinationEvents];
    });
  }, [messages]);

  // Get zone positions for SVG layout
  const getZonePosition = (zone: string) => {
    const positions = {
      hvac: { x: containerSize.width * 0.2, y: containerSize.height * 0.2 },
      power: { x: containerSize.width * 0.8, y: containerSize.height * 0.2 },
      security: { x: containerSize.width * 0.2, y: containerSize.height * 0.8 },
      network: { x: containerSize.width * 0.8, y: containerSize.height * 0.8 },
    };
    return positions[zone as keyof typeof positions];
  };

  // Get status color
  const getStatusColor = (status: string) => {
    const colors = {
      idle: '#6c757d',
      active: '#28a745',
      warning: '#ffc107',
      error: '#dc3545',
    };
    return colors[status as keyof typeof colors] || colors.idle;
  };

  // Get zone icon (simple SVG path)
  const getZoneIcon = (zone: string) => {
    const icons = {
      hvac: 'M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41',
      power: 'M13 10V3L4 14h7v7l9-11h-7z',
      security: 'M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z',
      network: 'M2 12h20M12 2l10 10-10 10L2 12z',
    };
    return icons[zone as keyof typeof icons] || '';
  };

  return (
    <div className="facility-layout">
      <h2>Facility Layout</h2>
      <div className="layout-container">
        <svg
          viewBox={`0 0 ${containerSize.width} ${containerSize.height}`}
          preserveAspectRatio="xMidYMid meet"
          className="facility-svg"
        >
          {/* Background grid */}
          <defs>
            <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
              <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#e0e0e0" strokeWidth="1"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
          
          {/* Connection lines for coordination events */}
          {coordinationEvents.map((event, index) => {
            if (event.agents.length < 2) return null;
            
            const pos1 = getZonePosition(event.agents[0]);
            const pos2 = getZonePosition(event.agents[1]);
            
            return (
              <line
                key={index}
                x1={pos1.x}
                y1={pos1.y}
                x2={pos2.x}
                y2={pos2.y}
                stroke="#007bff"
                strokeWidth="2"
                strokeDasharray="5,5"
                className="coordination-line"
                style={{
                  animation: 'coordinationPulse 1s ease-in-out',
                }}
              />
            );
          })}
          
          {/* Zone circles */}
          {(['hvac', 'power', 'security', 'network'] as const).map((zone) => {
            const pos = getZonePosition(zone);
            const status = agentStatus[zone];
            const color = getStatusColor(status);
            
            return (
              <g key={zone} className={`zone-group ${status}`}>
                {/* Zone circle */}
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r="60"
                  fill={status === 'active' ? `${color}20` : '#ffffff'}
                  stroke={color}
                  strokeWidth="3"
                  className={`zone-circle ${status}`}
                  style={{
                    animation: status === 'active' ? 'zonePulse 2s ease-in-out infinite' : 'none',
                  }}
                />
                
                {/* Zone icon */}
                <path
                  d={getZoneIcon(zone)}
                  transform={`translate(${pos.x - 12}, ${pos.y - 12}) scale(1.5)`}
                  fill={color}
                  stroke={color}
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                
                {/* Zone label */}
                <text
                  x={pos.x}
                  y={pos.y + 80}
                  textAnchor="middle"
                  className="zone-label"
                  fill="#333"
                  fontSize="14"
                  fontWeight="bold"
                >
                  {zone.toUpperCase()}
                </text>
                
                {/* Status indicator */}
                <circle
                  cx={pos.x + 45}
                  cy={pos.y - 45}
                  r="8"
                  fill={color}
                  className="status-indicator"
                  style={{
                    animation: status === 'active' ? 'statusPulse 1.5s ease-in-out infinite' : 'none',
                  }}
                />
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
};

export default FacilityLayout;