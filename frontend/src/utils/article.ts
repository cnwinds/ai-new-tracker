import type { Article } from '@/types';

export function getSummaryText(article: Article): string {
  if (!article.summary) return '';
  
  const summaryStr = String(article.summary).trim();
  if (!summaryStr) return '';
  
  if (summaryStr.startsWith('{') && summaryStr.includes('"summary"')) {
    try {
      const parsed = JSON.parse(summaryStr);
      if (typeof parsed === 'object' && parsed !== null && 'summary' in parsed) {
        if (typeof parsed.summary === 'string') {
          return parsed.summary;
        }
      }
    } catch {
      // JSON 解析失败，返回原始字符串
    }
  }
  
  return summaryStr;
}

export const IMPORTANCE_COLORS: Record<string, string> = {
  high: 'red',
  medium: 'orange',
  low: 'green',
} as const;

export const IMPORTANCE_LABELS: Record<string, string> = {
  high: '高',
  medium: '中',
  low: '低',
} as const;

export function getImportanceLabel(importance: string | undefined): string {
  if (!importance) return '';
  return IMPORTANCE_LABELS[importance] || importance;
}
