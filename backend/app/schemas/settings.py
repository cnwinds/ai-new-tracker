"""
配置相关的 Pydantic 模型
"""
from pydantic import BaseModel, Field


class CollectionSettings(BaseModel):
    """采集配置模型"""
    max_article_age_days: int = Field(..., ge=0, description="文章采集最大天数")
    max_analysis_age_days: int = Field(..., ge=0, description="AI分析最大天数")


class AutoCollectionSettings(BaseModel):
    """自动采集配置模型"""
    enabled: bool = Field(default=False, description="是否启用自动采集")
    time: str = Field(default="09:00", description="每日自动采集时间（格式：HH:MM，如09:00）")


class SummarySettings(BaseModel):
    """总结配置模型"""
    daily_summary_enabled: bool = Field(default=True, description="是否启用每日总结")
    daily_summary_time: str = Field(default="09:00", description="每日总结时间（格式：HH:MM，如09:00）")
    weekly_summary_enabled: bool = Field(default=True, description="是否启用每周总结")
    weekly_summary_time: str = Field(default="09:00", description="每周总结时间（格式：HH:MM，如09:00，在周六执行）")


