import React, { useState, useEffect, useCallback } from 'react';
import './PerformancePanel.css';

interface EventData {
  timestamp: number;
  type: string;
  payload?: any;
  source?: string;
}

interface PerformanceMetrics {
  messagesPerSecond: number;
  averageLatency: number;
  recentEvents: Array<{
    type: string;
    count: number;
    lastSeen: number;
  }>;
}

interface PerformancePanelProps {
  messages?: EventData[];
}

const PerformancePanel: React.FC<PerformancePanelProps> = ({ messages = [] }) => {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    messagesPerSecond: 0,
    averageLatency: 0,
    recentEvents: [],
  });

  // Calculate performance metrics
  const calculateMetrics = useCallback((events: EventData[]) => {
    const now = Date.now();
    const windowSize = 10000; // 10 seconds window
    const recentWindow = now - windowSize;
    
    // Filter events in the last 10 seconds
    const recentEvents = events.filter(event => event.timestamp >= recentWindow);
    
    // Calculate messages per second
    const messagesPerSecond = recentEvents.length / (windowSize / 1000);
    
    // Calculate average latency (time between consecutive events of same type)
    const latencyMap = new Map<string, number[]>();
    let totalLatency = 0;
    let latencyCount = 0;
    
    // Sort events by timestamp
    const sortedEvents = [...recentEvents].sort((a, b) => a.timestamp - b.timestamp);
    
    for (let i = 1; i < sortedEvents.length; i++) {
      const prevEvent = sortedEvents[i - 1];
      const currEvent = sortedEvents[i];
      
      if (prevEvent.type === currEvent.type) {
        const latency = currEvent.timestamp - prevEvent.timestamp;
        latencyMap.set(currEvent.type, [...(latencyMap.get(currEvent.type) || []), latency]);
        totalLatency += latency;
        latencyCount++;
      }
    }
    
    const averageLatency = latencyCount > 0 ? totalLatency / latencyCount : 0;
    
    // Calculate recent event types (last 5 unique types)
    const eventTypes = new Map<string, { count: number; lastSeen: number }>();
    
    events.forEach(event => {
      if (event.timestamp >= recentWindow) {
        const existing = eventTypes.get(event.type) || { count: 0, lastSeen: 0 };
        eventTypes.set(event.type, {
          count: existing.count + 1,
          lastSeen: Math.max(existing.lastSeen, event.timestamp),
        });
      }
    });
    
    const recentEventsArray = Array.from(eventTypes.entries())
      .map(([type, data]) => ({ type, ...data }))
      .sort((a, b) => b.lastSeen - a.lastSeen)
      .slice(0, 5);
    
    return {
      messagesPerSecond,
      averageLatency,
      recentEvents: recentEventsArray,
    };
  }, []);

  // Update metrics when messages change
  useEffect(() => {
    const newMetrics = calculateMetrics(messages);
    setMetrics(newMetrics);
  }, [messages, calculateMetrics]);

  // Format numbers for display
  const formatNumber = (num: number): string => {
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'k';
    }
    return num.toFixed(1);
  };

  // Format time ago
  const formatTimeAgo = (timestamp: number): string => {
    const now = Date.now();
    const diff = now - timestamp;
    
    if (diff < 1000) return 'just now';
    if (diff < 60000) return Math.floor(diff / 1000) + 's ago';
    if (diff < 3600000) return Math.floor(diff / 60000) + 'm ago';
    return Math.floor(diff / 3600000) + 'h ago';
  };

  // Get status color based on value
  const getStatusColor = (value: number, type: 'mps' | 'latency'): string => {
    if (type === 'mps') {
      if (value < 1) return '#28a745'; // Green - low traffic
      if (value < 5) return '#ffc107'; // Yellow - moderate traffic
      return '#dc3545'; // Red - high traffic
    } else {
      if (value < 100) return '#28a745'; // Green - low latency
      if (value < 500) return '#ffc107'; // Yellow - moderate latency
      return '#dc3545'; // Red - high latency
    }
  };

  return (
    <div className="performance-panel">
      <h2>Performance Metrics</h2>
      
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-title">Messages/sec</span>
            <span 
              className="metric-status" 
              style={{ color: getStatusColor(metrics.messagesPerSecond, 'mps') }}
            >
              {formatNumber(metrics.messagesPerSecond)}
            </span>
          </div>
          <div className="metric-bar">
            <div 
              className="metric-fill" 
              style={{ 
                width: `${Math.min(metrics.messagesPerSecond * 10, 100)}%`,
                backgroundColor: getStatusColor(metrics.messagesPerSecond, 'mps')
              }}
            ></div>
          </div>
          <div className="metric-description">
            Last 10 seconds
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-title">Avg Latency</span>
            <span 
              className="metric-status" 
              style={{ color: getStatusColor(metrics.averageLatency, 'latency') }}
            >
              {metrics.averageLatency.toFixed(0)}ms
            </span>
          </div>
          <div className="metric-bar">
            <div 
              className="metric-fill" 
              style={{ 
                width: `${Math.min(metrics.averageLatency / 10, 100)}%`,
                backgroundColor: getStatusColor(metrics.averageLatency, 'latency')
              }}
            ></div>
          </div>
          <div className="metric-description">
            Between related events
          </div>
        </div>
      </div>

      <div className="events-section">
        <h3>Recent Events</h3>
        <div className="events-list">
          {metrics.recentEvents.length > 0 ? (
            metrics.recentEvents.map((event, index) => (
              <div key={index} className="event-item">
                <span className="event-type">{event.type}</span>
                <span className="event-count">{event.count}</span>
                <span className="event-time">{formatTimeAgo(event.lastSeen)}</span>
              </div>
            ))
          ) : (
            <div className="no-events">
              No events in the last 10 seconds
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PerformancePanel;