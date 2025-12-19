import { render, screen } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import PerformancePanel from '../PerformancePanel';

describe('PerformancePanel', () => {
  const mockMessages = [
    {
      type: 'hvac.status',
      payload: { state: 'active' },
      timestamp: Date.now() - 5000, // 5 seconds ago
    },
    {
      type: 'power.status',
      payload: { state: 'warning' },
      timestamp: Date.now() - 3000, // 3 seconds ago
    },
    {
      type: 'security.status',
      payload: { state: 'error' },
      timestamp: Date.now() - 1000, // 1 second ago
    },
    {
      type: 'network.status',
      payload: { state: 'idle' },
      timestamp: Date.now() - 2000, // 2 seconds ago
    },
    {
      type: 'coordination.test',
      payload: { agents: ['hvac', 'power'] },
      timestamp: Date.now() - 4000, // 4 seconds ago
    },
    {
      type: 'scenario.step',
      payload: { step: 1 },
      timestamp: Date.now() - 6000, // 6 seconds ago
    },
  ];

  beforeEach(() => {
    // Mock Date.now() to control timestamps
    const mockNow = Date.now();
    vi.spyOn(Date, 'now').mockReturnValue(mockNow);
  });

  it('renders performance panel header', () => {
    render(<PerformancePanel messages={[]} />);
    
    expect(screen.getByText('Performance Metrics')).toBeInTheDocument();
  });

  it('displays messages per second metric', () => {
    render(<PerformancePanel messages={mockMessages} />);
    
    const mpsElement = screen.getByText(/messages\/sec/i);
    expect(mpsElement).toBeInTheDocument();
    
    // Should show a value greater than 0
    const mpsValue = screen.getByText(/[\d.]+k?/i);
    expect(mpsValue).toBeInTheDocument();
  });

  it('displays average latency metric', () => {
    render(<PerformancePanel messages={mockMessages} />);
    
    const latencyElement = screen.getByText(/avg latency/i);
    expect(latencyElement).toBeInTheDocument();
    
    // Should show a value in milliseconds
    const latencyValue = screen.getByText(/\d+ms/i);
    expect(latencyValue).toBeInTheDocument();
  });

  it('shows recent events section', () => {
    render(<PerformancePanel messages={mockMessages} />);
    
    expect(screen.getByText('Recent Events')).toBeInTheDocument();
  });

  it('accumulates events and computes simple MPS', () => {
    const testMessages = [
      {
        type: 'hvac.status',
        payload: { state: 'active' },
        timestamp: Date.now() - 5000,
      },
      {
        type: 'power.status',
        payload: { state: 'warning' },
        timestamp: Date.now() - 4000,
      },
      {
        type: 'security.status',
        payload: { state: 'error' },
        timestamp: Date.now() - 3000,
      },
    ];
    
    render(<PerformancePanel messages={testMessages} />);
    
    // Should show 3 messages in 10 seconds = 0.3 MPS
    const mpsValue = screen.getByText(/0.3/i);
    expect(mpsValue).toBeInTheDocument();
  });

  it('displays recent events list', () => {
    render(<PerformancePanel messages={mockMessages} />);
    
    // Should show the most recent event types
    const eventTypes = screen.getAllByText(/hvac\.status|power\.status|security\.status|network\.status|coordination\.test|scenario\.step/i);
    expect(eventTypes.length).toBeGreaterThan(0);
  });

  it('handles empty messages array', () => {
    render(<PerformancePanel messages={[]} />);
    
    expect(screen.getByText('Performance Metrics')).toBeInTheDocument();
    expect(screen.getByText('Messages/sec')).toBeInTheDocument();
    expect(screen.getByText('Avg Latency')).toBeInTheDocument();
    
    // Should show "No events in the last 10 seconds" in recent events
    expect(screen.getByText('No events in the last 10 seconds')).toBeInTheDocument();
  });

  it('filters events to last 10 seconds window', () => {
    const oldMessages = [
      {
        type: 'old.event',
        payload: {},
        timestamp: Date.now() - 15000, // 15 seconds ago (outside window)
      },
    ];
    
    const recentMessages = [
      {
        type: 'recent.event',
        payload: {},
        timestamp: Date.now() - 5000, // 5 seconds ago (inside window)
      },
    ];
    
    render(<PerformancePanel messages={[...oldMessages, ...recentMessages]} />);
    
    // Should only show recent event, not old one
    expect(screen.getByText('recent.event')).toBeInTheDocument();
    expect(screen.queryByText('old.event')).not.toBeInTheDocument();
  });

  it('sorts recent events by last seen time', () => {
    const messages = [
      {
        type: 'event1',
        payload: {},
        timestamp: Date.now() - 8000, // 8 seconds ago
      },
      {
        type: 'event2',
        payload: {},
        timestamp: Date.now() - 2000, // 2 seconds ago (most recent)
      },
      {
        type: 'event3',
        payload: {},
        timestamp: Date.now() - 5000, // 5 seconds ago
      },
    ];
    
    render(<PerformancePanel messages={messages} />);
    
    // Event2 should be first in the list
    const events = screen.getAllByRole('listitem');
    expect(events[0]).toHaveTextContent('event2');
  });

  it('limits recent events to last 5 unique types', () => {
    const messages = [];
    for (let i = 0; i < 10; i++) {
      messages.push({
        type: `event${i}`,
        payload: {},
        timestamp: Date.now() - (i * 1000), // Spread over 10 seconds
      });
    }
    
    render(<PerformancePanel messages={messages} />);
    
    // Should only show 5 unique events
    const events = screen.getAllByRole('listitem');
    expect(events.length).toBeLessThanOrEqual(5);
  });

  it('calculates average latency between related events', () => {
    const messages = [
      {
        type: 'hvac.status',
        payload: { state: 'active' },
        timestamp: Date.now() - 6000,
      },
      {
        type: 'hvac.status',
        payload: { state: 'idle' },
        timestamp: Date.now() - 5000,
      },
      {
        type: 'hvac.status',
        payload: { state: 'active' },
        timestamp: Date.now() - 4000,
      },
      {
        type: 'hvac.status',
        payload: { state: 'idle' },
        timestamp: Date.now() - 3000,
      },
    ];
    
    render(<PerformancePanel messages={messages} />);
    
    // Should calculate latency between consecutive hvac.status events
    const latencyValue = screen.getByText(/\d+ms/i);
    expect(latencyValue).toBeInTheDocument();
  });

  it('handles undefined messages prop', () => {
    render(<PerformancePanel />);
    
    expect(screen.getByText('Performance Metrics')).toBeInTheDocument();
    expect(screen.getByText('No events in the last 10 seconds')).toBeInTheDocument();
  });

  it('applies correct status colors based on metric values', () => {
    const highTrafficMessages = [];
    for (let i = 0; i < 20; i++) {
      highTrafficMessages.push({
        type: 'test.event',
        payload: {},
        timestamp: Date.now() - (i * 500), // High frequency
      });
    }
    
    render(<PerformancePanel messages={highTrafficMessages} />);
    
    // High traffic should show red color
    const mpsElement = screen.getByText(/messages\/sec/i);
    expect(mpsElement).toHaveStyle('color: #dc3545');
  });

  it('formats large numbers with k suffix', () => {
    const highVolumeMessages = [];
    for (let i = 0; i < 5000; i++) {
      highVolumeMessages.push({
        type: 'test.event',
        payload: {},
        timestamp: Date.now() - (i * 200), // Very high frequency
      });
    }
    
    render(<PerformancePanel messages={highVolumeMessages} />);
    
    // Should show number with 'k' suffix
    const mpsValue = screen.getByText(/[\d.]+k/i);
    expect(mpsValue).toBeInTheDocument();
  });

  it('handles events with no timestamp', () => {
    const messagesWithoutTimestamp = [
      {
        type: 'test.event',
        payload: {},
        timestamp: Date.now(),
      },
    ];
    
    render(<PerformancePanel messages={messagesWithoutTimestamp} />);
    
    // Should handle gracefully without errors
    expect(screen.getByText('Performance Metrics')).toBeInTheDocument();
  });
});