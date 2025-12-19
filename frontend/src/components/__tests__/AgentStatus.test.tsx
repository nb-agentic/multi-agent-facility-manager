import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import AgentStatus from '../AgentStatus';

describe('AgentStatus', () => {
  const mockAgents = [
    { name: 'hvac', status: 'idle' as const },
    { name: 'power', status: 'active' as const },
    { name: 'security', status: 'warning' as const },
    { name: 'network', status: 'error' as const },
  ];

  const mockMessages = [
    {
      type: 'hvac.status',
      payload: { state: 'active' },
      timestamp: Date.now(),
    },
    {
      type: 'power.status',
      payload: { state: 'warning' },
      timestamp: Date.now(),
    },
    {
      type: 'coordination.test',
      payload: { agents: ['hvac', 'security'] },
      timestamp: Date.now(),
    },
    {
      type: 'scenario.complete',
      payload: {},
      timestamp: Date.now(),
    },
  ];

  it('renders agent status with props', () => {
    render(<AgentStatus agents={mockAgents} />);
    
    expect(screen.getByText('Agent Status')).toBeInTheDocument();
    expect(screen.getByText('HVAC')).toBeInTheDocument();
    expect(screen.getByText('POWER')).toBeInTheDocument();
    expect(screen.getByText('SECURITY')).toBeInTheDocument();
    expect(screen.getByText('NETWORK')).toBeInTheDocument();
  });

  it('applies animation classes based on status prop', () => {
    render(<AgentStatus agents={mockAgents} />);
    
    // Check that each agent card has the correct status class
    const hvacCard = screen.getByText('HVAC').closest('.agent-card');
    const powerCard = screen.getByText('POWER').closest('.agent-card');
    const securityCard = screen.getByText('SECURITY').closest('.agent-card');
    const networkCard = screen.getByText('NETWORK').closest('.agent-card');
    
    expect(hvacCard).toHaveClass('idle');
    expect(powerCard).toHaveClass('active');
    expect(securityCard).toHaveClass('warning');
    expect(networkCard).toHaveClass('error');
  });

  it('updates status based on messages', () => {
    const { rerender } = render(<AgentStatus agents={mockAgents} messages={[]} />);
    
    // Initially HVAC should be idle
    let hvacCard = screen.getByText('HVAC').closest('.agent-card');
    expect(hvacCard).toHaveClass('idle');
    
    // Render with HVAC active message
    rerender(<AgentStatus agents={mockAgents} messages={mockMessages} />);
    
    // HVAC should now be active
    hvacCard = screen.getByText('HVAC').closest('.agent-card');
    expect(hvacCard).toHaveClass('active');
  });

  it('handles coordination events by setting agents to active temporarily', () => {
    const coordinationMessages = [
      {
        type: 'coordination.test',
        payload: { agents: ['hvac', 'security'] },
        timestamp: Date.now(),
      },
    ];
    
    render(<AgentStatus agents={mockAgents} messages={coordinationMessages} />);
    
    // HVAC and Security should be active due to coordination
    const hvacCard = screen.getByText('HVAC').closest('.agent-card');
    const securityCard = screen.getByText('SECURITY').closest('.agent-card');
    
    expect(hvacCard).toHaveClass('active');
    expect(securityCard).toHaveClass('active');
  });

  it('handles scenario.complete by resetting all agents to idle', () => {
    const { rerender } = render(<AgentStatus agents={mockAgents} messages={mockMessages} />);
    
    // Initially some agents should have non-idle status
    let hvacCard = screen.getByText('HVAC').closest('.agent-card');
    expect(hvacCard).toHaveClass('active');
    
    // Render with scenario complete
    rerender(<AgentStatus agents={mockAgents} messages={[...mockMessages, mockMessages[3]]} />);
    
    // All agents should now be idle
    hvacCard = screen.getByText('HVAC').closest('.agent-card');
    const powerCard = screen.getByText('POWER').closest('.agent-card');
    const securityCard = screen.getByText('SECURITY').closest('.agent-card');
    const networkCard = screen.getByText('NETWORK').closest('.agent-card');
    
    expect(hvacCard).toHaveClass('idle');
    expect(powerCard).toHaveClass('idle');
    expect(securityCard).toHaveClass('idle');
    expect(networkCard).toHaveClass('idle');
  });

  it('displays correct status icons and text', () => {
    render(<AgentStatus agents={mockAgents} />);
    
    const hvacCard = screen.getByText('HVAC').closest('.agent-card');
    const powerCard = screen.getByText('POWER').closest('.agent-card');
    const securityCard = screen.getByText('SECURITY').closest('.agent-card');
    const networkCard = screen.getByText('NETWORK').closest('.agent-card');
    
    // Check status indicators
    expect(hvacCard?.querySelector('.status-indicator')).toHaveClass('idle');
    expect(powerCard?.querySelector('.status-indicator')).toHaveClass('active');
    expect(securityCard?.querySelector('.status-indicator')).toHaveClass('warning');
    expect(networkCard?.querySelector('.status-indicator')).toHaveClass('error');
    
    // Check status text
    expect(screen.getByText('Idle')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByText('Warning')).toBeInTheDocument();
    expect(screen.getByText('Error')).toBeInTheDocument();
  });

  it('includes accessibility attributes', () => {
    render(<AgentStatus agents={mockAgents} />);
    
    const agentCards = screen.getAllByRole('status');
    expect(agentCards).toHaveLength(4);
    
    agentCards.forEach((card, index) => {
      expect(card).toHaveAttribute('aria-label');
      expect(card.getAttribute('aria-label')).toMatch(/HVAC|POWER|SECURITY|NETWORK/);
      expect(card.getAttribute('aria-label')).toMatch(/Idle|Active|Warning|Error/);
    });
  });

  it('handles empty agents array', () => {
    render(<AgentStatus agents={[]} />);
    
    expect(screen.getByText('Agent Status')).toBeInTheDocument();
    expect(screen.getByText('No agents to display')).toBeInTheDocument();
  });

  it('handles undefined messages prop', () => {
    render(<AgentStatus agents={mockAgents} />);
    
    // Should render without errors
    expect(screen.getByText('Agent Status')).toBeInTheDocument();
    expect(screen.getByText('HVAC')).toBeInTheDocument();
  });

  it('applies correct CSS animations for different status types', () => {
    render(<AgentStatus agents={mockAgents} />);
    
    const activeCard = screen.getByText('POWER').closest('.agent-card');
    const warningCard = screen.getByText('SECURITY').closest('.agent-card');
    const errorCard = screen.getByText('NETWORK').closest('.agent-card');
    
    // Check that animations are applied
    expect(activeCard).toHaveStyle('animation: activePulse 2s ease-in-out infinite');
    expect(warningCard).toHaveStyle('animation: warningShake 0.5s ease-in-out infinite');
    expect(errorCard).toHaveStyle('animation: errorPulse 1.5s ease-in-out infinite');
  });

  it('displays last update information', () => {
    render(<AgentStatus agents={mockAgents} />);
    
    // Check that last update text is present
    const lastUpdates = screen.getAllByText('Last updated: Just now');
    expect(lastUpdates).toHaveLength(4);
  });

  it('respects prefers-reduced-motion media query', () => {
    // Mock prefers-reduced-motion
    Object.defineProperty(window.matchMedia, 'matches', {
      writable: true,
      configurable: true,
      value: true,
    });
    
    render(<AgentStatus agents={mockAgents} />);
    
    // No animations should be applied
    const activeCard = screen.getByText('POWER').closest('.agent-card');
    expect(activeCard).not.toHaveStyle('animation');
  });
});