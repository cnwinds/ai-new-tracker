"""
访问统计API端点
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, case
from pydantic import BaseModel

from backend.app.core.dependencies import get_database
from backend.app.api.v1.endpoints.auth import verify_token, TokenData
from backend.app.db.models import AccessLog

router = APIRouter()

# 中国时区（UTC+8）
CHINA_TZ = timezone(timedelta(hours=8))


class DailyAccessStats(BaseModel):
    """每日访问统计"""
    date: str  # YYYY-MM-DD
    page_views: int  # 页面浏览量
    unique_users: int  # 独立用户数
    clicks: int  # 点击量


class AccessStatsResponse(BaseModel):
    """访问统计响应"""
    daily_stats: list[DailyAccessStats]  # 每日统计列表
    total_page_views: int  # 总页面浏览量
    total_unique_users: int  # 总独立用户数
    total_clicks: int  # 总点击量
    avg_daily_page_views: float  # 平均日页面浏览量
    avg_daily_users: float  # 平均日独立用户数


@router.get("/access-stats", response_model=AccessStatsResponse)
async def get_access_stats(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    token_data: TokenData = Depends(verify_token),
    db: Session = Depends(get_database)
):
    """
    获取访问统计数据

    参数:
        days: 统计最近多少天的数据（默认30天，最大365天）

    返回:
        每日访问统计列表和汇总数据
    """
    try:
        # 计算日期范围 - 使用中国时区（UTC+8）
        # 获取中国时区的当前日期
        china_now = datetime.now(CHINA_TZ)
        end_date = china_now.date()
        start_date = end_date - timedelta(days=days-1)

        # 查询每日统计数据
        # 注意：access_date已经使用中国时区存储（在log_access中使用CHINA_TZ），
        # 所以直接使用DATE()函数提取日期即可
        date_expr = func.date(AccessLog.access_date)
        
        # 查询每日统计数据
        # 使用更清晰的方式：分别查询 page_view 和 click，然后在 Python 中合并
        # 这样可以避免复杂的 SQL case 语句，逻辑更清晰
        
        # 查询 page_view 的每日统计（包含独立用户数）
        page_view_query = (
            db.query(
                date_expr.label('date'),
                func.count().label('page_views'),
                func.count(func.distinct(AccessLog.user_id)).label('unique_users')
            )
            .filter(
                and_(
                    date_expr >= start_date,
                    date_expr <= end_date,
                    AccessLog.access_type == 'page_view'
                )
            )
            .group_by(date_expr)
        )
        
        # 查询 click 的每日统计
        click_query = (
            db.query(
                date_expr.label('date'),
                func.count().label('clicks')
            )
            .filter(
                and_(
                    date_expr >= start_date,
                    date_expr <= end_date,
                    AccessLog.access_type == 'click'
                )
            )
            .group_by(date_expr)
        )
        
        # 获取结果
        page_view_results = {row.date: row for row in page_view_query.all()}
        click_results = {row.date: row for row in click_query.all()}
        
        # 合并所有日期
        all_dates = set(page_view_results.keys()) | set(click_results.keys())
        daily_stats_list = []
        
        for date in sorted(all_dates):
            page_view_row = page_view_results.get(date)
            click_row = click_results.get(date)
            
            daily_stats_list.append({
                'date': date,
                'page_views': int(page_view_row.page_views) if page_view_row else 0,
                'unique_users': int(page_view_row.unique_users) if page_view_row else 0,
                'clicks': int(click_row.clicks) if click_row else 0
            })

        # 构建每日统计列表
        daily_stats = []
        total_page_views = 0
        total_clicks = 0

        for stat in daily_stats_list:
            date_str = str(stat['date'])
            page_views = stat['page_views']
            unique_users = stat['unique_users']
            clicks = stat['clicks']

            daily_stats.append(DailyAccessStats(
                date=date_str,
                page_views=page_views,
                unique_users=unique_users,
                clicks=clicks
            ))

            total_page_views += page_views
            total_clicks += clicks

        # 获取总独立用户数（需要单独查询，因为上面的count(distinct)是按天分组的）
        # 使用相同的日期表达式确保一致性
        total_users_query = (
            db.query(
                func.count(
                    func.distinct(AccessLog.user_id)
                )
            )
            .filter(
                and_(
                    date_expr >= start_date,
                    date_expr <= end_date,
                    AccessLog.access_type == 'page_view'
                )
            )
        )
        total_unique_users = total_users_query.scalar() or 0

        # 计算平均值
        avg_daily_page_views = round(total_page_views / days, 2) if days > 0 else 0
        avg_daily_users = round(total_unique_users / days, 2) if days > 0 else 0

        return AccessStatsResponse(
            daily_stats=daily_stats,
            total_page_views=total_page_views,
            total_unique_users=total_unique_users,
            total_clicks=total_clicks,
            avg_daily_page_views=avg_daily_page_views,
            avg_daily_users=avg_daily_users
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取访问统计失败: {str(e)}"
        )


@router.post("/log-access")
async def log_access(
    access_type: str = Query(..., description="访问类型: page_view/click/api_call"),
    page_path: Optional[str] = Query(None, description="页面路径"),
    action: Optional[str] = Query(None, description="具体操作"),
    user_id: Optional[str] = Query(None, description="用户标识（可选，默认使用匿名）"),
    db: Session = Depends(get_database)
):
    """
    记录访问日志（无需认证，用于前端埋点）

    参数:
        access_type: 访问类型（page_view/click/api_call）
        page_path: 页面路径（可选）
        action: 具体操作（可选）
        user_id: 用户标识（可选，未登录用户使用session_id或其他标识）
    """
    try:
        # 如果没有提供user_id，使用匿名标识
        if not user_id:
            user_id = "anonymous"

        # 创建访问日志记录 - 使用中国时区（UTC+8）
        china_now = datetime.now(CHINA_TZ).replace(tzinfo=None)  # 转换为naive datetime存储
        access_log = AccessLog(
            access_date=china_now,
            user_id=user_id,
            access_type=access_type,
            page_path=page_path,
            action=action
        )

        db.add(access_log)
        db.commit()

        return {"message": "访问日志记录成功", "id": access_log.id}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"记录访问日志失败: {str(e)}"
        )
