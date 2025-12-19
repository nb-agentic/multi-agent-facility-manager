import { renderHook, act, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import useWebSocket from '../useWebSocket'

// Mock timers
vi.useFakeTimers()

describe.skip('useWebSocket', () => {
  let mockWebSocket: any
  let mockFetch: any

  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks()
    
    // Mock WebSocket
    mockWebSocket = {
      readyState: WebSocket.CONNECTING,
      send: vi.fn(),
      close: vi.fn(),
      onopen: null,
      onclose: null,
      onmessage: null,
      onerror: null,
    }

    // @ts-ignore
    (global as any).WebSocket = vi.fn(() => mockWebSocket)

    // Mock fetch for polling fallback
    mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ type: 'test', data: 'polling data' })
    })
    // @ts-ignore
    (global as any).fetch = mockFetch
  })

  afterEach(() => {
    vi.clearAllTimers()
    vi.useRealTimers()
    vi.useFakeTimers()
  })

  it('should initialize with correct default state', () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8000'))

    expect(result.current.messages).toEqual([])
    expect(result.current.isConnected).toBe(false)
    expect(result.current.connectionStatus.isConnected).toBe(false)
    expect(result.current.connectionStatus.isReconnecting).toBe(false)
    expect(result.current.connectionStatus.reconnectAttempts).toBe(0)
    expect(result.current.connectionStatus.usingFallback).toBe(false)
  })

  it('should establish WebSocket connection', async () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8000'))

    // Simulate WebSocket opening
    act(() => {
      mockWebSocket.readyState = WebSocket.OPEN
      if (mockWebSocket.onopen) {
        mockWebSocket.onopen(new Event('open'))
      }
    })

    expect(result.current.isConnected).toBe(true)
    expect(result.current.connectionStatus.isConnected).toBe(true)
    expect(result.current.connectionStatus.reconnectAttempts).toBe(0)
  })

  it('should handle incoming messages', async () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8000'))

    // Simulate connection and message
    act(() => {
      mockWebSocket.readyState = WebSocket.OPEN
      if (mockWebSocket.onopen) {
        mockWebSocket.onopen(new Event('open'))
      }
    })

    const testMessage = { type: 'test', data: 'hello' }
    act(() => {
      if (mockWebSocket.onmessage) {
        mockWebSocket.onmessage(new MessageEvent('message', {
          data: JSON.stringify(testMessage)
        }))
      }
    })

    expect(result.current.messages).toHaveLength(1)
    expect(result.current.messages[0]).toMatchObject(testMessage)
    expect(result.current.messages[0]).toHaveProperty('timestamp')
  })

  it('should handle heartbeat ping/pong', async () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8000'))

    // Simulate connection
    act(() => {
      mockWebSocket.readyState = WebSocket.OPEN
      if (mockWebSocket.onopen) {
        mockWebSocket.onopen(new Event('open'))
      }
    })

    // Fast-forward to trigger heartbeat
    act(() => {
      vi.advanceTimersByTime(30000) // 30 seconds
    })

    expect(mockWebSocket.send).toHaveBeenCalledWith(JSON.stringify({ type: 'ping' }))

    // Simulate pong response (should not be added to messages)
    act(() => {
      if (mockWebSocket.onmessage) {
        mockWebSocket.onmessage(new MessageEvent('message', {
          data: JSON.stringify({ type: 'pong' })
        }))
      }
    })

    expect(result.current.messages).toHaveLength(0) // Pong should not be added to messages
  })

  it('should attempt reconnection with exponential backoff', async () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8000'))

    // Simulate connection and then disconnection
    act(() => {
      mockWebSocket.readyState = WebSocket.OPEN
      if (mockWebSocket.onopen) {
        mockWebSocket.onopen(new Event('open'))
      }
    })

    expect(result.current.isConnected).toBe(true)

    // Simulate disconnection
    act(() => {
      mockWebSocket.readyState = WebSocket.CLOSED
      if (mockWebSocket.onclose) {
        mockWebSocket.onclose(new CloseEvent('close'))
      }
    })

    expect(result.current.isConnected).toBe(false)
    expect(result.current.connectionStatus.isReconnecting).toBe(true)
    expect(result.current.connectionStatus.reconnectAttempts).toBe(1)

    // Fast-forward to trigger first reconnection attempt (should be within 5 seconds)
    act(() => {
      vi.advanceTimersByTime(5000)
    })

    // WebSocket constructor should be called again for reconnection
    expect((global as any).WebSocket).toHaveBeenCalledTimes(2)
  })

  it('should fall back to polling after max reconnection attempts', async () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8000/ws'))

    // Simulate multiple failed reconnection attempts
    for (let i = 0; i < 11; i++) { // Exceed max attempts (10)
      act(() => {
        if (mockWebSocket.onclose) {
          mockWebSocket.onclose(new CloseEvent('close'))
        }
      })

      if (i < 10) {
        act(() => {
          vi.advanceTimersByTime(5000)
        })
      }
    }

    expect(result.current.connectionStatus.usingFallback).toBe(true)
    expect(result.current.connectionStatus.isReconnecting).toBe(false)

    // Fast-forward to trigger polling
    act(() => {
      vi.advanceTimersByTime(1000)
    })

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/health')
    })
  })

  it('should handle WebSocket errors', async () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8000'))

    // Simulate WebSocket error
    act(() => {
      if (mockWebSocket.onerror) {
        mockWebSocket.onerror(new Event('error'))
      }
    })

    expect(result.current.connectionStatus.lastError).toBe('WebSocket connection error')
  })

  it('should provide manual reconnect function', async () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8000'))

    expect(typeof result.current.reconnect).toBe('function')

    // Call manual reconnect
    act(() => {
      result.current.reconnect()
    })

    // Should create a new WebSocket connection
    expect((global as any).WebSocket).toHaveBeenCalledTimes(2)
  })

  it('should clean up on unmount', () => {
    const { unmount } = renderHook(() => useWebSocket('ws://localhost:8000'))

    // Simulate connection
    act(() => {
      mockWebSocket.readyState = WebSocket.OPEN
      if (mockWebSocket.onopen) {
        mockWebSocket.onopen(new Event('open'))
      }
    })

    unmount()

    expect(mockWebSocket.close).toHaveBeenCalled()
  })

  it('should not connect if URL is empty', () => {
    const { result } = renderHook(() => useWebSocket(''))

    expect((global as any).WebSocket).not.toHaveBeenCalled()
    expect(result.current.isConnected).toBe(false)
  })

  it('should handle JSON parsing errors gracefully', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const { result } = renderHook(() => useWebSocket('ws://localhost:8000'))

    // Simulate connection
    act(() => {
      mockWebSocket.readyState = WebSocket.OPEN
      if (mockWebSocket.onopen) {
        mockWebSocket.onopen(new Event('open'))
      }
    })

    // Send invalid JSON
    act(() => {
      if (mockWebSocket.onmessage) {
        mockWebSocket.onmessage(new MessageEvent('message', {
          data: 'invalid json'
        }))
      }
    })

    expect(consoleSpy).toHaveBeenCalledWith('Error parsing WebSocket message:', expect.any(Error))
    expect(result.current.messages).toHaveLength(0)

    consoleSpy.mockRestore()
  })

  it('should ensure reconnection happens within 5 seconds', async () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8000'))

    // Simulate connection and disconnection
    act(() => {
      mockWebSocket.readyState = WebSocket.OPEN
      if (mockWebSocket.onopen) {
        mockWebSocket.onopen(new Event('open'))
      }
    })

    act(() => {
      mockWebSocket.readyState = WebSocket.CLOSED
      if (mockWebSocket.onclose) {
        mockWebSocket.onclose(new CloseEvent('close'))
      }
    })

    // Even with exponential backoff, reconnection should happen within 5 seconds
    act(() => {
      vi.advanceTimersByTime(5000)
    })

    expect((global as any).WebSocket).toHaveBeenCalledTimes(2)
  })
})