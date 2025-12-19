import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import FacilityLayout from '../FacilityLayout';

describe('FacilityLayout', () => {
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
      payload: { agents: ['hvac', 'power'] },
      timestamp: Date.now(),
    },
  ];

  beforeEach(() => {
    // Mock window resize
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024,
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: 768,
    });
  });

  it('renders all zones and labels', () => {
    render(<FacilityLayout />);
    
    expect(screen.getByText('Facility Layout')).toBeInTheDocument();
    expect(screen.getByText('HVAC')).toBeInTheDocument();
    expect(screen.getByText('POWER')).toBeInTheDocument();
    expect(screen.getByText('SECURITY')).toBeInTheDocument();
    expect(screen.getByText('NETWORK')).toBeInTheDocument();
  });

  it('applies active CSS class when simulated event is received', () => {
    const { rerender } = render(<FacilityLayout messages={[]} />);
    
    // Initially all zones should be idle
    const hvacZone = document.querySelector('g:has(text:contains("HVAC"))');
    expect(hvacZone?.classList.contains('active')).toBe(false);
    
    // Render with active HVAC message
    rerender(<FacilityLayout messages={mockMessages} />);
    
    // HVAC should now be active
    const hvacElement = screen.getByText('HVAC').parentElement?.parentElement;
    expect(hvacElement?.classList.contains('active')).toBe(true);
  });

  it('shows transient coordination line when coordination event occurs', () => {
    const { rerender } = render(<FacilityLayout messages={[]} />);
    
    // Initially no coordination lines should be present
    expect(document.querySelector('.coordination-line')).toBeNull();
    
    // Render with coordination event
    rerender(<FacilityLayout messages={mockMessages} />);
    
    // Coordination line should now be present
    expect(document.querySelector('.coordination-line')).toBeInTheDocument();
  });

  it('handles scenario.complete event by resetting all zones to idle', () => {
    const completeMessage = {
      type: 'scenario.complete',
      payload: {},
      timestamp: Date.now(),
    };
    
    const { rerender } = render(<FacilityLayout messages={mockMessages} />);
    
    // Initially zones should have status from mock messages
    const hvacElement = screen.getByText('HVAC').parentElement?.parentElement;
    const powerElement = screen.getByText('POWER').parentElement?.parentElement;
    expect(hvacElement?.classList.contains('active')).toBe(true);
    expect(powerElement?.classList.contains('warning')).toBe(true);
    
    // Render with scenario complete
    rerender(<FacilityLayout messages={[...mockMessages, completeMessage]} />);
    
    // All zones should now be idle
    const hvacAfterReset = screen.getByText('HVAC').parentElement?.parentElement;
    expect(hvacAfterReset?.classList.contains('active')).toBe(false);
    expect(hvacAfterReset?.classList.contains('warning')).toBe(false);
    expect(hvacAfterReset?.classList.contains('error')).toBe(false);
  });

  it('updates zone status based on status messages', () => {
    const securityError = {
      type: 'security.status',
      payload: { state: 'error' },
      timestamp: Date.now(),
    };
    
    const { rerender } = render(<FacilityLayout messages={[]} />);
    
    // Initially security should be idle
    const securityElement = screen.getByText('SECURITY').parentElement?.parentElement;
    expect(securityElement?.classList.contains('error')).toBe(false);
    
    // Render with security error
    rerender(<FacilityLayout messages={[securityError]} />);
    
    // Security should now be error
    const securityAfterError = screen.getByText('SECURITY').parentElement?.parentElement;
    expect(securityAfterError?.classList.contains('error')).toBe(true);
  });

  it('displays correct zone icons and colors', () => {
    render(<FacilityLayout messages={mockMessages} />);
    
    // Check that zones are present with correct structure
    const zones = ['HVAC', 'POWER', 'SECURITY', 'NETWORK'];
    zones.forEach(zone => {
      expect(screen.getByText(zone)).toBeInTheDocument();
      const zoneElement = screen.getByText(zone).closest('g');
      expect(zoneElement).toBeInTheDocument();
      expect(zoneElement?.querySelector('circle')).toBeInTheDocument();
      expect(zoneElement?.querySelector('path')).toBeInTheDocument();
    });
  });

  it('handles window resize for responsive sizing', () => {
    // Initial render
    render(<FacilityLayout />);
    
    // Simulate window resize
    fireEvent(window, new Event('resize'));
    
    // Component should handle resize gracefully (no errors thrown)
    expect(screen.getByText('Facility Layout')).toBeInTheDocument();
  });

  it('applies correct CSS classes for different status types', () => {
    const warningMessage = {
      type: 'network.status',
      payload: { state: 'warning' },
      timestamp: Date.now(),
    };
    
    const { rerender } = render(<FacilityLayout messages={[]} />);
    
    // Initially network should be idle
    const networkElement = screen.getByText('NETWORK').parentElement?.parentElement;
    expect(networkElement?.classList.contains('warning')).toBe(false);
    
    // Render with network warning
    rerender(<FacilityLayout messages={[warningMessage]} />);
    
    // Network should now be warning
    const networkAfterWarning = screen.getByText('NETWORK').parentElement?.parentElement;
    expect(networkAfterWarning?.classList.contains('warning')).toBe(true);
  });

  it('displays grid background in SVG', () => {
    render(<FacilityLayout />);
    
    const svg = document.querySelector('.facility-svg');
    expect(svg).toBeInTheDocument();
    
    const gridPattern = svg?.querySelector('#grid');
    expect(gridPattern).toBeInTheDocument();
    
    const gridRect = svg?.querySelector('rect[fill="url(#grid)"]');
    expect(gridRect).toBeInTheDocument();
  });

  it('handles multiple coordination events', () => {
    const coordinationMessages = [
      {
        type: 'coordination.test1',
        payload: { agents: ['hvac', 'power'] },
        timestamp: Date.now(),
      },
      {
        type: 'coordination.test2',
        payload: { agents: ['security', 'network'] },
        timestamp: Date.now(),
      },
    ];
    
    const { rerender } = render(<FacilityLayout messages={[]} />);
    
    // Initially no coordination lines
    expect(document.querySelectorAll('.coordination-line').length).toBe(0);
    
    // Render with multiple coordination events
    rerender(<FacilityLayout messages={coordinationMessages} />);
    
    // Should have coordination lines for both events
    expect(document.querySelectorAll('.coordination-line').length).toBe(2);
  });

  it('respects prefers-reduced-motion media query', () => {
    // Mock prefers-reduced-motion
    Object.defineProperty(window.matchMedia, 'matches', {
      writable: true,
      configurable: true,
      value: true,
    });
    
    render(<FacilityLayout messages={mockMessages} />);
    
    // Component should render without animations
    const zones = document.querySelectorAll('.zone-circle');
    zones.forEach(zone => {
      expect(zone).not.toHaveStyle('animation');
    });
  });
});