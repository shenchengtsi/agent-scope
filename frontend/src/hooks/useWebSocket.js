import { useState, useEffect, useRef, useCallback } from 'react';

const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';

export function useWebSocket() {
  const [traces, setTraces] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);
  const ws = useRef(null);
  const reconnectTimeout = useRef(null);

  const connect = useCallback(() => {
    try {
      ws.current = new WebSocket(WS_URL);

      ws.current.onopen = () => {
        console.log('✅ Connected to AgentScope backend');
        setIsConnected(true);
        setError(null);
      };

      ws.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          
          if (message.type === 'initial') {
            setTraces(message.data || []);
          } else if (message.type === 'trace_update') {
            setTraces((prevTraces) => {
              const existingIndex = prevTraces.findIndex(t => t.id === message.data.id);
              if (existingIndex >= 0) {
                // Update existing trace
                const updated = [...prevTraces];
                updated[existingIndex] = message.data;
                return updated;
              } else {
                // Add new trace at the beginning
                return [message.data, ...prevTraces];
              }
            });
          } else if (message.type === 'clear_all') {
            setTraces([]);
          }
        } catch (err) {
          console.error('Failed to parse message:', err);
        }
      };

      ws.current.onclose = () => {
        console.log('❌ Disconnected from backend');
        setIsConnected(false);
        // Attempt to reconnect after 3 seconds
        reconnectTimeout.current = setTimeout(connect, 3000);
      };

      ws.current.onerror = (err) => {
        console.error('WebSocket error:', err);
        setError('Connection error');
        setIsConnected(false);
      };
    } catch (err) {
      console.error('Failed to connect:', err);
      setError('Failed to connect');
      reconnectTimeout.current = setTimeout(connect, 3000);
    }
  }, []);

  const sendMessage = useCallback((message) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    }
  }, []);

  const clearAllTraces = useCallback(async () => {
    try {
      await fetch('/api/traces', { method: 'DELETE' });
      setTraces([]);
    } catch (err) {
      console.error('Failed to clear traces:', err);
    }
  }, []);

  useEffect(() => {
    connect();
    
    // Ping to keep connection alive
    const pingInterval = setInterval(() => {
      sendMessage({ type: 'ping' });
    }, 25000);

    return () => {
      clearInterval(pingInterval);
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect, sendMessage]);

  return {
    traces,
    isConnected,
    error,
    sendMessage,
    clearAllTraces,
  };
}