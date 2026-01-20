/**
 * 统一的错误处理工具
 */
import type { ApiError } from '@/components/settings/types';

/**
 * 从错误对象中提取详细错误消息
 */
export function extractErrorMessage(error: unknown): string {
  if (typeof error === 'object' && error !== null) {
    const apiError = error as ApiError;
    
    if (apiError.response?.data?.detail) {
      return apiError.response.data.detail;
    }
    
    if (apiError.message) {
      return apiError.message;
    }
    
    if (apiError.data && typeof apiError.data === 'object') {
      const data = apiError.data as Record<string, unknown>;
      if (typeof data.detail === 'string') {
        return data.detail;
      }
      if (typeof data.message === 'string') {
        return data.message;
      }
    }
  }
  
  if (error instanceof Error) {
    return error.message;
  }
  
  return '未知错误';
}

export function isAuthError(error: unknown): boolean {
  return isErrorWithStatus(error, 401);
}

export function isForbiddenError(error: unknown): boolean {
  return isErrorWithStatus(error, 403);
}

export function isServerError(error: unknown): boolean {
  if (typeof error === 'object' && error !== null) {
    const apiError = error as ApiError;
    return apiError.status >= 500 && apiError.status < 600;
  }
  return false;
}

export function isClientError(error: unknown): boolean {
  if (typeof error === 'object' && error !== null) {
    const apiError = error as ApiError;
    return apiError.status >= 400 && apiError.status < 500 && 
           apiError.status !== 401 && apiError.status !== 403;
  }
  return false;
}

function isErrorWithStatus(error: unknown, status: number): boolean {
  if (typeof error === 'object' && error !== null) {
    const apiError = error as ApiError;
    return apiError.status === status;
  }
  return false;
}

export function getFriendlyErrorMessage(error: unknown, defaultMessage: string = '操作失败'): string {
  if (isAuthError(error)) {
    return '需要登录才能执行此操作';
  }
  
  if (isForbiddenError(error)) {
    return '您没有权限执行此操作';
  }
  
  if (isServerError(error)) {
    return '服务器错误，请稍后重试';
  }
  
  const errorMessage = extractErrorMessage(error);
  return errorMessage || defaultMessage;
}

/**
 * Mutation 错误处理配置
 */
export interface MutationErrorHandlerOptions {
  operationName: string;
  customMessages?: {
    auth?: string;
    forbidden?: string;
    server?: string;
    client?: string;
    default?: string;
  };
  showDetails?: boolean;
}

/**
 * 消息提示接口（用于解耦，避免循环依赖）
 */
export interface MessageApi {
  error: (content: string) => void;
  success: (content: string) => void;
  warning: (content: string) => void;
  info: (content: string) => void;
}

/**
 * 创建统一的 Mutation 错误处理函数
 */
export function createMutationErrorHandler(
  message: MessageApi,
  options: MutationErrorHandlerOptions
) {
  return (error: unknown) => {
    const {
      operationName,
      customMessages = {},
      showDetails = import.meta.env.DEV,
    } = options;

    if (isAuthError(error)) {
      message.error(customMessages.auth || '需要登录才能执行此操作');
      return;
    }

    if (isForbiddenError(error)) {
      message.error(customMessages.forbidden || '您没有权限执行此操作');
      return;
    }

    if (isServerError(error)) {
      message.error(customMessages.server || '服务器错误，请稍后重试');
      return;
    }

    const errorMessage = extractErrorMessage(error);
    const friendlyMessage = customMessages.client || 
                           customMessages.default || 
                           `${operationName}失败${showDetails && errorMessage ? `: ${errorMessage}` : ''}`;
    
    message.error(friendlyMessage);
  };
}

