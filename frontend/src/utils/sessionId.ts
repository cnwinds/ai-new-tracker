/**
 * Session ID 工具函数
 * 用于统一管理用户会话标识，确保独立用户统计的准确性
 */

const STORAGE_KEY = 'access_session_id';

/**
 * 获取或创建 session ID
 * 使用 localStorage 持久化，确保同一用户在不同页面刷新时使用相同的标识
 */
export function getOrCreateSessionId(): string {
  // 尝试从 localStorage 获取
  let sessionId = localStorage.getItem(STORAGE_KEY);

  // 如果不存在，生成新的并保存
  if (!sessionId) {
    sessionId = `session_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
    localStorage.setItem(STORAGE_KEY, sessionId);
  }

  return sessionId;
}

/**
 * 清除 session ID（用于测试或登出时）
 */
export function clearSessionId(): void {
  localStorage.removeItem(STORAGE_KEY);
}
