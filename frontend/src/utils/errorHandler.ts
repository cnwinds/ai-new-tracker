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
    
    // 优先使用 response.data.detail（FastAPI 标准错误格式）
    if (apiError.response?.data?.detail) {
      return apiError.response.data.detail;
    }
    
    // 其次使用 message
    if (apiError.message) {
      return apiError.message;
    }
    
    // 最后尝试从 data 中提取
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

/**
 * 检查是否为认证错误（401）
 */
export function isAuthError(error: unknown): boolean {
  if (typeof error === 'object' && error !== null) {
    const apiError = error as ApiError;
    return apiError.status === 401;
  }
  return false;
}

/**
 * 检查是否为权限错误（403）
 */
export function isForbiddenError(error: unknown): boolean {
  if (typeof error === 'object' && error !== null) {
    const apiError = error as ApiError;
    return apiError.status === 403;
  }
  return false;
}

/**
 * 检查是否为服务器错误（5xx）
 */
export function isServerError(error: unknown): boolean {
  if (typeof error === 'object' && error !== null) {
    const apiError = error as ApiError;
    return apiError.status >= 500 && apiError.status < 600;
  }
  return false;
}

/**
 * 检查是否为客户端错误（4xx，除了401和403）
 */
export function isClientError(error: unknown): boolean {
  if (typeof error === 'object' && error !== null) {
    const apiError = error as ApiError;
    return apiError.status >= 400 && apiError.status < 500 && 
           apiError.status !== 401 && apiError.status !== 403;
  }
  return false;
}

/**
 * 获取友好的错误消息
 */
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
  /** 操作名称（用于生成默认错误消息） */
  operationName: string;
  /** 自定义错误消息映射 */
  customMessages?: {
    auth?: string;
    forbidden?: string;
    server?: string;
    client?: string;
    default?: string;
  };
  /** 是否显示详细错误信息（默认：生产环境不显示，开发环境显示） */
  showDetails?: boolean;
}

/**
 * 创建统一的 Mutation 错误处理函数
 */
export function createMutationErrorHandler(
  message: ReturnType<typeof useMessage>,
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

    // 客户端错误或未知错误
    const errorMessage = extractErrorMessage(error);
    const friendlyMessage = customMessages.client || 
                           customMessages.default || 
                           `${operationName}失败${showDetails && errorMessage ? `: ${errorMessage}` : ''}`;
    
    message.error(friendlyMessage);
  };
}

/**
 * Hook: 创建统一的错误处理函数
 */
import { useMessage } from '@/hooks/useMessage';

export function useErrorHandler() {
  const message = useMessage();

  /**
   * 处理 Mutation 错误
   */
  const handleMutationError = (
    error: unknown,
    options: MutationErrorHandlerOptions
  ) => {
    createMutationErrorHandler(message, options)(error);
  };

  /**
   * 创建 Mutation 错误处理函数（用于 useMutation 的 onError）
   */
  const createErrorHandler = (options: MutationErrorHandlerOptions) => {
    return (error: unknown) => {
      handleMutationError(error, options);
    };
  };

  /**
   * 显示错误消息
   */
  const showError = (error: unknown, defaultMessage?: string) => {
    const errorMessage = getFriendlyErrorMessage(error, defaultMessage);
    message.error(errorMessage);
  };

  /**
   * 显示成功消息
   */
  const showSuccess = (msg: string) => {
    message.success(msg);
  };

  /**
   * 显示警告消息
   */
  const showWarning = (msg: string) => {
    message.warning(msg);
  };

  /**
   * 显示信息消息
   */
  const showInfo = (msg: string) => {
    message.info(msg);
  };

  return {
    handleMutationError,
    createErrorHandler,
    showError,
    showSuccess,
    showWarning,
    showInfo,
    isAuthError,
    isForbiddenError,
    isServerError,
    isClientError,
    extractErrorMessage,
    getFriendlyErrorMessage,
  };
}
