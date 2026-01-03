"""
采集相关 API 端点
"""
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import sys
from pathlib import Path
import threading

# 添加项目根目录到路径
# __file__ = backend/app/api/v1/endpoints/collection.py
# 需要 6 个 parent 到达项目根目录
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.db.repositories import CollectionTaskRepository
from backend.app.db.models import CollectionTask
from backend.app.core.dependencies import get_database, get_collection_service
from backend.app.schemas.collection import (
    CollectionTask as CollectionTaskSchema,
    CollectionTaskCreate,
    CollectionTaskStatus,
    CollectionStats,
)
from backend.app.services.collector import CollectionService
from backend.app.db import get_db

router = APIRouter()

# 全局变量存储当前运行的任务
_running_tasks = {}
_task_lock = threading.Lock()


def _run_collection_background(
    task_id: int,
    enable_ai: bool,
    collection_service: CollectionService,
):
    """后台运行采集任务"""
    try:
        db = get_db()
        
        # 执行采集
        stats = collection_service.collect_all(
            enable_ai_analysis=enable_ai,
            task_id=task_id,
        )
        
        # 更新任务状态
        with db.get_session() as session:
            task = session.query(CollectionTask).filter(CollectionTask.id == task_id).first()
            if task:
                task.status = "completed"
                task.new_articles_count = stats.get('new_articles', 0)
                task.total_sources = stats.get('sources_success', 0) + stats.get('sources_error', 0)
                task.success_sources = stats.get('sources_success', 0)
                task.failed_sources = stats.get('sources_error', 0)
                task.duration = stats.get('duration', 0)
                task.completed_at = datetime.now()
                task.ai_analyzed_count = stats.get('analyzed_count', 0)
                session.commit()
        
        # 从运行任务中移除
        with _task_lock:
            if task_id in _running_tasks:
                del _running_tasks[task_id]
                
    except Exception as e:
        # 更新任务状态为错误
        db = get_db()
        with db.get_session() as session:
            task = session.query(CollectionTask).filter(CollectionTask.id == task_id).first()
            if task:
                task.status = "error"
                task.error_message = str(e)
                task.completed_at = datetime.now()
                session.commit()
        
        # 从运行任务中移除
        with _task_lock:
            if task_id in _running_tasks:
                del _running_tasks[task_id]


@router.post("/start", response_model=CollectionTaskSchema)
async def start_collection(
    request: CollectionTaskCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_database),
    collection_service: CollectionService = Depends(get_collection_service),
):
    """启动采集任务"""
    # 检查是否有正在运行的任务
    with _task_lock:
        if _running_tasks:
            raise HTTPException(
                status_code=400,
                detail="已有采集任务正在运行，请等待完成后再启动新任务"
            )
    
    # 创建任务记录
    task = CollectionTask(
        status="running",
        ai_enabled=request.enable_ai,
        started_at=datetime.now(),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # 在后台线程中运行采集
    thread = threading.Thread(
        target=_run_collection_background,
        args=(task.id, request.enable_ai, collection_service),
        daemon=True,
    )
    thread.start()
    
    # 记录运行中的任务
    with _task_lock:
        _running_tasks[task.id] = thread
    
    return CollectionTaskSchema.model_validate(task)


@router.get("/tasks", response_model=List[CollectionTaskSchema])
async def get_collection_tasks(
    limit: int = 50,
    db: Session = Depends(get_database),
):
    """获取采集历史"""
    tasks = CollectionTaskRepository.get_recent_tasks(db, limit=limit)
    return [CollectionTaskSchema.model_validate(task) for task in tasks]


@router.get("/tasks/{task_id}", response_model=CollectionTaskSchema)
async def get_collection_task(
    task_id: int,
    db: Session = Depends(get_database),
):
    """获取采集任务详情"""
    task = db.query(CollectionTask).filter(CollectionTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return CollectionTaskSchema.model_validate(task)


@router.get("/status", response_model=CollectionTaskStatus)
async def get_collection_status(
    db: Session = Depends(get_database),
):
    """获取当前采集状态"""
    # 检查是否有运行中的任务
    with _task_lock:
        running_task_ids = list(_running_tasks.keys())
    
    if running_task_ids:
        # 获取最新的运行中任务
        task = db.query(CollectionTask).filter(
            CollectionTask.id == running_task_ids[0]
        ).first()
        if task:
            return CollectionTaskStatus(
                task_id=task.id,
                status=task.status,
                message="采集进行中...",
            )
    
    # 获取最新的任务
    latest_task = CollectionTaskRepository.get_latest_task(db)
    if latest_task:
        if latest_task.status == "completed":
            message = f"✅ 采集完成！新增 {latest_task.new_articles_count} 篇文章，耗时 {latest_task.duration or 0:.1f}秒"
        elif latest_task.status == "error":
            message = f"❌ 采集失败: {latest_task.error_message}"
        else:
            message = "采集进行中..."
        
        return CollectionTaskStatus(
            task_id=latest_task.id,
            status=latest_task.status,
            message=message,
        )
    
    return CollectionTaskStatus(
        task_id=0,
        status="idle",
        message="暂无采集任务",
    )

