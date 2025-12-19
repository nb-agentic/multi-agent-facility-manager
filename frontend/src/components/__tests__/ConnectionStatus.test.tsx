import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ConnectionStatus from '../ConnectionStatus';

describe('ConnectionStatus', () => {
  it('renders connected state correctly', () => {
    const connectionStatus = {
      isConnected: true,
      isReconnecting: false,
      reconnectAttempts: 0,
      usingFallback: false,
    };

    render(<ConnectionStatus connectionStatus={connectionStatus} />);
    
    expect(screen.getByText('Connected')).toBeInTheDocument();
    expect(screen.getByText('●')).toBeInTheDocument();
  });

  it('renders disconnected state correctly', () => {
    const connectionStatus = {
      isConnected: false,
      isReconnecting: false,
      reconnectAttempts: 0,
      usingFallback: false,
    };

    render(<ConnectionStatus connectionStatus={connectionStatus} />);
    
    expect(screen.getByText('Disconnected')).toBeInTheDocument();
    expect(screen.getByText('○')).toBeInTheDocument();
  });

  it('renders reconnecting state with attempt count', () => {
    const connectionStatus = {
      isConnected: false,
      isReconnecting: true,
      reconnectAttempts: 3,
      usingFallback: false,
    };

    render(<ConnectionStatus connectionStatus={connectionStatus} />);
    
    expect(screen.getByText('Reconnecting (3/10)')).toBeInTheDocument();
    expect(screen.getByText('◐')).toBeInTheDocument();
  });

  it('renders progress bar during reconnecting', () => {
    const connectionStatus = {
      isConnected: false,
      isReconnecting: true,
      reconnectAttempts: 5,
      usingFallback: false,
    };

    render(<ConnectionStatus connectionStatus={connectionStatus} />);
    
    const progressFill = document.querySelector('.connection-status__progress-fill');
    expect(progressFill).toBeInTheDocument();
    expect(progressFill).toHaveStyle('width: 50%');
  });

  it('renders fallback state correctly', () => {
    const connectionStatus = {
      isConnected: false,
      isReconnecting: false,
      reconnectAttempts: 0,
      usingFallback: true,
    };

    render(<ConnectionStatus connectionStatus={connectionStatus} />);
    
    expect(screen.getByText('Using Fallback')).toBeInTheDocument();
    expect(screen.getByText('◑')).toBeInTheDocument();
    expect(screen.getByText('Polling for updates')).toBeInTheDocument();
  });

  it('renders error message when present', () => {
    const connectionStatus = {
      isConnected: false,
      isReconnecting: false,
      reconnectAttempts: 0,
      lastError: 'Connection timeout',
      usingFallback: false,
    };

    render(<ConnectionStatus connectionStatus={connectionStatus} />);
    
    expect(screen.getByText('Connection timeout')).toBeInTheDocument();
    expect(screen.getByText('⚠')).toBeInTheDocument();
  });

  it('does not show error when connected', () => {
    const connectionStatus = {
      isConnected: true,
      isReconnecting: false,
      reconnectAttempts: 0,
      lastError: 'Previous error',
      usingFallback: false,
    };

    render(<ConnectionStatus connectionStatus={connectionStatus} />);
    
    expect(screen.queryByText('Previous error')).not.toBeInTheDocument();
    expect(screen.queryByText('⚠')).not.toBeInTheDocument();
  });

  it('does not show error when reconnecting', () => {
    const connectionStatus = {
      isConnected: false,
      isReconnecting: true,
      reconnectAttempts: 2,
      lastError: 'Previous error',
      usingFallback: false,
    };

    render(<ConnectionStatus connectionStatus={connectionStatus} />);
    
    expect(screen.queryByText('Previous error')).not.toBeInTheDocument();
    expect(screen.queryByText('⚠')).not.toBeInTheDocument();
  });

  it('applies correct CSS classes for each state', () => {
    const { rerender } = render(
      <ConnectionStatus 
        connectionStatus={{
          isConnected: true,
          isReconnecting: false,
          reconnectAttempts: 0,
          usingFallback: false,
        }} 
      />
    );
    
    expect(document.querySelector('.connection-status--connected')).toBeInTheDocument();

    rerender(
      <ConnectionStatus 
        connectionStatus={{
          isConnected: false,
          isReconnecting: true,
          reconnectAttempts: 1,
          usingFallback: false,
        }} 
      />
    );
    
    expect(document.querySelector('.connection-status--reconnecting')).toBeInTheDocument();

    rerender(
      <ConnectionStatus 
        connectionStatus={{
          isConnected: false,
          isReconnecting: false,
          reconnectAttempts: 0,
          usingFallback: true,
        }} 
      />
    );
    
    expect(document.querySelector('.connection-status--fallback')).toBeInTheDocument();

    rerender(
      <ConnectionStatus 
        connectionStatus={{
          isConnected: false,
          isReconnecting: false,
          reconnectAttempts: 0,
          usingFallback: false,
        }} 
      />
    );
    
    expect(document.querySelector('.connection-status--disconnected')).toBeInTheDocument();
  });

  it('handles edge case with maximum reconnect attempts', () => {
    const connectionStatus = {
      isConnected: false,
      isReconnecting: true,
      reconnectAttempts: 10,
      usingFallback: false,
    };

    render(<ConnectionStatus connectionStatus={connectionStatus} />);
    
    expect(screen.getByText('Reconnecting (10/10)')).toBeInTheDocument();
    
    const progressFill = document.querySelector('.connection-status__progress-fill');
    expect(progressFill).toHaveStyle('width: 100%');
  });
});