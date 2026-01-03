"""
FastAPI 应用入口
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import sys
from pathlib import Path
import logging
import os

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.core.config import settings
from backend.app.core.security import setup_cors
from backend.app.api.v1.api import api_router
from backend.app.utils import setup_logger

logger = setup_logger(__name__)

# 全局调度器实例
scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理（启动和关闭事件）"""
    global scheduler
    
    # 启动事件
    logger.info("🚀 应用启动中...")
    
    # 可选：启动定时任务调度器
    # 如果环境变量 ENABLE_SCHEDULER=true，则启动调度器
    if os.getenv("ENABLE_SCHEDULER", "false").lower() == "true":
        try:
            from backend.app.services.scheduler import create_scheduler
            scheduler = create_scheduler()
            logger.info("✅ 定时任务调度器已启动")
        except Exception as e:
            logger.error(f"❌ 启动定时任务调度器失败: {e}", exc_info=True)
    else:
        logger.info("ℹ️  定时任务调度器未启用（设置 ENABLE_SCHEDULER=true 启用）")
    
    yield
    
    # 关闭事件
    logger.info("⏹️  应用关闭中...")
    
    if scheduler:
        try:
            scheduler.shutdown()
            logger.info("✅ 定时任务调度器已关闭")
        except Exception as e:
            logger.error(f"❌ 关闭定时任务调度器失败: {e}", exc_info=True)
    
    logger.info("✅ 应用已关闭")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,  # 使用新的 lifespan 事件处理器
)

# 配置 CORS
setup_cors(app)

# 注册路由
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """根路径"""
    return JSONResponse({
        "message": "AI News Tracker API",
        "version": settings.VERSION,
        "docs": "/docs",
    })


@app.get("/health")
async def health_check():
    """健康检查"""
    return JSONResponse({"status": "healthy"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )

