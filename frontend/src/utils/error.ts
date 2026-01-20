/**
 * 错误处理相关的工具函数（已迁移到 errorHandler.ts，保留此文件以保持向后兼容）
 * @deprecated 请使用 @/utils/errorHandler 中的 useErrorHandler Hook
 */
export { 
  extractErrorMessage as getErrorMessage,
  isAuthError,
  getFriendlyErrorMessage,
  createMutationErrorHandler,
  useErrorHandler,
} from './errorHandler';
