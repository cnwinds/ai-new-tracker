/**
 * 日期相关的工具函数
 */

/**
 * 计算距离今天的天数
 */
export function getDaysAgo(dateString: string | undefined): number | null {
  if (!dateString) return null;
  
  const date = new Date(dateString);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  date.setHours(0, 0, 0, 0);
  
  const diffTime = today.getTime() - date.getTime();
  return Math.floor(diffTime / (1000 * 60 * 60 * 24));
}

/**
 * 获取天数显示文本
 */
export function getDaysAgoText(daysAgo: number | null): string {
  if (daysAgo === null) return '';
  if (daysAgo === 0) return '今天';
  if (daysAgo === 1) return '昨天';
  return `${daysAgo}天前`;
}

/**
 * 格式化日期显示
 */
export function formatDate(dateString: string | undefined): string {
  if (!dateString) return '暂无';
  
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * 获取天数显示颜色
 */
export function getDaysAgoColor(daysAgo: number | null): string {
  if (daysAgo === null) return '#999';
  if (daysAgo > 30) return '#ff4d4f';
  if (daysAgo > 7) return '#faad14';
  return '#52c41a';
}
