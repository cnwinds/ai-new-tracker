"""
YouTube热帖采集服务
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class YouTubeCollector:
    """YouTube热帖采集器"""

    def __init__(self, api_key: str):
        """
        初始化YouTube采集器

        Args:
            api_key: YouTube Data API v3密钥
        """
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
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
        query: str = "AI",
        published_after: Optional[datetime] = None,
        min_view_count: int = 200000,
        max_results: int = 50
    ) -> List[Dict]:
        """
        搜索YouTube视频

        Args:
            query: 搜索关键词
            published_after: 发布时间筛选(之后)
            min_view_count: 最小观看量
            max_results: 最大结果数

        Returns:
            视频列表
        """
        try:
            # 计算时间范围
            if not published_after:
                published_after = datetime.now() - timedelta(days=1)

            # 搜索视频（严格按照n8n工作流配置）
            search_url = f"{self.base_url}/search"
            search_params = {
                "part": "snippet",
                "q": query,
                "order": "relevance",  # 按相关性排序
                "maxResults": max_results,
                "regionCode": "US",  # n8n配置中有此参数
                "type": "video",
                "publishedAfter": published_after.isoformat() + "Z",
                "key": self.api_key  # API key在query参数中（httpQueryAuth）
            }

            response = self.session.get(
                search_url, 
                params=search_params, 
                timeout=(10, 30),
                verify=True,
                allow_redirects=True
            )
            response.raise_for_status()
            search_data = response.json()

            # 提取视频ID和snippet信息（按照n8n工作流逻辑）
            search_items = search_data.get("items", [])
            if not search_items:
                logger.warning(f"未找到符合条件的视频: {query}")
                return []

            video_ids = []
            snippet_map = {}  # 存储videoId -> snippet的映射
            for item in search_items:
                video_id = item.get("id", {}).get("videoId")
                if video_id:
                    video_ids.append(video_id)
                    snippet_map[video_id] = item.get("snippet", {})

            if not video_ids:
                logger.warning(f"未找到有效的视频ID: {query}")
                return []

            # 获取视频统计信息（严格按照n8n工作流配置 - 只获取statistics）
            videos_url = f"{self.base_url}/videos"
            videos_params = {
                "part": "statistics",  # n8n配置中只使用statistics
                "id": ",".join(video_ids),
                "key": self.api_key  # API key在query参数中（httpQueryAuth）
            }

            response = self.session.get(
                videos_url, 
                params=videos_params, 
                timeout=(10, 30),
                verify=True,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # 尝试解析JSON，失败时输出完整响应内容
            try:
                videos_data = response.json()
            except Exception as json_error:
                logger.error(f"YouTube Videos API返回非JSON响应 - 状态码: {response.status_code}")
                logger.error(f"响应Headers: {dict(response.headers)}")
                logger.error(f"响应内容(前1000字符): {response.text[:1000]}")
                logger.error(f"完整响应内容: {response.text}")
                logger.error(f"JSON解析错误: {json_error}")
                raise

            # 合并snippet和statistics（按照n8n工作流的JavaScript逻辑）
            all_parsed_videos = []
            for item in videos_data.get("items", []):
                video_id = item.get("id")
                statistics = item.get("statistics", {})
                snippet = snippet_map.get(video_id, {})
                
                # 合并数据
                merged_item = {
                    "id": video_id,
                    "snippet": snippet,
                    "statistics": statistics
                }
                
                video = self._parse_video(merged_item)
                if video:
                    all_parsed_videos.append(video)
            
            # 过滤观看量
            filtered_videos = []
            for video in all_parsed_videos:
                if video.get("view_count", 0) >= min_view_count:
                    filtered_videos.append(video)

            return filtered_videos

        except Exception as e:
            logger.error(f"YouTube采集失败: {e}", exc_info=True)
            return []

    def _parse_video(self, item: Dict) -> Optional[Dict]:
        """
        解析视频数据

        Args:
            item: YouTube API返回的视频项

        Returns:
            解析后的视频数据
        """
        try:
            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})

            # 解析发布时间
            published_at = None
            if snippet.get("publishTime"):
                try:
                    published_at = datetime.fromisoformat(
                        snippet["publishTime"].replace("Z", "+00:00")
                    )
                except:
                    pass

            # 构建视频数据
            video = {
                "platform": "youtube",
                "post_id": item.get("id"),
                "title": snippet.get("title", ""),
                "content": snippet.get("description", ""),
                "author_name": snippet.get("channelTitle", ""),
                "author_id": snippet.get("channelId", ""),
                "author_url": f"https://www.youtube.com/channel/{snippet.get('channelId', '')}",
                "view_count": int(statistics.get("viewCount", 0)),
                "like_count": int(statistics.get("likeCount", 0)),
                "comment_count": int(statistics.get("commentCount", 0)),
                "favorite_count": int(statistics.get("favoriteCount", 0)),
                "post_url": f"https://www.youtube.com/watch?v={item.get('id')}",
                "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                "published_at": published_at,
                "collected_at": datetime.now(),
                "extra_data": {
                    "category_id": snippet.get("categoryId"),
                    "live_broadcast_content": snippet.get("liveBroadcastContent"),
                    "tags": snippet.get("tags", [])
                }
            }

            return video

        except Exception as e:
            logger.warning(f"解析视频数据失败: {e}")
            return None

    def get_channel_videos(
        self,
        channel_id: str,
        published_after: Optional[datetime] = None,
        min_view_count: int = 200000,
        max_results: int = 50
    ) -> List[Dict]:
        """
        获取指定频道的视频

        Args:
            channel_id: 频道ID
            published_after: 发布时间筛选
            min_view_count: 最小观看量
            max_results: 最大结果数

        Returns:
            视频列表
        """
        try:
            # 计算时间范围
            if not published_after:
                published_after = datetime.now() - timedelta(days=1)

            # 搜索频道视频
            search_url = f"{self.base_url}/search"
            search_params = {
                "part": "snippet",
                "channelId": channel_id,
                "type": "video",
                "order": "date",
                "publishedAfter": published_after.isoformat() + "Z",
                "maxResults": max_results,
                "key": self.api_key
            }

            response = self.session.get(
                search_url, 
                params=search_params, 
                timeout=(10, 30),
                verify=True,
                allow_redirects=True
            )
            response.raise_for_status()
            search_data = response.json()

            # 提取视频ID并获取统计信息
            video_ids = [
                item.get("id", {}).get("videoId")
                for item in search_data.get("items", [])
                if item.get("id", {}).get("videoId")
            ]

            if not video_ids:
                return []

            # 获取视频详情(包括统计信息)
            videos_url = f"{self.base_url}/videos"
            videos_params = {
                "part": "statistics,snippet",
                "id": ",".join(video_ids),
                "key": self.api_key
            }

            response = self.session.get(
                videos_url, 
                params=videos_params, 
                timeout=(10, 30),
                verify=True,
                allow_redirects=True
            )
            response.raise_for_status()
            videos_data = response.json()

            # 处理并过滤视频
            videos = []
            for item in videos_data.get("items", []):
                video = self._parse_video(item)
                if video and video.get("view_count", 0) >= min_view_count:
                    videos.append(video)

            return videos

        except Exception as e:
            logger.error(f"获取频道视频失败: {e}")
            return []
