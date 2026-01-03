"""
摘要相关的 Pydantic 模型
"""
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, ConfigDict


class DailySummaryBase(BaseModel):
    """每日摘要基础模型"""
    summary_type: str = Field(..., description="摘要类型: daily/weekly")
    summary_date: datetime
    start_date: datetime
    end_date: datetime
    summary_content: str
    total_articles: int = 0
    high_importance_count: int = 0
    medium_importance_count: int = 0
    key_topics: Optional[List[str]] = None
    recommended_articles: Optional[List[Dict]] = None


class DailySummaryCreate(DailySummaryBase):
    """创建摘要模型"""
    model_used: Optional[str] = None
    generation_time: Optional[float] = None
    
    model_config = ConfigDict(
        protected_namespaces=(),  # 允许使用 model_ 开头的字段名
    )


class DailySummary(DailySummaryBase):
    """摘要响应模型"""
    id: int
    model_used: Optional[str] = None
    generation_time: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        protected_namespaces=(),  # 允许使用 model_ 开头的字段名
    )


class SummaryGenerateRequest(BaseModel):
    """生成摘要请求"""
    summary_type: str = Field("daily", description="摘要类型: daily/weekly")
    limit: int = Field(20, ge=1, le=50, description="文章数量限制")
    hours: int = Field(24, ge=1, description="时间范围（小时）")

