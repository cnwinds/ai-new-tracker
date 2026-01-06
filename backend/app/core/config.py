"""
FastAPI 应用配置
"""
import os
from typing import List

from backend.app.core.settings import settings as app_settings


class Settings:
    """FastAPI 应用配置"""
    
    # API 配置
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI News Tracker API"
    VERSION: str = "2.0.0"
    
    # CORS 配置
    # 从环境变量读取，如果没有设置则允许所有来源（开发环境）
    _cors_origins = os.getenv("BACKEND_CORS_ORIGINS", "")
    if _cors_origins:
        # 如果环境变量设置了，使用环境变量的值（逗号分隔）
        BACKEND_CORS_ORIGINS: List[str] = [origin.strip() for origin in _cors_origins.split(",")]
    else:
        # 默认允许所有来源（开发环境）
        BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # 服务器配置
    HOST: str = app_settings.WEB_HOST
    PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # 数据库配置（复用现有配置）
    DATABASE_URL: str = app_settings.DATABASE_URL
    
    # WebSocket 配置
    WS_HEARTBEAT_INTERVAL: int = 30  # 秒


settings = Settings()

