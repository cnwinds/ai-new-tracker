"""
数据库会话管理（复用现有实现）
"""
from backend.app.db import get_db, DatabaseManager


def get_db_manager() -> DatabaseManager:
    """获取数据库管理器"""
    return get_db()

