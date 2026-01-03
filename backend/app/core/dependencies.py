"""
依赖注入
"""
from typing import Generator
from sqlalchemy.orm import Session
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.db import get_db
from backend.app.services.collector import CollectionService
from backend.app.utils import create_ai_analyzer


def get_database() -> Generator[Session, None, None]:
    """获取数据库会话"""
    db = get_db()
    with db.get_session() as session:
        yield session


def get_collection_service() -> CollectionService:
    """获取采集服务实例"""
    ai_analyzer = create_ai_analyzer()
    return CollectionService(ai_analyzer=ai_analyzer)

