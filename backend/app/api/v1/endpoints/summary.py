"""
摘要相关 API 端点
"""
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import sys
from pathlib import Path

# 添加项目根目录到路径
# __file__ = backend/app/api/v1/endpoints/summary.py
# 需要 6 个 parent 到达项目根目录
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.db.models import DailySummary
from backend.app.core.dependencies import get_database, get_collection_service
from backend.app.schemas.summary import (
    DailySummary as DailySummarySchema,
    SummaryGenerateRequest,
)
from backend.app.services.collector import CollectionService
from backend.app.utils import create_ai_analyzer
from backend.app.db import get_db

router = APIRouter()


@router.get("", response_model=List[DailySummarySchema])
async def get_summaries(
    limit: int = 50,
    db: Session = Depends(get_database),
):
    """获取历史摘要列表"""
    summaries = (
        db.query(DailySummary)
        .order_by(DailySummary.summary_date.desc())
        .limit(limit)
        .all()
    )
    return [DailySummarySchema.model_validate(s) for s in summaries]


@router.get("/{summary_id}", response_model=DailySummarySchema)
async def get_summary(
    summary_id: int,
    db: Session = Depends(get_database),
):
    """获取摘要详情"""
    summary = db.query(DailySummary).filter(DailySummary.id == summary_id).first()
    if not summary:
        raise HTTPException(status_code=404, detail="摘要不存在")
    return DailySummarySchema.model_validate(summary)


@router.post("/generate")
async def generate_summary(
    request: SummaryGenerateRequest,
    collection_service: CollectionService = Depends(get_collection_service),
    db: Session = Depends(get_database),
):
    """生成新摘要"""
    # 检查AI分析器
    ai_analyzer = create_ai_analyzer()
    if not ai_analyzer:
        raise HTTPException(status_code=400, detail="未配置AI分析器")
    
    # 获取文章
    db_manager = get_db()
    articles = collection_service.get_daily_summary(
        db_manager,
        limit=request.limit,
    )
    
    if not articles:
        raise HTTPException(status_code=404, detail="没有符合条件的文章")
    
    # 准备文章数据
    articles_data = []
    for article in articles:
        articles_data.append({
            "title": article.title,
            "content": article.content,
            "source": article.source,
            "published_at": article.published_at,
        })
    
    # 生成摘要
    try:
        summary_text = ai_analyzer.generate_daily_summary(
            articles_data,
            max_count=request.limit,
        )
        
        # 计算时间范围
        now = datetime.now()
        start_date = now - timedelta(hours=request.hours)
        end_date = now
        
        # 统计信息
        high_count = sum(1 for a in articles if a.importance == "high")
        medium_count = sum(1 for a in articles if a.importance == "medium")
        
        # 提取关键主题（从文章标签中）
        all_topics = []
        for article in articles:
            if article.tags:
                all_topics.extend(article.tags)
        key_topics = list(set(all_topics))[:10]  # 取前10个
        
        # 推荐文章
        recommended = []
        for article in articles[:5]:  # 前5篇
            if article.importance in ["high", "medium"]:
                recommended.append({
                    "id": article.id,
                    "title": article.title,
                    "reason": f"重要性: {article.importance}",
                })
        
        # 保存摘要
        summary = DailySummary(
            summary_type=request.summary_type,
            summary_date=now,
            start_date=start_date,
            end_date=end_date,
            summary_content=summary_text,
            total_articles=len(articles),
            high_importance_count=high_count,
            medium_importance_count=medium_count,
            key_topics=key_topics,
            recommended_articles=recommended,
            model_used=ai_analyzer.model,
        )
        db.add(summary)
        db.commit()
        db.refresh(summary)
        
        return DailySummarySchema.model_validate(summary)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"生成摘要失败: {str(e)}")

