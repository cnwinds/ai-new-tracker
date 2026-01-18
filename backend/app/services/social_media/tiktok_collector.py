"""
TikTok热帖采集服务
"""
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class TikTokCollector:
    """TikTok热帖采集器"""

    def __init__(self, api_key: str):
        """
        初始化TikTok采集器

        Args:
            api_key: RapidAPI密钥
        """
        self.api_key = api_key
        self.base_url = "https://tiktok-api23.p.rapidapi.com"
        
        # 创建带重试机制的Session
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def search_videos(
        self,
        keyword: str = "AI",
        min_viral_score: float = 8.0,
        max_days: int = 7,
        max_results: int = 100
    ) -> List[Dict]:
        """
        搜索TikTok视频

        Args:
            keyword: 搜索关键词
            min_viral_score: 最小爆款指数
            max_days: 最大天数(发布时间筛选,默认7天)
            max_results: 最大结果数

        Returns:
            视频列表
        """
        try:
            videos = []
            cursor = 0
            search_id = 0

            while len(videos) < max_results:
                # 构建请求参数（严格按照n8n工作流配置）
                params = {
                    "keyword": keyword,
                    "cursor": str(cursor) if cursor != 0 else "0",  # n8n中初始值为"=0"
                    "search_id": str(search_id) if search_id != 0 else "0"  # n8n中初始值为"=0"
                }

                # 请求头（严格按照n8n工作流配置）
                headers = {
                    "x-rapidapi-host": "tiktok-api23.p.rapidapi.com",  # n8n配置中的header
                    "x-rapidapi-key": self.api_key  # API key在header中（httpHeaderAuth）
                }
                
                response = self.session.get(
                    f"{self.base_url}/api/search/general",
                    params=params,
                    headers=headers,
                    timeout=(10, 30),  # (连接超时, 读取超时)
                    verify=True,  # SSL验证
                    allow_redirects=True
                )
                response.raise_for_status()
                
                # 尝试解析JSON，失败时输出完整响应内容
                try:
                    data = response.json()
                except Exception as json_error:
                    logger.error(f"TikTok API返回非JSON响应 - 状态码: {response.status_code}")
                    logger.error(f"响应Headers: {dict(response.headers)}")
                    logger.error(f"响应内容(前1000字符): {response.text[:1000]}")
                    logger.error(f"完整响应内容: {response.text}")
                    logger.error(f"JSON解析错误: {json_error}")
                    raise

                # 解析视频（按照n8n工作流逻辑）
                batch_videos = self._parse_batch(data, max_days)
                videos.extend(batch_videos)

                # 更新cursor和search_id（按照n8n工作流 - 从根级别获取）
                # n8n中: const cursor = fullResponse.cursor || null;
                # n8n中: const searchId = fullResponse.search_id || (fullResponse.log_pb ? fullResponse.log_pb.impr_id : null) || null;
                new_cursor = data.get("cursor")
                if new_cursor is not None:
                    try:
                        cursor = int(new_cursor) if isinstance(new_cursor, (int, str)) and str(new_cursor).isdigit() else new_cursor
                    except:
                        cursor = new_cursor
                
                new_search_id = data.get("search_id")
                if new_search_id is None and data.get("log_pb"):
                    new_search_id = data.get("log_pb", {}).get("impr_id")
                if new_search_id is not None:
                    try:
                        search_id = int(new_search_id) if isinstance(new_search_id, (int, str)) and str(new_search_id).isdigit() else new_search_id
                    except:
                        search_id = new_search_id

                # 检查是否还有更多结果
                if not data.get("has_more", False):
                    break

                # 避免请求过多
                if len(videos) >= max_results:
                    break

            # 计算爆款分数并过滤
            total_collected = len(videos)
            filtered_videos = []
            for video in videos:
                viral_score = self._calculate_viral_score(video)
                video["viral_score"] = viral_score
                video["viral_metrics"] = self._get_viral_metrics(video)

                if viral_score >= min_viral_score:
                    filtered_videos.append(video)

            return filtered_videos[:max_results]

        except Exception as e:
            logger.error(f"TikTok采集失败: {e}", exc_info=True)
            return []

    def _parse_batch(self, data: Dict, max_days: int = 7) -> List[Dict]:
        """
        批量解析视频数据

        Args:
            data: API返回数据
            max_days: 最大天数(默认7天)

        Returns:
            视频列表
        """
        videos = []
        videos_data = data.get("data", [])

        # 计算时间阈值
        time_threshold = datetime.now() - timedelta(days=max_days)

        for video_data in videos_data:
            video = self._parse_video(video_data)
            if video:
                # 过滤发布时间
                if video.get("published_at") and video["published_at"] >= time_threshold:
                    videos.append(video)

        return videos

    def _parse_video(self, video_data: Dict) -> Optional[Dict]:
        """
        解析单个视频数据

        Args:
            video_data: TikTok API返回的视频数据

        Returns:
            解析后的视频数据
        """
        try:
            item = video_data.get("item", {})
            author = item.get("author", {})
            author_stats = item.get("authorStats", {})
            stats = item.get("stats", {})
            video_info = item.get("video", {})

            # 基本信息
            video_id = item.get("id")
            description = item.get("desc", "")

            # 作者信息
            author_id = author.get("id")
            author_name = author.get("uniqueId")
            follower_count = author_stats.get("followerCount", 0)

            # 统计信息
            play_count = stats.get("playCount", 0)
            digg_count = stats.get("diggCount", 0)
            comment_count = stats.get("commentCount", 0)
            share_count = stats.get("shareCount", 0)
            collect_count = stats.get("collectCount", 0)

            # 解析发布时间
            published_at = None
            create_time = item.get("createTime")
            if create_time:
                try:
                    published_at = datetime.fromtimestamp(create_time)
                except:
                    pass

            # 构建视频数据
            video = {
                "platform": "tiktok",
                "post_id": video_id,
                "title": description[:200] if len(description) > 200 else description,
                "content": description,
                "author_name": author_name,
                "author_id": author_id,
                "author_url": f"https://www.tiktok.com/@{author_name}" if author_name else None,
                "follower_count": follower_count,
                "view_count": play_count,
                "like_count": digg_count,
                "comment_count": comment_count,
                "share_count": share_count,
                "favorite_count": collect_count,
                "post_url": f"https://www.tiktok.com/@{author_name}/video/{video_id}" if author_name and video_id else None,
                "thumbnail_url": video_info.get("cover"),
                "published_at": published_at,
                "collected_at": datetime.now(),
                "extra_data": {
                    "duration": video_info.get("duration"),
                    "music": item.get("music", {}),
                    "hashtags": item.get("hashtags", [])
                }
            }

            return video

        except Exception as e:
            logger.warning(f"解析TikTok视频数据失败: {e}")
            return None

    def _calculate_viral_score(self, video: Dict) -> float:
        """
        计算爆款指数
        综合考虑播放/粉丝比、点赞率、评论率、分享率

        Args:
            video: 视频数据

        Returns:
            爆款指数
        """
        # 基础门槛检查
        min_play_count = 100000  # 最小播放量
        min_follower_count = 100  # 最小粉丝数

        play_count = video.get("view_count", 0)
        follower_count = video.get("follower_count", 0)

        if play_count < min_play_count or follower_count < min_follower_count:
            return 0.0

        if play_count == 0 or follower_count == 0:
            return 0.0

        # 计算各项比率
        play_to_follower_ratio = play_count / follower_count  # 播放/粉丝比
        like_to_play_ratio = video.get("like_count", 0) / play_count  # 点赞率
        comment_to_play_ratio = video.get("comment_count", 0) / play_count  # 评论率
        share_to_play_ratio = video.get("share_count", 0) / play_count  # 分享率

        # 权重配置
        weights = {
            "play_to_follower": 3.0,
            "like_to_play": 1.0,
            "comment_to_play": 5.0,
            "share_to_play": 10.0
        }

        # 计算总爆款指数
        viral_score = (
            play_to_follower_ratio * weights["play_to_follower"] +
            like_to_play_ratio * weights["like_to_play"] +
            comment_to_play_ratio * weights["comment_to_play"] +
            share_to_play_ratio * weights["share_to_play"]
        )

        return round(viral_score, 2)

    def _get_viral_metrics(self, video: Dict) -> Dict:
        """
        获取爆款指标详情

        Args:
            video: 视频数据

        Returns:
            爆款指标详情
        """
        play_count = video.get("view_count", 0)
        follower_count = video.get("follower_count", 0)

        if play_count == 0 or follower_count == 0:
            return {}

        return {
            "play_to_follower_ratio": round(play_count / follower_count, 2),
            "like_to_play_ratio": round(video.get("like_count", 0) / play_count, 4),
            "comment_to_play_ratio": round(video.get("comment_count", 0) / play_count, 4),
            "share_to_play_ratio": round(video.get("share_count", 0) / play_count, 4)
        }
