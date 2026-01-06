/**
 * 文章相关的工具函数
 */
import type { Article } from '@/types';

/**
 * 处理 summary 字段：如果是 JSON 字符串，尝试解析并提取 summary 字段
 */
export function getSummaryText(article: Article): string {
  if (!article.summary) return '';
  
  const summaryStr = String(article.summary).trim();
  if (!summaryStr) return '';
  
  // 检查是否以 { 开头，可能是 JSON 对象字符串
  if (summaryStr.startsWith('{') && summaryStr.includes('"summary"')) {
    try {
      const parsed = JSON.parse(summaryStr);
      // 如果解析成功且是对象，提取 summary 字段
      if (typeof parsed === 'object' && parsed !== null && 'summary' in parsed) {
        if (typeof parsed.summary === 'string') {
          return parsed.summary;
        }
      }
    } catch (e) {
      // JSON 解析失败，可能是格式不完整，返回原始字符串
      console.warn('Failed to parse summary JSON:', e);
    }
  }
  
  // 如果不是 JSON 格式，直接返回原始字符串
  return summaryStr;
}

/**
 * 重要性颜色映射
 */
export const IMPORTANCE_COLORS: Record<string, string> = {
  high: 'red',
  medium: 'orange',
  low: 'green',
} as const;

/**
 * 重要性标签文本映射
 */
export const IMPORTANCE_LABELS: Record<string, string> = {
  high: '高',
  medium: '中',
  low: '低',
} as const;

/**
 * 获取重要性标签文本
 */
export function getImportanceLabel(importance: string | undefined): string {
  if (!importance) return '';
  return IMPORTANCE_LABELS[importance] || importance;
}
