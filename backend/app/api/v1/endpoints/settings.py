"""
配置相关 API 端点
"""
from fastapi import APIRouter, Depends
import sys
from pathlib import Path

# 添加项目根目录到路径
# __file__ = backend/app/api/v1/endpoints/settings.py
# 需要 6 个 parent 到达项目根目录
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.schemas.settings import (
    CollectionSettings, 
    AutoCollectionSettings, 
    SummarySettings,
    LLMSettings,
    CollectorSettings
)
from backend.app.core.settings import settings

router = APIRouter()


@router.get("/collection", response_model=CollectionSettings)
async def get_collection_settings():
    """获取采集配置"""
    # 确保从数据库加载最新配置
    settings.load_settings_from_db()
    return CollectionSettings(
        max_article_age_days=settings.MAX_ARTICLE_AGE_DAYS,
        max_analysis_age_days=settings.MAX_ANALYSIS_AGE_DAYS,
    )


@router.put("/collection", response_model=CollectionSettings)
async def update_collection_settings(
    new_settings: CollectionSettings,
):
    """更新采集配置"""
    success = settings.save_collection_settings(
        max_article_age_days=new_settings.max_article_age_days,
        max_analysis_age_days=new_settings.max_analysis_age_days,
    )
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="保存配置失败")
    
    return CollectionSettings(
        max_article_age_days=settings.MAX_ARTICLE_AGE_DAYS,
        max_analysis_age_days=settings.MAX_ANALYSIS_AGE_DAYS,
    )


@router.get("/auto-collection", response_model=AutoCollectionSettings)
async def get_auto_collection_settings():
    """获取自动采集配置"""
    # 确保从数据库加载最新配置
    settings.load_settings_from_db()
    return AutoCollectionSettings(
        enabled=settings.AUTO_COLLECTION_ENABLED,
        interval_hours=settings.COLLECTION_INTERVAL_HOURS,
        max_articles_per_source=settings.MAX_ARTICLES_PER_SOURCE,
        request_timeout=settings.REQUEST_TIMEOUT,
    )


@router.put("/auto-collection", response_model=AutoCollectionSettings)
async def update_auto_collection_settings(
    new_settings: AutoCollectionSettings,
):
    """更新自动采集配置"""
    success = settings.save_auto_collection_settings(
        enabled=new_settings.enabled,
        interval_hours=new_settings.interval_hours,
        max_articles_per_source=new_settings.max_articles_per_source,
        request_timeout=new_settings.request_timeout,
    )
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="保存自动采集配置失败")
    
    # 如果调度器正在运行，更新采集任务
    try:
        from backend.app.main import scheduler
        if scheduler:
            # 如果启用了自动采集，更新或添加任务
            if new_settings.enabled:
                interval_hours = settings.get_auto_collection_interval_hours()
                if interval_hours:
                    scheduler.add_collection_job(interval_hours)
            else:
                # 如果禁用了，移除任务
                try:
                    scheduler.scheduler.remove_job("collection_job")
                except:
                    pass
    except Exception as e:
        # 如果调度器未运行或更新失败，记录日志但不影响配置保存
        import logging
        logging.getLogger(__name__).warning(f"更新调度器任务失败: {e}")
    
    return AutoCollectionSettings(
        enabled=settings.AUTO_COLLECTION_ENABLED,
        interval_hours=settings.COLLECTION_INTERVAL_HOURS,
        max_articles_per_source=settings.MAX_ARTICLES_PER_SOURCE,
        request_timeout=settings.REQUEST_TIMEOUT,
    )


@router.get("/summary", response_model=SummarySettings)
async def get_summary_settings():
    """获取总结配置"""
    # 确保从数据库加载最新配置
    settings.load_settings_from_db()
    return SummarySettings(
        daily_summary_enabled=settings.DAILY_SUMMARY_ENABLED,
        daily_summary_time=settings.DAILY_SUMMARY_TIME,
        weekly_summary_enabled=settings.WEEKLY_SUMMARY_ENABLED,
        weekly_summary_time=settings.WEEKLY_SUMMARY_TIME,
    )


@router.put("/summary", response_model=SummarySettings)
async def update_summary_settings(
    new_settings: SummarySettings,
):
    """更新总结配置"""
    success = settings.save_summary_settings(
        daily_enabled=new_settings.daily_summary_enabled,
        daily_time=new_settings.daily_summary_time,
        weekly_enabled=new_settings.weekly_summary_enabled,
        weekly_time=new_settings.weekly_summary_time,
    )
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="保存总结配置失败")
    
    # 如果调度器正在运行，更新总结任务
    try:
        from backend.app.main import scheduler
        if scheduler:
            # 更新每日总结任务
            if new_settings.daily_summary_enabled:
                cron_expr = settings.get_daily_summary_cron()
                if cron_expr:
                    scheduler.add_daily_summary_job(cron_expr)
            else:
                try:
                    scheduler.scheduler.remove_job("daily_summary_job")
                except:
                    pass
            
            # 更新每周总结任务
            if new_settings.weekly_summary_enabled:
                cron_expr = settings.get_weekly_summary_cron()
                if cron_expr:
                    scheduler.add_weekly_summary_job(cron_expr)
            else:
                try:
                    scheduler.scheduler.remove_job("weekly_summary_job")
                except:
                    pass
    except Exception as e:
        # 如果调度器未运行或更新失败，记录日志但不影响配置保存
        import logging
        logging.getLogger(__name__).warning(f"更新调度器任务失败: {e}")
    
    return SummarySettings(
        daily_summary_enabled=settings.DAILY_SUMMARY_ENABLED,
        daily_summary_time=settings.DAILY_SUMMARY_TIME,
        weekly_summary_enabled=settings.WEEKLY_SUMMARY_ENABLED,
        weekly_summary_time=settings.WEEKLY_SUMMARY_TIME,
    )


@router.get("/llm", response_model=LLMSettings)
async def get_llm_settings():
    """获取LLM配置"""
    # 确保从数据库加载最新配置
    settings.load_settings_from_db()
    return LLMSettings(
        openai_api_key=settings.OPENAI_API_KEY,
        openai_api_base=settings.OPENAI_API_BASE,
        openai_model=settings.OPENAI_MODEL,
        openai_embedding_model=settings.OPENAI_EMBEDDING_MODEL,
    )


@router.put("/llm", response_model=LLMSettings)
async def update_llm_settings(
    new_settings: LLMSettings,
):
    """更新LLM配置"""
    success = settings.save_llm_settings(
        api_key=new_settings.openai_api_key,
        api_base=new_settings.openai_api_base,
        model=new_settings.openai_model,
        embedding_model=new_settings.openai_embedding_model,
    )
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="保存LLM配置失败")
    
    return LLMSettings(
        openai_api_key=settings.OPENAI_API_KEY,
        openai_api_base=settings.OPENAI_API_BASE,
        openai_model=settings.OPENAI_MODEL,
        openai_embedding_model=settings.OPENAI_EMBEDDING_MODEL,
    )


@router.get("/collector", response_model=CollectorSettings)
async def get_collector_settings():
    """获取采集器配置"""
    # 确保从数据库加载最新配置
    settings.load_settings_from_db()
    return CollectorSettings(
        collection_interval_hours=settings.COLLECTION_INTERVAL_HOURS,
        max_articles_per_source=settings.MAX_ARTICLES_PER_SOURCE,
        request_timeout=settings.REQUEST_TIMEOUT,
    )


@router.put("/collector", response_model=CollectorSettings)
async def update_collector_settings(
    new_settings: CollectorSettings,
):
    """更新采集器配置"""
    success = settings.save_collector_settings(
        collection_interval_hours=new_settings.collection_interval_hours,
        max_articles_per_source=new_settings.max_articles_per_source,
        request_timeout=new_settings.request_timeout,
    )
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="保存采集器配置失败")
    
    return CollectorSettings(
        collection_interval_hours=settings.COLLECTION_INTERVAL_HOURS,
        max_articles_per_source=settings.MAX_ARTICLES_PER_SOURCE,
        request_timeout=settings.REQUEST_TIMEOUT,
    )

