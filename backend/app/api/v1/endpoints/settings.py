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

from backend.app.schemas.settings import CollectionSettings
from backend.app.core.settings import settings

router = APIRouter()


@router.get("/collection", response_model=CollectionSettings)
async def get_collection_settings():
    """获取采集配置"""
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

