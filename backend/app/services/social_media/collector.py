"""
社交平台热帖采集服务 - 统一入口
"""
import logging
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from backend.app.services.social_media.youtube_collector import YouTubeCollector
from backend.app.services.social_media.twitter_collector import TwitterCollector
from backend.app.services.social_media.tiktok_collector import TikTokCollector
from backend.app.services.social_media.reddit_collector import RedditCollector
from backend.app.services.social_media.report_generator import SocialMediaReportGenerator
from backend.app.db.models import SocialMediaPost
from backend.app.utils import create_ai_analyzer

logger = logging.getLogger(__name__)


class SocialMediaCollector:
    """社交平台热帖采集服务"""

    def __init__(self):
        """初始化采集服务"""
        self.youtube_collector = None
        self.twitter_collector = None
        self.tiktok_collector = None
        self.reddit_collector = None
        self.report_generator = None
        self.ai_analyzer = None

    def initialize(
        self,
        youtube_api_key: Optional[str] = None,
        twitter_api_key: Optional[str] = None,
        tiktok_api_key: Optional[str] = None,
        reddit_client_id: Optional[str] = None,
        reddit_client_secret: Optional[str] = None,
        reddit_user_agent: Optional[str] = None
    ):
        """
        初始化各个采集器

        Args:
            youtube_api_key: YouTube API密钥
            twitter_api_key: Twitter API密钥
            tiktok_api_key: TikTok API密钥
            reddit_client_id: Reddit客户端ID
            reddit_client_secret: Reddit客户端密钥
            reddit_user_agent: Reddit用户代理
        """
        if youtube_api_key:
            self.youtube_collector = YouTubeCollector(youtube_api_key)
            logger.info("YouTube采集器初始化成功, 过滤条件: 观看量>=200000")

        if twitter_api_key:
            self.twitter_collector = TwitterCollector(twitter_api_key)
            logger.info("Twitter采集器初始化成功, 过滤条件: 观看量>=10000 且 互动分数>=1000")

        if tiktok_api_key:
            self.tiktok_collector = TikTokCollector(tiktok_api_key)
            logger.info("TikTok采集器初始化成功, 过滤条件: 爆款指数>=8.0 且 发布时间<=7天")

        if reddit_client_id and reddit_client_secret and reddit_user_agent:
            self.reddit_collector = RedditCollector(
                client_id=reddit_client_id,
                client_secret=reddit_client_secret,
                user_agent=reddit_user_agent
            )
            logger.info("Reddit采集器初始化成功, 过滤条件: 24小时内 且 点赞数>=50")

        # 初始化AI分析器
        self.ai_analyzer = create_ai_analyzer()
        if self.ai_analyzer:
            self.report_generator = SocialMediaReportGenerator(self.ai_analyzer)
            logger.info("AI分析器初始化成功, AI过滤: Twitter价值判断(过滤无信息价值推文)")
        else:
            self.report_generator = SocialMediaReportGenerator()
            logger.warning("AI分析器未配置,将使用基础功能(无AI过滤)")

    def collect_all_platforms(
        self,
        db: Session,
        youtube_enabled: bool = True,
        tiktok_enabled: bool = True,
        twitter_enabled: bool = True,
        reddit_enabled: bool = True,
        **kwargs
    ) -> Dict[str, List[Dict]]:
        """
        采集所有平台的热帖

        Args:
            db: 数据库会话
            youtube_enabled: 是否采集YouTube
            tiktok_enabled: 是否采集TikTok
            twitter_enabled: 是否采集Twitter
            reddit_enabled: 是否采集Reddit
            **kwargs: 其他采集参数

        Returns:
            各平台采集结果
        """
        results = {
            "youtube": [],
            "tiktok": [],
            "twitter": [],
            "reddit": []
        }

        # YouTube采集
        if youtube_enabled and self.youtube_collector:
            try:
                youtube_videos = self.youtube_collector.search_videos(**kwargs)
                results["youtube"] = youtube_videos
                logger.info(f"YouTube采集完成: {len(youtube_videos)}条")
            except Exception as e:
                logger.error(f"YouTube采集失败: {e}")

        # TikTok采集
        if tiktok_enabled and self.tiktok_collector:
            try:
                tiktok_videos = self.tiktok_collector.search_videos(**kwargs)
                results["tiktok"] = tiktok_videos
                logger.info(f"TikTok采集完成: {len(tiktok_videos)}条")
            except Exception as e:
                logger.error(f"TikTok采集失败: {e}")

        # Twitter采集
        if twitter_enabled and self.twitter_collector:
            try:
                twitter_tweets = self.twitter_collector.search_tweets(**kwargs)
                results["twitter"] = twitter_tweets
                logger.info(f"Twitter采集完成: {len(twitter_tweets)}条")
            except Exception as e:
                logger.error(f"Twitter采集失败: {e}")

        # Reddit采集
        if reddit_enabled and self.reddit_collector:
            try:
                # Reddit使用特定参数
                reddit_posts = self.reddit_collector.search_posts(
                    min_upvotes=kwargs.get("reddit_min_upvotes", 50),
                    max_results=kwargs.get("max_results", 50)
                )
                results["reddit"] = reddit_posts
                logger.info(f"Reddit采集完成: {len(reddit_posts)}条")
            except Exception as e:
                logger.error(f"Reddit采集失败: {e}")

        return results

    def save_posts(
        self,
        db: Session,
        posts_data: List[Dict]
    ) -> List[SocialMediaPost]:
        """
        保存采集的帖子到数据库

        Args:
            db: 数据库会话
            posts_data: 帖子数据列表

        Returns:
            保存的帖子对象列表
        """
        saved_posts = []

        for post_data in posts_data:
            try:
                # 检查是否已存在
                existing_post = db.query(SocialMediaPost).filter(
                    SocialMediaPost.platform == post_data["platform"],
                    SocialMediaPost.post_id == post_data["post_id"]
                ).first()

                if existing_post:
                    logger.debug(f"帖子已存在,跳过: {post_data['platform']} - {post_data['post_id']}")
                    continue

                # 创建新帖子
                post = SocialMediaPost(**post_data)
                db.add(post)
                saved_posts.append(post)

            except Exception as e:
                logger.error(f"保存帖子失败: {e}")
                continue

        try:
            db.commit()
            # 刷新以获取ID
            for post in saved_posts:
                db.refresh(post)

            logger.info(f"保存帖子成功: {len(saved_posts)}条")
            return saved_posts

        except Exception as e:
            logger.error(f"批量保存失败: {e}")
            db.rollback()
            return []

    def analyze_posts(
        self,
        db: Session,
        posts: List[SocialMediaPost]
    ) -> int:
        """
        使用AI分析帖子

        Args:
            db: 数据库会话
            posts: 帖子列表

        Returns:
            分析成功的数量
        """
        if not self.ai_analyzer:
            logger.warning("AI分析器未配置,跳过分析")
            return 0

        analyzed_count = 0

        for post in posts:
            if post.is_processed:
                continue

            try:
                # 构建分析内容
                content = post.title or ""
                if post.content:
                    content += "\n\n" + post.content

                # 使用AI分析(翻译标题+判断价值)
                prompt = f"""你是一名社交媒体内容编辑,任务是将帖子标题翻译成中文,并判断其AI信息价值。

输入信息:
标题: {post.title}
内容: {post.content[:500] if post.content else ''}
平台: {post.platform}
作者: {post.author_name}

请判断该帖子是否包含AI相关的有价值信息(产品、模型、研究、趋势、观点等)。

输出JSON格式:
{{
  "title_zh": "中文标题",
  "has_value": true/false,
  "value_reason": "理由"
}}"""

                # 这里需要根据实际的AI分析器接口调整
                # 假设有一个analyze_text方法
                # result = self.ai_analyzer.analyze_text(prompt)

                # 暂时跳过实际AI调用,只是标记
                post.is_processed = True
                analyzed_count += 1

            except Exception as e:
                logger.error(f"分析帖子失败: {e}")
                continue

        try:
            db.commit()
            logger.info(f"AI分析完成: {analyzed_count}条")
            return analyzed_count

        except Exception as e:
            logger.error(f"保存分析结果失败: {e}")
            db.rollback()
            return analyzed_count

    def generate_report(
        self,
        db: Session,
        report_date: Optional[datetime] = None,
        youtube_enabled: bool = True,
        tiktok_enabled: bool = True,
        twitter_enabled: bool = True,
        reddit_enabled: bool = True
    ) -> Optional[object]:
        """
        生成热帖报告

        Args:
            db: 数据库会话
            report_date: 报告日期
            youtube_enabled: 是否启用YouTube
            tiktok_enabled: 是否启用TikTok
            twitter_enabled: 是否启用Twitter
            reddit_enabled: 是否启用Reddit

        Returns:
            生成的报告对象
        """
        if not self.report_generator:
            logger.error("报告生成器未初始化")
            return None

        return self.report_generator.generate_daily_report(
            db=db,
            report_date=report_date,
            youtube_enabled=youtube_enabled,
            tiktok_enabled=tiktok_enabled,
            twitter_enabled=twitter_enabled,
            reddit_enabled=reddit_enabled
        )
