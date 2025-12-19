import React from 'react';
import './ConnectionStatus.css';

interface ConnectionStatusProps {
  connectionStatus: {
    isConnected: boolean;
    isReconnecting: boolean;
    reconnectAttempts: number;
    lastError?: string;
    usingFallback: boolean;
  };
}

const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ connectionStatus }) => {
  const {
    isConnected,
    isReconnecting,
    reconnectAttempts,
    lastError,
    usingFallback
  } = connectionStatus;

  const getStatusInfo = () => {
    if (isConnected && !usingFallback) {
      return {
        status: 'connected',
        label: 'Connected',
        icon: '●',
        className: 'connection-status--connected'
      };
    }
    
    if (isReconnecting) {
      return {
        status: 'reconnecting',
        label: `Reconnecting (${reconnectAttempts}/10)`,
        icon: '◐',
        className: 'connection-status--reconnecting'
      };
    }
    
    if (usingFallback) {
      return {
        status: 'fallback',
        label: 'Using Fallback',
        icon: '◑',
        className: 'connection-status--fallback'
      };
    }
    
    return {
      status: 'disconnected',
      label: 'Disconnected',
      icon: '○',
      className: 'connection-status--disconnected'
    };
  };

  const statusInfo = getStatusInfo();

  return (
    <div className={`connection-status ${statusInfo.className}`}>
      <div className="connection-status__indicator">
        <span className="connection-status__icon" aria-hidden="true">
          {statusInfo.icon}
        </span>
        <span className="connection-status__label">
          {statusInfo.label}
        </span>
      </div>
      
      {isReconnecting && (
        <div className="connection-status__details">
          <div className="connection-status__progress">
            <div className="connection-status__progress-bar">
              <div 
                className="connection-status__progress-fill"
                style={{ width: `${(reconnectAttempts / 10) * 100}%` }}
              />
            </div>
          </div>
        </div>
      )}
      
      {lastError && !isConnected && !isReconnecting && (
        <div className="connection-status__error">
          <span className="connection-status__error-icon" aria-hidden="true">⚠</span>
          <span className="connection-status__error-message">{lastError}</span>
        </div>
      )}
      
      {usingFallback && (
        <div className="connection-status__fallback-info">
          <span className="connection-status__fallback-icon" aria-hidden="true">🔄</span>
          <span className="connection-status__fallback-message">
            Polling for updates
          </span>
        </div>
      )}
    </div>
  );
};

export default ConnectionStatus;