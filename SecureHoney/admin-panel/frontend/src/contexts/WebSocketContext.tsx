import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';

interface WebSocketContextType {
  socket: WebSocket | null;
  lastMessage: any;
  connectionStatus: 'connecting' | 'connected' | 'disconnected';
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

interface WebSocketProviderProps {
  children: ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [lastMessage, setLastMessage] = useState<any>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');

  useEffect(() => {
    const connectWebSocket = () => {
      setConnectionStatus('connecting');
      const ws = new WebSocket('ws://localhost:5001/ws');

      ws.onopen = () => {
        setConnectionStatus('connected');
        setSocket(ws);
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          setLastMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        setConnectionStatus('disconnected');
        setSocket(null);
        // Reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('disconnected');
      };
    };

    connectWebSocket();

    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, []);

  return (
    <WebSocketContext.Provider value={{ socket, lastMessage, connectionStatus }}>
      {children}
    </WebSocketContext.Provider>
  );
};
