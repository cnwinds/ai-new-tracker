import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '@/services/api';
import type { ArticleFilter, Article } from '@/types';
import { useErrorHandler } from './useErrorHandler';

const STALE_TIME_30S = 30 * 1000;
const STALE_TIME_1M = 60 * 1000;
const STALE_TIME_5M = 5 * 60 * 1000;

export function useArticles(filter: ArticleFilter = {}) {
  return useQuery({
    queryKey: ['articles', filter],
    queryFn: () => apiService.getArticles(filter),
    staleTime: STALE_TIME_30S,
  });
}

export function useArticle(id: number) {
  return useQuery({
    queryKey: ['article', id],
    queryFn: () => apiService.getArticle(id),
    enabled: !!id && id > 0,
    staleTime: STALE_TIME_1M,
  });
}

export function useAnalyzeArticle() {
  const queryClient = useQueryClient();
  const { showError, showSuccess } = useErrorHandler();

  return useMutation({
    mutationFn: ({ id, force = false }: { id: number; force?: boolean }) => 
      apiService.analyzeArticle(id, force),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['article', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      const messageText = data.is_processed && variables.force 
        ? '重新分析完成' 
        : '分析完成';
      showSuccess(messageText);
    },
    onError: (error) => {
      showError(error, '分析失败');
    },
  });
}

export function useDeleteArticle() {
  const queryClient = useQueryClient();
  const { showError, showSuccess } = useErrorHandler();

  return useMutation({
    mutationFn: (id: number) => apiService.deleteArticle(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      showSuccess('文章已删除');
    },
    onError: (error) => {
      showError(error, '删除失败');
    },
  });
}

export function useFavoriteArticle() {
  const queryClient = useQueryClient();
  const { showError, showSuccess } = useErrorHandler();

  return useMutation({
    mutationFn: (id: number) => apiService.favoriteArticle(id),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['article', variables] });
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      queryClient.invalidateQueries({ queryKey: ['rag'] });
      showSuccess('已收藏');
    },
    onError: (error) => {
      showError(error, '收藏失败');
    },
  });
}

export function useUnfavoriteArticle() {
  const queryClient = useQueryClient();
  const { showError, showSuccess } = useErrorHandler();

  return useMutation({
    mutationFn: (id: number) => apiService.unfavoriteArticle(id),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['article', variables] });
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      queryClient.invalidateQueries({ queryKey: ['rag'] });
      showSuccess('已取消收藏');
    },
    onError: (error) => {
      showError(error, '取消收藏失败');
    },
  });
}

export function useUpdateArticle() {
  const queryClient = useQueryClient();
  const { showError, showSuccess } = useErrorHandler();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Article> }) => 
      apiService.updateArticle(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['article', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      showSuccess('更新成功');
    },
    onError: (error) => {
      showError(error, '更新失败');
    },
  });
}

export function useArticleDetails(id: number, enabled: boolean = true) {
  return useQuery({
    queryKey: ['article', id, 'details'],
    queryFn: () => apiService.getArticleFields(id, 'all'),
    enabled: enabled && !!id && id > 0,
    staleTime: STALE_TIME_5M,
  });
}
