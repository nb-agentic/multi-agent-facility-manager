import { useState, useEffect, useRef, useCallback } from 'react';

interface ConnectionStatus {
  isConnected: boolean;
  isReconnecting: boolean;
  reconnectAttempts: number;
  lastError?: string;
  usingFallback: boolean;
}

const useWebSocket = (url: string) => {
  const [messages, setMessages] = useState<any[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
    isConnected: false,
    isReconnecting: false,
    reconnectAttempts: 0,
    usingFallback: false,
  });
  
  const webSocketRef = useRef<WebSocket | null>(null);
  const heartbeatIntervalRef = useRef<number | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const pollingIntervalRef = useRef<number | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 10;
  const heartbeatInterval = 30000; // 30 seconds
  const pollingInterval = 1000; // 1 second for fallback polling

  // Heartbeat mechanism
  const startHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
    }
    
    heartbeatIntervalRef.current = setInterval(() => {
      if (webSocketRef.current?.readyState === WebSocket.OPEN) {
        webSocketRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, heartbeatInterval);
  }, []);

  const stopHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  // Exponential backoff calculation
  const getReconnectDelay = useCallback((attempt: number): number => {
    const baseDelay = 1000; // 1 second
    const maxDelay = 30000; // 30 seconds
    const delay = Math.min(baseDelay * Math.pow(2, attempt), maxDelay);
    return delay + Math.random() * 1000; // Add jitter
  }, []);

  // Fallback polling mechanism
  const startPolling = useCallback(() => {
    if (pollingIntervalRef.current) return;
    
    setConnectionStatus(prev => ({ ...prev, usingFallback: true }));
    
    pollingIntervalRef.current = setInterval(async () => {
      try {
        const response = await fetch(url.replace('ws://', 'http://').replace('wss://', 'https://') + '/health');
        if (response.ok) {
          const data = await response.json();
          setMessages(prev => [...prev, { ...data, timestamp: Date.now(), source: 'polling' }]);
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, pollingInterval);
  }, [url]);

  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
      setConnectionStatus(prev => ({ ...prev, usingFallback: false }));
    }
  }, []);

  const connect = useCallback(() => {
    if (webSocketRef.current?.readyState === WebSocket.CONNECTING) {
      return;
    }

    try {
      const ws = new WebSocket(url);
      webSocketRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        reconnectAttemptsRef.current = 0;
        setConnectionStatus({
          isConnected: true,
          isReconnecting: false,
          reconnectAttempts: 0,
          usingFallback: false,
        });
        startHeartbeat();
        stopPolling();
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          // Handle pong responses for heartbeat
          if (message.type === 'pong') {
            return;
          }
          setMessages((prevMessages) => [...prevMessages, { ...message, timestamp: Date.now() }]);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket disconnected', event.code, event.reason);
        stopHeartbeat();
        
        setConnectionStatus(prev => ({
          ...prev,
          isConnected: false,
          isReconnecting: reconnectAttemptsRef.current < maxReconnectAttempts,
        }));

        // Attempt reconnection with exponential backoff
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = getReconnectDelay(reconnectAttemptsRef.current);
          reconnectAttemptsRef.current++;
          
          setConnectionStatus(prev => ({
            ...prev,
            reconnectAttempts: reconnectAttemptsRef.current,
          }));

          console.log(`Attempting to reconnect in ${delay}ms (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, Math.min(delay, 5000)); // Ensure reconnection within 5 seconds as required
        } else {
          console.log('Max reconnection attempts reached, falling back to polling');
          setConnectionStatus(prev => ({
            ...prev,
            isReconnecting: false,
            lastError: 'Max reconnection attempts reached',
          }));
          startPolling();
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus(prev => ({
          ...prev,
          lastError: 'WebSocket connection error',
        }));
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionStatus(prev => ({
        ...prev,
        lastError: 'Failed to create WebSocket connection',
      }));
      
      // If WebSocket creation fails, start polling immediately
      if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
        startPolling();
      }
    }
  }, [url, getReconnectDelay, startHeartbeat, stopHeartbeat, startPolling, stopPolling]);

  useEffect(() => {
    if (!url) return;

    connect();

    return () => {
      stopHeartbeat();
      stopPolling();
      
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      
      if (webSocketRef.current) {
        webSocketRef.current.close();
      }
    };
  }, [url, connect, stopHeartbeat, stopPolling]);

  // Legacy compatibility - maintain isConnected for existing components
  const isConnected = connectionStatus.isConnected;

  return {
    messages,
    isConnected,
    connectionStatus,
    reconnect: connect
  };
};

export default useWebSocket;