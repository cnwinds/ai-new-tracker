"""
Reddit热帖采集服务
严格按照 n8n 工作流实现
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class RedditCollector:
    """Reddit热帖采集器 - 基于 n8n 工作流配置"""

    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        """
        初始化Reddit采集器

        Args:
            client_id: Reddit API客户端ID
            client_secret: Reddit API客户端密钥
            user_agent: 用户代理字符串
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        self.base_url = "https://www.reddit.com"
        self.oauth_url = "https://www.reddit.com/r/"
        self.access_token = None
        self.token_expires_at = None

        # 创建带重试机制的Session
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        # 设置User-Agent
        self.session.headers.update({"User-Agent": self.user_agent})

    def _ensure_access_token(self):
        """确保有有效的访问令牌"""
        # 检查token是否仍然有效
        if self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at:
                return

        # 获取新的访问令牌
        try:
            auth = requests.auth.HTTPBasicAuth(self.client_id, self.client_secret)
            data = {"grant_type": "client_credentials"}
            headers = {"User-Agent": self.user_agent}

            response = self.session.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=auth,
                data=data,
                headers=headers,
                timeout=(10, 30),
                verify=True
            )
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data.get("access_token")

            # 设置token过期时间（提前5分钟刷新）
            expires_in = token_data.get("expires_in", 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)

            logger.info("Reddit访问令牌获取成功")

        except Exception as e:
            logger.error(f"获取Reddit访问令牌失败: {e}")
            raise

    def search_posts(
        self,
        subreddits: List[str] = None,
        category: str = "hot",
        time_range: str = "day",
        min_upvotes: int = 50,
        max_results: int = 50
    ) -> List[Dict]:
        """
        搜索Reddit帖子 - 严格按照n8n工作流配置

        Args:
            subreddits: 子版块列表（默认为AI相关版块）
            category: 排序类型 (hot, new, top, rising)
            time_range: 时间范围 (hour, day, week, month, year, all)
            min_upvotes: 最小点赞数
            max_results: 最大结果数

        Returns:
            帖子列表
        """
        try:
            # 默认AI相关版块（n8n配置）
            if subreddits is None:
                subreddits = ["ArtificialInteligence", "artificial"]

            # 确保认证
            self._ensure_access_token()

            all_posts = []

            # 从每个版块获取帖子
            for subreddit in subreddits:
                try:
                    posts = self._fetch_subreddit_posts(
                        subreddit=subreddit,
                        category=category,
                        time_range=time_range,
                        max_results=max_results
                    )
                    all_posts.extend(posts)
                except Exception as e:
                    logger.warning(f"从版块 {subreddit} 获取帖子失败: {e}")
                    continue

            if not all_posts:
                logger.warning("未找到符合条件的帖子")
                return []

            # 过滤：24小时内且赞>50（严格按照n8n工作流）
            now = datetime.now().timestamp()
            total_collected = len(all_posts)
            filtered_posts = []

            for post in all_posts:
                created_utc = post.get("created_utc", 0)
                ups = post.get("ups", 0)

                # 过滤条件：24小时内且赞>50
                if created_utc > now - 86400 and ups > min_upvotes:
                    parsed_post = self._parse_post(post, subreddit)
                    if parsed_post:
                        filtered_posts.append(parsed_post)

            return filtered_posts

        except Exception as e:
            logger.error(f"Reddit采集失败: {e}", exc_info=True)
            return []

    def _fetch_subreddit_posts(
        self,
        subreddit: str,
        category: str,
        time_range: str,
        max_results: int
    ) -> List[Dict]:
        """
        从指定版块获取帖子

        Args:
            subreddit: 版块名称
            category: 排序类型
            time_range: 时间范围
            max_results: 最大结果数

        Returns:
            原始帖子数据列表
        """
        try:
            # 构建API URL
            url = f"{self.oauth_url}{subreddit}/{category}"

            # 设置请求头（带认证）
            headers = {
                "User-Agent": self.user_agent,
                "Authorization": f"bearer {self.access_token}"
            }

            # 请求参数
            params = {
                "limit": min(max_results * 2, 100),  # 多获取一些用于过滤
                "t": time_range if category in ["top", "controversial"] else None
            }

            response = self.session.get(
                url,
                headers=headers,
                params=params,
                timeout=(10, 30),
                verify=True,
                allow_redirects=True
            )
            response.raise_for_status()

            data = response.json()

            # 提取帖子列表
            posts = data.get("data", {}).get("children", [])
            return [post.get("data", {}) for post in posts]

        except Exception as e:
            logger.error(f"获取版块 {subreddit} 帖子失败: {e}")
            return []

    def _parse_post(self, post: Dict, subreddit: str) -> Optional[Dict]:
        """
        解析帖子数据 - 按照n8n工作流映射字段

        Args:
            post: Reddit API返回的帖子数据
            subreddit: 版块名称

        Returns:
            解析后的帖子数据
        """
        try:
            # 解析发布时间（UTC时间戳）
            created_utc = post.get("created_utc")
            published_at = None
            if created_utc:
                try:
                    published_at = datetime.fromtimestamp(created_utc)
                except:
                    pass

            # 构建标题和内容（n8n配置：标题 + selftext）
            title = post.get("title", "")
            selftext = post.get("selftext", "")
            content = f"{title}\n\n{selftext}" if selftext else title

            # 构建URL
            post_id = post.get("id", "")
            post_url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/"

            # 计算爆款分数（基于赞数和评论数）
            ups = post.get("ups", 0)
            num_comments = post.get("num_comments", 0)
            viral_score = self._calculate_viral_score(ups, num_comments, created_utc)

            # 构建帖子数据
            reddit_post = {
                "platform": "reddit",
                "post_id": post_id,
                "title": title,
                "content": selftext,
                "author_name": post.get("author", ""),
                "author_id": post.get("author_fullname", ""),
                "author_url": f"https://www.reddit.com/user/{post.get('author', '')}",
                "view_count": 0,  # Reddit API不提供观看数
                "like_count": ups,
                "comment_count": num_comments,
                "share_count": 0,  # Reddit API不提供分享数
                "post_url": post_url,
                "thumbnail_url": post.get("url_overridden_by_dest") if post.get("url_overridden_by_dest") else post.get("thumbnail", ""),
                "published_at": published_at,
                "collected_at": datetime.now(),
                "viral_score": viral_score,
                "viral_metrics": {
                    "ups": ups,
                    "num_comments": num_comments,
                    "upvote_ratio": post.get("upvote_ratio", 0),
                    "subreddit": subreddit,
                    "category": post.get("link_flair_text", "")
                },
                "extra_data": {
                    "subreddit": subreddit,
                    "selftext": selftext,
                    "permalink": post.get("permalink", ""),
                    "url": post.get("url", ""),
                    "is_self": post.get("is_self", False),
                    "over_18": post.get("over_18", False),
                    "spoiler": post.get("spoiler", False),
                    "locked": post.get("locked", False),
                    "stickied": post.get("stickied", False)
                }
            }

            return reddit_post

        except Exception as e:
            logger.warning(f"解析帖子数据失败: {e}")
            return None

    def _calculate_viral_score(
        self,
        ups: int,
        num_comments: int,
        created_utc: float
    ) -> float:
        """
        计算爆款分数

        Args:
            ups: 点赞数
            num_comments: 评论数
            created_utc: 创建时间(UTC时间戳)

        Returns:
            爆款分数(0-10)
        """
        try:
            # 基础分数（基于赞数）
            if ups <= 0:
                base_score = 0
            elif ups < 100:
                base_score = 3
            elif ups < 500:
                base_score = 5
            elif ups < 1000:
                base_score = 7
            elif ups < 5000:
                base_score = 8
            else:
                base_score = 9

            # 评论加分
            if num_comments > 100:
                base_score += 0.5
            elif num_comments > 500:
                base_score += 1.0

            # 时间衰减因子（新帖获得额外分数）
            if created_utc:
                post_age = datetime.now().timestamp() - created_utc
                age_hours = post_age / 3600

                if age_hours < 6:
                    base_score += 0.5
                elif age_hours < 24:
                    base_score += 0.3

            # 确保分数在0-10范围内
            return min(max(base_score, 0), 10)

        except Exception as e:
            logger.warning(f"计算爆款分数失败: {e}")
            return 0.0

    def search_by_query(
        self,
        query: str,
        subreddit: Optional[str] = None,
        category: str = "hot",
        time_range: str = "day",
        min_upvotes: int = 50,
        max_results: int = 50
    ) -> List[Dict]:
        """
        根据关键词搜索帖子

        Args:
            query: 搜索关键词
            subreddit: 限定版块（可选）
            category: 排序类型
            time_range: 时间范围
            min_upvotes: 最小点赞数
            max_results: 最大结果数

        Returns:
            帖子列表
        """
        try:
            # 确保认证
            self._ensure_access_token()

            # 构建搜索URL
            if subreddit:
                url = f"{self.oauth_url}{subreddit}/search"
            else:
                url = f"{self.base_url}/search"

            # 设置请求头（带认证）
            headers = {
                "User-Agent": self.user_agent,
                "Authorization": f"bearer {self.access_token}"
            }

            # 请求参数
            params = {
                "q": query,
                "restrict_sr": "on" if subreddit else "off",
                "sort": category,
                "t": time_range,
                "limit": max_results
            }

            response = self.session.get(
                url,
                headers=headers,
                params=params,
                timeout=(10, 30),
                verify=True,
                allow_redirects=True
            )
            response.raise_for_status()

            data = response.json()

            # 提取帖子列表
            posts = data.get("data", {}).get("children", [])
            raw_posts = [post.get("data", {}) for post in posts]

            # 过滤和解析
            now = datetime.now().timestamp()
            total_collected = len(raw_posts)
            filtered_posts = []

            for post in raw_posts:
                created_utc = post.get("created_utc", 0)
                ups = post.get("ups", 0)

                # 过滤条件：24小时内且赞>min_upvotes
                if created_utc > now - 86400 and ups > min_upvotes:
                    post_subreddit = post.get("subreddit", subreddit or "unknown")
                    parsed_post = self._parse_post(post, post_subreddit)
                    if parsed_post:
                        filtered_posts.append(parsed_post)

            logger.info(f"Reddit搜索统计: 采集到{total_collected}条记录(关键词: {query}), 过滤条件(24小时内 且 点赞数>={min_upvotes}), 通过过滤{len(filtered_posts)}条有效记录")
            return filtered_posts

        except Exception as e:
            logger.error(f"Reddit搜索失败: {e}", exc_info=True)
            return []
