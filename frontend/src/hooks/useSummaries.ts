import { useQuery } from '@tanstack/react-query';
import { apiService } from '@/services/api';

const STALE_TIME_5M = 5 * 60 * 1000;

export function useSummaryDetails(id: number, enabled: boolean = true) {
  return useQuery({
    queryKey: ['summary', id, 'details'],
    queryFn: () => apiService.getSummaryFields(id, 'all'),
    enabled: enabled && !!id && id > 0,
    staleTime: STALE_TIME_5M,
  });
}
