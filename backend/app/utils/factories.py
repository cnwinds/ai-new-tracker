"""
工厂函数模块 - 用于创建通用对象实例
"""
from typing import Optional
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.services.analyzer.ai_analyzer import AIAnalyzer
from backend.app.core.settings import settings


def create_ai_analyzer(api_key: Optional[str] = None) -> Optional[AIAnalyzer]:
    """
    创建AI分析器实例

    Args:
        api_key: OpenAI API密钥（可选，默认从配置读取）

    Returns:
        AI分析器实例，如果未配置API密钥则返回None
    """
    key = api_key or settings.OPENAI_API_KEY
    if not key:
        return None

    return AIAnalyzer(
        api_key=key,
        base_url=settings.OPENAI_API_BASE,
        model=settings.OPENAI_MODEL,
    )
