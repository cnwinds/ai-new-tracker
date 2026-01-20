const SOURCE_TYPE_MAP: Record<string, string> = {
  rss_feed: 'rss',
  api_source: 'api',
  web_source: 'web',
};

export function normalizeSourceType(type: string | undefined): string {
  if (!type) return 'rss';
  const normalized = type.toLowerCase().trim();
  return SOURCE_TYPE_MAP[normalized] || normalized;
}

export const SOURCE_TYPE_LABELS: Record<string, string> = {
  rss: 'RSS源',
  api: 'API源',
  web: 'Web源',
  email: '邮件源',
} as const;

export function groupSourcesByType<T extends { source_type?: string }>(
  sources: T[]
): Record<string, T[]> {
  return sources.reduce((acc, source) => {
    const type = normalizeSourceType(source.source_type);
    if (!acc[type]) {
      acc[type] = [];
    }
    acc[type].push(source);
    return acc;
  }, {} as Record<string, T[]>);
}

const SUB_TYPE_SUPPORTED_SOURCES = ['api'] as const;

export function sourceTypeSupportsSubType(sourceType: string): boolean {
  return SUB_TYPE_SUPPORTED_SOURCES.includes(normalizeSourceType(sourceType) as typeof SUB_TYPE_SUPPORTED_SOURCES[number]);
}

const API_SUB_TYPE_OPTIONS: Array<{ value: string; label: string }> = [
  { value: 'arxiv', label: 'arXiv' },
  { value: 'huggingface', label: 'Hugging Face' },
  { value: 'paperswithcode', label: 'Papers with Code' },
  { value: 'twitter', label: 'Twitter/X' },
];

export function getSubTypeOptions(sourceType: string): Array<{ value: string; label: string }> {
  const normalizedType = normalizeSourceType(sourceType);
  
  if (normalizedType === 'api') {
    return API_SUB_TYPE_OPTIONS;
  }
  
  return [];
}
