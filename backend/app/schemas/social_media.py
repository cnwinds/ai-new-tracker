"""
社交平台配置Schema
"""
from pydantic import BaseModel, field_serializer
from typing import Optional
from datetime import datetime


class SocialMediaSettings(BaseModel):
    """社交平台采集配置"""
    youtube_enabled: bool = False
    tiktok_enabled: bool = False
    twitter_enabled: bool = False
    reddit_enabled: bool = False
    youtube_api_key: Optional[str] = None
    tiktok_api_key: Optional[str] = None
    twitter_api_key: Optional[str] = None
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_user_agent: Optional[str] = None


class SocialMediaCollectionRequest(BaseModel):
    """社交平台采集请求"""
    youtube_enabled: bool = True
    tiktok_enabled: bool = True
    twitter_enabled: bool = True
    reddit_enabled: bool = True

    # 采集参数
    query: str = "AI"
    max_results: int = 50

    # YouTube参数
    youtube_min_view_count: int = 200000
    youtube_max_days: int = 1

    # TikTok参数
    tiktok_min_viral_score: float = 8.0
    tiktok_max_days: int = 14

    # Twitter参数
    twitter_min_view_count: int = 10000
    twitter_min_engagement_score: int = 1000

    # Reddit参数
    reddit_min_upvotes: int = 50
    reddit_max_days: int = 1


class SocialMediaReportRequest(BaseModel):
    """社交平台报告生成请求"""
    youtube_enabled: bool = True
    tiktok_enabled: bool = True
    twitter_enabled: bool = True
    reddit_enabled: bool = True
    date: Optional[str] = None  # YYYY-MM-DD格式


class SocialMediaPostResponse(BaseModel):
    """社交平台帖子响应"""
    id: int
    platform: str
    post_id: str
    title: Optional[str] = None
    title_zh: Optional[str] = None
    content: Optional[str] = None
    author_name: Optional[str] = None
    author_url: Optional[str] = None
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    viral_score: Optional[float] = None
    post_url: str
    published_at: Optional[str] = None
    collected_at: str
    has_value: Optional[bool] = None

    class Config:
        from_attributes = True


class SocialMediaReportResponse(BaseModel):
    """社交平台报告响应"""
    id: int
    report_date: datetime
    youtube_count: int
    tiktok_count: int
    twitter_count: int
    reddit_count: int
    total_count: int
    report_content: str
    youtube_enabled: bool
    tiktok_enabled: bool
    twitter_enabled: bool
    reddit_enabled: bool
    created_at: datetime

    @field_serializer('report_date', 'created_at')
    def serialize_datetime(self, dt: datetime, _info) -> str:
        """序列化datetime对象为ISO格式字符串"""
        if dt is None:
            return ""
        return dt.isoformat()

    class Config:
        from_attributes = True


class SocialMediaStatsResponse(BaseModel):
    """社交平台统计响应"""
    total_posts: int
    youtube_count: int
    tiktok_count: int
    twitter_count: int
    reddit_count: int
    today_posts: int
    week_posts: int
