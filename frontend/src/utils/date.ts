const MILLISECONDS_PER_DAY = 1000 * 60 * 60 * 24;

export function getDaysAgo(dateString: string | undefined): number | null {
  if (!dateString) return null;
  
  const date = new Date(dateString);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  date.setHours(0, 0, 0, 0);
  
  const diffTime = today.getTime() - date.getTime();
  return Math.floor(diffTime / MILLISECONDS_PER_DAY);
}

export function getDaysAgoText(daysAgo: number | null): string {
  if (daysAgo === null) return '';
  if (daysAgo === 0) return '今天';
  if (daysAgo === 1) return '昨天';
  return `${daysAgo}天前`;
}

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

export function getDaysAgoColor(daysAgo: number | null): string {
  if (daysAgo === null) return '#999';
  if (daysAgo > 30) return '#ff4d4f';
  if (daysAgo > 7) return '#faad14';
  return '#52c41a';
}
