"""
FastAPI 应用配置
"""
import os
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.core.settings import settings as app_settings


class Settings:
    """FastAPI 应用配置"""
    
    # API 配置
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI News Tracker API"
    VERSION: str = "2.0.0"
    
    # CORS 配置
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",  # Vite 默认端口
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    
    # 服务器配置
    HOST: str = app_settings.WEB_HOST
    PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # 数据库配置（复用现有配置）
    DATABASE_URL: str = app_settings.DATABASE_URL
    
    # WebSocket 配置
    WS_HEARTBEAT_INTERVAL: int = 30  # 秒


settings = Settings()

