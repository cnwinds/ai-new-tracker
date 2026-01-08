/**
 * 来源过滤开关组件
 * 按压式按钮设计 - 包含（按下）/排除（弹起）
 */
import { useState } from 'react';
import { useTheme } from '@/contexts/ThemeContext';
import { getThemeColor } from '@/utils/theme';

interface SourceFilterToggleProps {
  mode: 'include' | 'exclude';
  onModeChange: (mode: 'include' | 'exclude') => void;
}

// 将颜色转换为带透明度的 rgba 格式
function colorToRgba(color: string, alpha: number): string {
  // 如果已经是 rgba 格式，提取 RGB 值
  if (color.startsWith('rgba')) {
    const match = color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
    if (match) {
      return `rgba(${match[1]}, ${match[2]}, ${match[3]}, ${alpha})`;
    }
  }
  // 如果是十六进制格式
  if (color.startsWith('#')) {
    const r = parseInt(color.slice(1, 3), 16);
    const g = parseInt(color.slice(3, 5), 16);
    const b = parseInt(color.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }
  // 默认返回原色
  return color;
}

export default function SourceFilterToggle({ mode, onModeChange }: SourceFilterToggleProps) {
  const { theme } = useTheme();
  const [isAnimating, setIsAnimating] = useState(false);

  const handleToggle = () => {
    setIsAnimating(true);
    const newMode = mode === 'include' ? 'exclude' : 'include';
    onModeChange(newMode);
    setTimeout(() => setIsAnimating(false), 200);
  };

  const isInclude = mode === 'include';
  // 按下状态 = 包含，弹起状态 = 排除
  const isPressed = isInclude;

  // 使用主题色
  const primaryColor = getThemeColor(theme, 'primary');
  const textColor = getThemeColor(theme, 'text');
  const textSecondaryColor = getThemeColor(theme, 'textSecondary');
  const borderColor = getThemeColor(theme, 'border');

  // 按下状态（包含）：使用主题 primary 色
  // 弹起状态（排除）：使用更中性的颜色
  const pressedBg = primaryColor;
  const unpressedBg = theme === 'dark' 
    ? getThemeColor(theme, 'bgSecondary') 
    : getThemeColor(theme, 'bgContainer');

  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'stretch',
        height: '32px',
        borderTopLeftRadius: '6px',
        borderBottomLeftRadius: '6px',
        borderTopRightRadius: 0,
        borderBottomRightRadius: 0,
        background: getThemeColor(theme, 'bgElevated'),
        border: `1px solid ${borderColor}`,
        borderRight: 'none',
        overflow: 'hidden',
        userSelect: 'none',
        position: 'relative',
      }}
    >
      {/* 单一切换按钮 */}
      <button
        onClick={handleToggle}
        style={{
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '6px',
          padding: '0 16px',
          height: 'calc(100% + 2px)',
          width: 'calc(100% + 1px)',
          margin: '-1px',
          marginRight: 0,
          border: 'none',
          borderRadius: '6px 0 0 6px',
          background: isPressed ? pressedBg : unpressedBg,
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          boxShadow: isPressed
            ? 'inset 0 2px 4px rgba(0, 0, 0, 0.15), 0 1px 2px rgba(0, 0, 0, 0.05)'
            : '0 2px 4px rgba(0, 0, 0, 0.1)',
          outline: 'none',
          lineHeight: '1',
        }}
        title={isPressed ? '当前：包含模式（按下）' : '当前：排除模式（弹起）'}
      >
        {/* 图标 */}
        <svg
          width="14"
          height="14"
          viewBox="0 0 14 14"
          fill="none"
          style={{
            filter: isPressed ? 'drop-shadow(0 1px 1px rgba(0, 0, 0, 0.2))' : 'none',
            flexShrink: 0,
          }}
        >
          {isPressed ? (
            // 包含图标（+ 加号）
            <path
              d="M7 3.5V10.5M3.5 7H10.5"
              stroke="#ffffff"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          ) : (
            // 排除图标（× 叉号）
            <path
              d="M4.5 4.5L9.5 9.5M9.5 4.5L4.5 9.5"
              stroke={textSecondaryColor}
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          )}
        </svg>
        <span
          style={{
            fontSize: '14px',
            fontWeight: 600,
            color: isPressed ? '#ffffff' : textColor,
            textShadow: isPressed ? '0 1px 2px rgba(0, 0, 0, 0.2)' : 'none',
            lineHeight: '1',
            display: 'inline-block',
          }}
        >
          {isPressed ? '包含' : '排除'}
        </span>

        {/* 高光效果 */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '50%',
            borderRadius: '6px 0 0 0',
            background: 'linear-gradient(180deg, rgba(255, 255, 255, 0.15) 0%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />
      </button>

      {/* 点击波纹效果 */}
      {isAnimating && (
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            background: isPressed
              ? `radial-gradient(circle, ${colorToRgba(primaryColor, 0.3)} 0%, transparent 70%)`
              : `radial-gradient(circle, ${colorToRgba(textSecondaryColor, 0.2)} 0%, transparent 70%)`,
            animation: 'ripple-press 0.3s ease-out forwards',
            pointerEvents: 'none',
          }}
        />
      )}
    </div>
  );
}

// 添加 CSS 动画
const style = document.createElement('style');
style.innerHTML = `
  @keyframes ripple-press {
    0% {
      opacity: 0.8;
    }
    100% {
      opacity: 0;
    }
  }
`;
if (!document.head.querySelector('style[data-source-filter-toggle]')) {
  style.setAttribute('data-source-filter-toggle', 'true');
  document.head.appendChild(style);
}
