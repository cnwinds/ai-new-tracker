/**
 * 错误处理 Hook
 * 提供统一的错误处理功能
 */
import { useMessage } from './useMessage';
import {
  createMutationErrorHandler,
  type MutationErrorHandlerOptions,
  type MessageApi,
  isAuthError,
  isForbiddenError,
  isServerError,
  isClientError,
  extractErrorMessage,
  getFriendlyErrorMessage,
} from '@/utils/errorHandler';

export function useErrorHandler() {
  const message = useMessage();

  const handleMutationError = (
    error: unknown,
    options: MutationErrorHandlerOptions
  ) => {
    createMutationErrorHandler(message as MessageApi, options)(error);
  };

  const createErrorHandler = (options: MutationErrorHandlerOptions) => {
    return (error: unknown) => {
      handleMutationError(error, options);
    };
  };

  const showError = (error: unknown, defaultMessage?: string) => {
    const errorMessage = getFriendlyErrorMessage(error, defaultMessage);
    message.error(errorMessage);
  };

  const showSuccess = (msg: string) => {
    message.success(msg);
  };

  const showWarning = (msg: string) => {
    message.warning(msg);
  };

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
