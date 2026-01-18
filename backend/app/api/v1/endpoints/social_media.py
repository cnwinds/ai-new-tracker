"""
社交平台相关 API 端点
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.api.v1.endpoints.settings import require_auth
from backend.app.core.dependencies import get_database
from backend.app.db.models import SocialMediaPost, SocialMediaReport
from backend.app.schemas.social_media import (
    SocialMediaCollectionRequest,
    SocialMediaReportRequest,
    SocialMediaPostResponse,
    SocialMediaReportResponse,
    SocialMediaStatsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# 全局采集器实例
_social_collector = None


def get_social_collector():
    """获取社交平台采集器实例（每次调用时重新加载配置）"""
    global _social_collector
    if _social_collector is None:
        from backend.app.services.social_media import SocialMediaCollector
        _social_collector = SocialMediaCollector()

    # 每次调用时从数据库重新加载配置
    from backend.app.core.settings import settings
    settings.load_social_media_settings()

    youtube_key = settings.YOUTUBE_API_KEY
    twitter_key = settings.TWITTER_API_KEY
    tiktok_key = settings.TIKTOK_API_KEY
    reddit_client_id = settings.REDDIT_CLIENT_ID
    reddit_client_secret = settings.REDDIT_CLIENT_SECRET
    reddit_user_agent = settings.REDDIT_USER_AGENT

    _social_collector.initialize(
        youtube_api_key=youtube_key,
        twitter_api_key=twitter_key,
        tiktok_api_key=tiktok_key,
        reddit_client_id=reddit_client_id,
        reddit_client_secret=reddit_client_secret,
        reddit_user_agent=reddit_user_agent
    )

    return _social_collector


@router.post("/collect", response_model=dict)
async def collect_social_media_posts(
    request: SocialMediaCollectionRequest,
    db: Session = Depends(get_database),
    current_user: str = Depends(require_auth),
):
    """采集社交平台热帖"""
    collector = get_social_collector()

    # 检查采集器是否已初始化
    if not any([collector.youtube_collector, collector.tiktok_collector, collector.twitter_collector, collector.reddit_collector]):
        raise HTTPException(
            status_code=400,
            detail="未配置任何社交平台API密钥,请先在设置中配置"
        )

    try:
        # 采集所有平台
        results = collector.collect_all_platforms(
            db=db,
            youtube_enabled=request.youtube_enabled and collector.youtube_collector is not None,
            tiktok_enabled=request.tiktok_enabled and collector.tiktok_collector is not None,
            twitter_enabled=request.twitter_enabled and collector.twitter_collector is not None,
            reddit_enabled=request.reddit_enabled and collector.reddit_collector is not None,
            query=request.query,
            max_results=request.max_results,
            min_view_count=request.youtube_min_view_count if request.youtube_enabled else None,
            min_viral_score=request.tiktok_min_viral_score if request.tiktok_enabled else None,
            max_days=request.tiktok_max_days if request.tiktok_enabled else None,
            min_engagement_score=request.twitter_min_engagement_score if request.twitter_enabled else None,
            reddit_min_upvotes=request.reddit_min_upvotes if request.reddit_enabled else None,
        )

        # 保存到数据库
        all_posts = []
        for platform, posts in results.items():
            all_posts.extend(posts)

        saved_posts = collector.save_posts(db, all_posts)

        # AI分析(异步执行)
        if saved_posts:
            asyncio.create_task(analyze_posts_async(collector, db, [p.id for p in saved_posts]))

        return {
            "message": "采集完成",
            "total_collected": len(all_posts),
            "total_saved": len(saved_posts),
            "youtube_count": len(results.get("youtube", [])),
            "tiktok_count": len(results.get("tiktok", [])),
            "twitter_count": len(results.get("twitter", [])),
            "reddit_count": len(results.get("reddit", [])),
        }

    except Exception as e:
        logger.error(f"采集失败: {e}")
        raise HTTPException(status_code=500, detail=f"采集失败: {str(e)}")


async def analyze_posts_async(collector, db, post_ids: List[int]):
    """异步分析帖子"""
    try:
        # 重新获取帖子对象
        posts = db.query(SocialMediaPost).filter(SocialMediaPost.id.in_(post_ids)).all()
        collector.analyze_posts(db, posts)
    except Exception as e:
        logger.error(f"异步分析失败: {e}")


@router.post("/report/generate", response_model=SocialMediaReportResponse)
async def generate_social_media_report(
    request: SocialMediaReportRequest,
    db: Session = Depends(get_database),
    current_user: str = Depends(require_auth),
):
    """生成社交平台热帖报告（基于采集的实时数据）"""
    collector = get_social_collector()

    if not collector.report_generator:
        raise HTTPException(status_code=400, detail="报告生成器未初始化")

    try:
        # 检查哪些平台已配置，只启用已配置的平台
        from backend.app.core.settings import settings
        settings.load_social_media_settings()

        youtube_enabled = request.youtube_enabled and collector.youtube_collector is not None
        tiktok_enabled = request.tiktok_enabled and collector.tiktok_collector is not None
        twitter_enabled = request.twitter_enabled and collector.twitter_collector is not None
        reddit_enabled = request.reddit_enabled and collector.reddit_collector is not None

        # 如果所有请求的平台都未配置，返回错误
        if not any([youtube_enabled, tiktok_enabled, twitter_enabled, reddit_enabled]):
            raise HTTPException(
                status_code=400,
                detail="没有已配置的社交平台，请在设置中配置至少一个平台的API密钥"
            )

        # 解析日期
        report_date = None
        is_realtime = False  # 标记是否为实时数据请求
        if request.date:
            try:
                report_date = datetime.strptime(request.date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误,应为YYYY-MM-DD")
        else:
            # 不传日期时，使用当前日期并标记为实时数据
            report_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            is_realtime = True

        # 采集数据（总是采集最新数据，确保报告基于实时采集结果）
        from datetime import timedelta

        # 计算采集时间范围
        # 实时数据：采集最近1天的数据
        # 历史日期：采集该日期当天的数据
        if is_realtime or report_date.date() == datetime.now().date():
            published_after = datetime.now() - timedelta(days=1)
            tiktok_max_days = 1
        else:
            # 历史日期：采集该日期当天的数据
            published_after = report_date
            tiktok_max_days = 1


        # 自动采集数据
        results = {
            "youtube": [],
            "tiktok": [],
            "twitter": [],
            "reddit": []
        }

        # 记录采集到的原始条数
        youtube_collected = 0
        tiktok_collected = 0
        twitter_collected = 0
        reddit_collected = 0

        # YouTube采集（使用query参数）
        if youtube_enabled and collector.youtube_collector:
            try:
                youtube_videos = collector.youtube_collector.search_videos(
                    query="AI",  # YouTube使用query
                    published_after=published_after,
                    max_results=50,
                    # min_view_count使用默认值200000
                )
                results["youtube"] = youtube_videos
                youtube_collected = len(youtube_videos)
            except Exception as e:
                logger.error(f"YouTube采集失败: {e}")

        # TikTok采集(使用keyword参数)
        if tiktok_enabled and collector.tiktok_collector:
            try:
                tiktok_videos = collector.tiktok_collector.search_videos(
                    keyword="AI",  # TikTok使用keyword
                    min_viral_score=8.0,
                    max_days=tiktok_max_days,  # 采集最近1天的视频
                    max_results=50,
                )
                results["tiktok"] = tiktok_videos
                tiktok_collected = len(tiktok_videos)
            except Exception as e:
                logger.error(f"TikTok采集失败: {e}")

        # Twitter采集(使用query参数)
        if twitter_enabled and collector.twitter_collector:
            try:
                twitter_tweets = collector.twitter_collector.search_tweets(
                    query="AI",  # Twitter使用query
                    query_type="Top",  # 根据n8n工作流配置
                    min_view_count=10000,
                    min_engagement_score=1000,
                    max_results=50,
                )
                results["twitter"] = twitter_tweets
                twitter_collected = len(twitter_tweets)
            except Exception as e:
                logger.error(f"Twitter采集失败: {e}")

        # Reddit采集（严格按照n8n工作流配置）
        if reddit_enabled and collector.reddit_collector:
            try:
                reddit_posts = collector.reddit_collector.search_posts(
                    subreddits=["ArtificialInteligence", "artificial"],  # n8n配置的AI版块
                    category="hot",  # n8n配置
                    time_range="day",  # n8n配置
                    min_upvotes=50,  # n8n配置
                    max_results=50,
                )
                results["reddit"] = reddit_posts
                reddit_collected = len(reddit_posts)
            except Exception as e:
                logger.error(f"Reddit采集失败: {e}")

        # 汇总采集数据
        all_posts = []
        for platform, posts in results.items():
            all_posts.extend(posts)

        if not all_posts:
            raise HTTPException(
                status_code=404,
                detail="未采集到任何数据，请检查API配置或稍后重试"
            )

        # 将字典转换为SocialMediaPost对象（临时对象，用于生成报告）
        temp_posts = []
        platform_counts = {"youtube": 0, "tiktok": 0, "twitter": 0, "reddit": 0}
        for post_data in all_posts:
            try:
                # 创建临时对象（不保存到数据库）
                temp_post = SocialMediaPost(**post_data)
                temp_posts.append(temp_post)
                platform = post_data.get("platform", "unknown")
                if platform in platform_counts:
                    platform_counts[platform] += 1
            except Exception as e:
                logger.warning(f"转换帖子数据失败: {e}")
                continue

        if not temp_posts:
            raise HTTPException(
                status_code=404,
                detail="转换帖子数据失败"
            )

        # 保存到数据库（作为缓存）
        saved_posts = collector.save_posts(db, all_posts)  # 保存原始字典数据

        # 从数据库加载已有的翻译和价值判断结果，填充到临时对象中
        # 这样可以避免对已存在的帖子重复调用LLM
        post_ids_by_platform = {}
        for temp_post in temp_posts:
            if temp_post.post_id:
                platform = temp_post.platform
                if platform not in post_ids_by_platform:
                    post_ids_by_platform[platform] = []
                post_ids_by_platform[platform].append(temp_post.post_id)

        # 批量查询已有的翻译和价值判断结果
        if post_ids_by_platform:
            for platform, post_ids in post_ids_by_platform.items():
                existing_posts = db.query(SocialMediaPost).filter(
                    SocialMediaPost.platform == platform,
                    SocialMediaPost.post_id.in_(post_ids)
                ).all()
                
                # 创建映射：post_id -> 数据库中的帖子对象
                existing_posts_map = {p.post_id: p for p in existing_posts}
                
                # 将数据库中的翻译和价值判断结果填充到临时对象
                for temp_post in temp_posts:
                    if temp_post.platform == platform and temp_post.post_id in existing_posts_map:
                        existing_post = existing_posts_map[temp_post.post_id]
                        # 如果数据库中有翻译结果，使用数据库中的
                        if existing_post.title_zh:
                            temp_post.title_zh = existing_post.title_zh
                        # 如果数据库中有价值判断结果，使用数据库中的
                        if existing_post.has_value is not None:
                            temp_post.has_value = existing_post.has_value

        # AI分析(异步执行) - 只对新保存的帖子进行分析
        if saved_posts:
            asyncio.create_task(analyze_posts_async(collector, db, [p.id for p in saved_posts]))

        # 生成报告（使用采集到的原始数据，而不是查询数据库）
        # 使用临时SocialMediaPost对象生成报告
        report = collector.report_generator.generate_daily_report(
            db=db,
            posts=temp_posts,  # 传入临时对象列表
            report_date=report_date,
            youtube_enabled=youtube_enabled,
            tiktok_enabled=tiktok_enabled,
            twitter_enabled=twitter_enabled,
            reddit_enabled=reddit_enabled,
        )

        if not report:
            raise HTTPException(status_code=404, detail="生成报告失败，数据可能为空")

        # 输出统一的采集日志（包含采集条数和AI过滤后保留条数）
        logger.info(
            f"YouTube: 采集{youtube_collected}条, 过滤后保留{report.youtube_count}条 | "
            f"TikTok: 采集{tiktok_collected}条, 过滤后保留{report.tiktok_count}条 | "
            f"Twitter: 采集{twitter_collected}条, 过滤后保留{report.twitter_count}条 | "
            f"Reddit: 采集{reddit_collected}条, 过滤后保留{report.reddit_count}条"
        )

        return SocialMediaReportResponse.model_validate(report)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成报告失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成报告失败: {str(e)}")


@router.get("/posts", response_model=List[SocialMediaPostResponse])
async def get_social_media_posts(
    platform: Optional[str] = Query(None, description="平台筛选"),
    min_viral_score: Optional[float] = Query(None, description="最小爆款分数"),
    has_value: Optional[bool] = Query(None, description="是否有信息价值"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_database),
):
    """获取社交平台帖子列表"""
    query = db.query(SocialMediaPost)

    # 平台筛选
    if platform:
        query = query.filter(SocialMediaPost.platform == platform)

    # 爆款分数筛选
    if min_viral_score is not None:
        query = query.filter(SocialMediaPost.viral_score >= min_viral_score)

    # 价值筛选
    if has_value is not None:
        query = query.filter(SocialMediaPost.has_value == has_value)

    # 排序和分页
    query = query.order_by(SocialMediaPost.collected_at.desc())
    query = query.offset(offset).limit(limit)

    posts = query.all()
    return [SocialMediaPostResponse.model_validate(p) for p in posts]


@router.get("/reports", response_model=List[SocialMediaReportResponse])
async def get_social_media_reports(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_database),
):
    """获取社交平台报告列表"""
    reports = (
        db.query(SocialMediaReport)
        .order_by(SocialMediaReport.report_date.desc())
        .limit(limit)
        .all()
    )
    return [SocialMediaReportResponse.model_validate(r) for r in reports]


@router.get("/reports/{report_id}", response_model=SocialMediaReportResponse)
async def get_social_media_report(
    report_id: int,
    db: Session = Depends(get_database),
):
    """获取报告详情"""
    report = db.query(SocialMediaReport).filter(SocialMediaReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    return SocialMediaReportResponse.model_validate(report)


@router.get("/stats", response_model=SocialMediaStatsResponse)
async def get_social_media_stats(
    db: Session = Depends(get_database),
):
    """获取社交平台统计数据"""
    from datetime import timedelta

    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)

    # 总数统计
    total_posts = db.query(SocialMediaPost).count()
    youtube_count = db.query(SocialMediaPost).filter(SocialMediaPost.platform == "youtube").count()
    tiktok_count = db.query(SocialMediaPost).filter(SocialMediaPost.platform == "tiktok").count()
    twitter_count = db.query(SocialMediaPost).filter(SocialMediaPost.platform == "twitter").count()
    reddit_count = db.query(SocialMediaPost).filter(SocialMediaPost.platform == "reddit").count()

    # 时间统计
    today_posts = db.query(SocialMediaPost).filter(
        SocialMediaPost.collected_at >= today_start
    ).count()
    week_posts = db.query(SocialMediaPost).filter(
        SocialMediaPost.collected_at >= week_start
    ).count()

    return SocialMediaStatsResponse(
        total_posts=total_posts,
        youtube_count=youtube_count,
        tiktok_count=tiktok_count,
        twitter_count=twitter_count,
        reddit_count=reddit_count,
        today_posts=today_posts,
        week_posts=week_posts,
    )


@router.delete("/posts/{post_id}")
async def delete_social_media_post(
    post_id: int,
    db: Session = Depends(get_database),
    current_user: str = Depends(require_auth),
):
    """删除帖子"""
    post = db.query(SocialMediaPost).filter(SocialMediaPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    db.delete(post)
    db.commit()

    return {"message": "帖子已删除", "post_id": post_id}


@router.delete("/reports/{report_id}")
async def delete_social_media_report(
    report_id: int,
    db: Session = Depends(get_database),
    current_user: str = Depends(require_auth),
):
    """删除报告"""
    report = db.query(SocialMediaReport).filter(SocialMediaReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    db.delete(report)
    db.commit()

    return {"message": "报告已删除", "report_id": report_id}
