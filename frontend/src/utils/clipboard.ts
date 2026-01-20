/**
 * 剪贴板工具函数
 * 注意：此函数不直接使用 message，需要调用者传入回调函数
 */

export interface ClipboardCallbacks {
  onSuccess?: (message: string) => void;
  onInfo?: (message: string) => void;
}

/**
 * 复制文本到剪贴板
 * @param text 要复制的文本
 * @param callbacks 回调函数对象
 * @param successMessage 成功提示消息，默认为 '已复制到剪贴板'
 */
export async function copyToClipboard(
  text: string,
  callbacks?: ClipboardCallbacks,
  successMessage: string = '已复制到剪贴板'
): Promise<void> {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      callbacks?.onSuccess?.(successMessage);
      return;
    }
  } catch {
    // 如果 Clipboard API 失败，使用降级方案
  }

  // 降级方案：使用传统的 execCommand
  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.style.position = 'fixed';
  textarea.style.left = '-9999px';
  document.body.appendChild(textarea);
  textarea.select();
  
  try {
    const success = document.execCommand('copy');
    if (success) {
      callbacks?.onSuccess?.(successMessage);
    } else {
      callbacks?.onInfo?.(`文本内容: ${text}`);
    }
  } catch {
    callbacks?.onInfo?.(`文本内容: ${text}`);
  } finally {
    document.body.removeChild(textarea);
  }
}
