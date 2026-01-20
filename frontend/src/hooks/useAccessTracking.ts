import { useEffect, useRef, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { apiService } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';

function generateSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
}

export function useAccessTracking() {
  const location = useLocation();
  const { username } = useAuth();
  const sessionIdRef = useRef<string>(generateSessionId());
  const lastPathRef = useRef<string>('');

  useEffect(() => {
    if (location.pathname !== lastPathRef.current) {
      const currentPath = location.pathname;

      apiService.logAccess(
        'page_view',
        currentPath,
        `浏览页面: ${currentPath}`,
        username || sessionIdRef.current
      ).catch((error) => {
        if (import.meta.env.DEV) {
          console.debug('Failed to log access:', error);
        }
      });

      lastPathRef.current = currentPath;
    }
  }, [location.pathname, username]);

  const trackClick = useCallback((action: string, pagePath?: string) => {
    apiService.logAccess(
      'click',
      pagePath || location.pathname,
      action,
      username || sessionIdRef.current
    ).catch((error) => {
      if (import.meta.env.DEV) {
        console.debug('Failed to log click:', error);
      }
    });
  }, [location.pathname, username]);

  return { trackClick };
}
