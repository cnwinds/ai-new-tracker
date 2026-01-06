/**
 * Articles Hook
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '@/services/api';
import type { ArticleFilter, Article } from '@/types';
import { message } from 'antd';
import { showError } from '@/utils/error';

export function useArticles(filter: ArticleFilter = {}) {
  return useQuery({
    queryKey: ['articles', filter],
    queryFn: () => apiService.getArticles(filter),
    staleTime: 30 * 1000, // 30秒
  });
}

export function useArticle(id: number) {
  return useQuery({
    queryKey: ['article', id],
    queryFn: () => apiService.getArticle(id),
    enabled: !!id && id > 0,
    staleTime: 60 * 1000, // 1分钟
  });
}

export function useAnalyzeArticle() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, force }: { id: number; force?: boolean }) => 
      apiService.analyzeArticle(id, force ?? false),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['article', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      const messageText = data.is_processed && variables.force 
        ? '重新分析完成' 
        : '分析完成';
      message.success(messageText);
    },
    onError: (error) => {
      showError(error, '分析失败');
    },
  });
}

export function useDeleteArticle() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => apiService.deleteArticle(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      message.success('文章已删除');
    },
    onError: (error) => {
      showError(error, '删除失败');
    },
  });
}

export function useFavoriteArticle() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => apiService.favoriteArticle(id),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['article', variables] });
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      queryClient.invalidateQueries({ queryKey: ['rag'] });
      message.success('已收藏');
    },
    onError: (error) => {
      showError(error, '收藏失败');
    },
  });
}

export function useUnfavoriteArticle() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => apiService.unfavoriteArticle(id),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['article', variables] });
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      queryClient.invalidateQueries({ queryKey: ['rag'] });
      message.success('已取消收藏');
    },
    onError: (error) => {
      showError(error, '取消收藏失败');
    },
  });
}

export function useUpdateArticle() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Article> }) => 
      apiService.updateArticle(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['article', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      message.success('更新成功');
    },
    onError: (error) => {
      showError(error, '更新失败');
    },
  });
}
