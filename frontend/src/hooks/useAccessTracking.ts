import { useEffect, useRef, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { apiService } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import { getOrCreateSessionId } from '@/utils/sessionId';

export function useAccessTracking() {
  const location = useLocation();
  const { username } = useAuth();
  // 使用统一的 sessionId 工具函数，确保持久化
  const sessionIdRef = useRef<string>(getOrCreateSessionId());
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
