/**
 * 访问追踪组件 - 在 Router 内部使用
 */
import { useMemo } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { getOrCreateSessionId } from '@/utils/sessionId';

export default function AccessTracker() {
  // 这个组件不直接使用 username，但保留 useAuth 调用以备将来使用
  useAuth();

  // 使用 useMemo 确保 sessionId 只生成一次
  // 这个 session ID 会在文章展开和查看详情时使用
  useMemo(() => getOrCreateSessionId(), []);

  // 这个组件不渲染任何内容
  // 只负责生成和存储 session ID
  return null;
}
