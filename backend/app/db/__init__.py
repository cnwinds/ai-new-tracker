"""
数据库初始化和管理
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path
from contextlib import contextmanager
from typing import Generator
import logging
import sys

# 添加项目根目录到路径
# __file__ = backend/app/db/__init__.py
# .parent = backend/app/db/
# .parent = backend/app/
# .parent = backend/
# .parent = 项目根目录
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.db.models import Base
from backend.app.db.repositories import (
    ArticleRepository,
    RSSSourceRepository,
    CollectionTaskRepository,
    CollectionLogRepository,
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, database_url: str = None):
        # 默认使用 backend/app/data/ai_news.db
        if database_url is None:
            from backend.app.core.settings import settings
            # 计算数据库路径
            db_path = Path(__file__).parent.parent / "data" / "ai_news.db"
            database_url = f"sqlite:///{db_path.absolute()}"
        else:
            # 如果提供了 database_url，使用它
            database_url = database_url
        
        self.database_url = database_url

        # 确保数据目录存在
        if database_url.startswith("sqlite:///"):
            db_path = database_url.replace("sqlite:///", "")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # 创建引擎
        self.engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
            echo=False,
        )

        # 创建会话工厂
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # 初始化数据库
        self.init_db()

    def init_db(self):
        """初始化数据库表"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ 数据库初始化成功")
        except Exception as e:
            logger.error(f"❌ 数据库初始化失败: {e}")
            raise

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """获取数据库会话（上下文管理器）"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def drop_all(self):
        """删除所有表（谨慎使用）"""
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("⚠️  所有数据库表已删除")


# 全局数据库实例
db_manager = None


def get_db() -> DatabaseManager:
    """获取数据库管理器实例"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager
