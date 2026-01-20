import { useEffect, useState, useCallback, useRef } from 'react';
import { wsService } from '@/services/websocket';
import type { WebSocketMessage } from '@/types';

const CONNECT_DELAY = 100;

export function useWebSocket() {
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    
    const connectTimer = setTimeout(() => {
      if (isMountedRef.current) {
        wsService.connect();
      }
    }, CONNECT_DELAY);

    const handleConnected = () => {
      if (isMountedRef.current) {
        setConnected(true);
      }
    };

    const handleError = () => {
      if (isMountedRef.current) {
        setConnected(false);
      }
    };

    const handleClose = () => {
      if (isMountedRef.current) {
        setConnected(false);
      }
    };

    const unsubscribeConnected = wsService.on('connected', handleConnected);
    const unsubscribeError = wsService.on('error', handleError);
    const unsubscribeClose = wsService.on('close', handleClose);

    return () => {
      clearTimeout(connectTimer);
      isMountedRef.current = false;
      unsubscribeConnected();
      unsubscribeError();
      unsubscribeClose();
    };
  }, []);

  const subscribe = useCallback((event: string, callback: (data: unknown) => void) => {
    const unsubscribe = wsService.on(event, (data) => {
      if (isMountedRef.current) {
        setLastMessage({ type: event, ...(data as Record<string, unknown>) } as WebSocketMessage);
        callback(data);
      }
    });
    return unsubscribe;
  }, []);

  return {
    connected,
    lastMessage,
    subscribe,
    isConnected: wsService.isConnected(),
  };
}

