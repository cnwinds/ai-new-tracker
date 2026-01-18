"""
Twitter热帖采集服务
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class TwitterCollector:
    """Twitter热帖采集器"""

    def __init__(self, api_key: str):
        """
        初始化Twitter采集器

        Args:
            api_key: Twitter API密钥(使用twitterapi.io)
        """
        self.api_key = api_key
        self.base_url = "https://api.twitterapi.io/twitter/tweet"
        
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

    def search_tweets(
        self,
        query: str = "AI",
        query_type: str = "Top",
        min_view_count: int = 10000,
        min_engagement_score: int = 1000,
        max_results: int = 100
    ) -> List[Dict]:
        """
        搜索Twitter推文

        Args:
            query: 搜索关键词
            query_type: 查询类型(Top/Latest)
            min_view_count: 最小观看量
            min_engagement_score: 最小互动分数
            max_results: 最大结果数

        Returns:
            推文列表
        """
        try:
            tweets = []
            cursor = ""

            while len(tweets) < max_results:
                # 构建请求参数（严格按照n8n工作流配置）
                params = {
                    "query": query,
                    "queryType": query_type,  # n8n中为"Top"
                    "cursor": cursor if cursor else ""  # n8n中初始值为"="
                }

                # 请求头（严格按照n8n工作流配置 - httpHeaderAuth）
                headers = {
                    "X-API-Key": self.api_key  # API key在header中（httpHeaderAuth）
                }

                response = self.session.get(
                    f"{self.base_url}/advanced_search",
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
                    logger.error(f"Twitter API返回非JSON响应 - 状态码: {response.status_code}")
                    logger.error(f"响应Headers: {dict(response.headers)}")
                    logger.error(f"响应内容(前1000字符): {response.text[:1000]}")
                    logger.error(f"完整响应内容: {response.text}")
                    logger.error(f"JSON解析错误: {json_error}")
                    raise

                # 解析推文
                batch_tweets = self._parse_batch(data)
                tweets.extend(batch_tweets)

                # 检查是否还有更多结果
                if not data.get("hasMore") or not data.get("cursor"):
                    break

                cursor = data.get("cursor", "")

                # 避免请求过多
                if len(tweets) >= max_results:
                    break

            # 过滤推文
            total_collected = len(tweets)
            filtered_tweets = []
            for tweet in tweets:
                engagement_score = self._calculate_engagement_score(tweet)
                view_count = tweet.get("view_count", 0)
                if engagement_score >= min_engagement_score and view_count >= min_view_count:
                    filtered_tweets.append(tweet)

            return filtered_tweets[:max_results]

        except Exception as e:
            logger.error(f"Twitter采集失败: {e}", exc_info=True)
            return []

    def _parse_batch(self, data: Dict) -> List[Dict]:
        """
        批量解析推文数据

        Args:
            data: API返回数据

        Returns:
            推文列表
        """
        tweets = []
        tweets_data = data.get("tweets", [])

        for tweet_data in tweets_data:
            tweet = self._parse_tweet(tweet_data)
            if tweet:
                tweets.append(tweet)

        return tweets

    def _parse_tweet(self, tweet_data: Dict) -> Optional[Dict]:
        """
        解析单条推文数据

        Args:
            tweet_data: Twitter API返回的推文数据

        Returns:
            解析后的推文数据
        """
        try:
            # 基本信息提取
            tweet_id = tweet_data.get("id") or tweet_data.get("tweetId")
            text = tweet_data.get("text") or tweet_data.get("content", "")

            # 作者信息
            author_info = tweet_data.get("author", {})
            author_name = author_info.get("userName") or author_info.get("username") or author_info.get("name", "")
            author_id = author_info.get("id") or author_info.get("userId", "")

            # 统计信息 - API直接返回在顶层,使用驼峰命名
            like_count = tweet_data.get("likeCount", 0)
            retweet_count = tweet_data.get("retweetCount", 0)
            reply_count = tweet_data.get("replyCount", 0)
            quote_count = tweet_data.get("quoteCount", 0)
            view_count = tweet_data.get("viewCount", 0)
            bookmark_count = tweet_data.get("bookmarkCount", 0)

            # 解析发布时间
            published_at = None
            created_at = tweet_data.get("createdAt") or tweet_data.get("created_at")
            if created_at:
                try:
                    # Twitter格式: "Sat Jan 17 08:00:01 +0000 2026"
                    # 需要处理时区
                    created_at = created_at.replace("+0000", "").replace("UTC", "").strip()
                    # 尝试多种格式
                    for fmt in [
                        "%a %b %d %H:%M:%S %Y",
                        "%a %b %d %H:%M:%S %Z %Y",
                        "%a %b %d %H:%M:%S +0000 %Y"
                    ]:
                        try:
                            published_at = datetime.strptime(created_at, fmt)
                            break
                        except:
                            continue
                except Exception as e:
                    logger.debug(f"解析时间失败: {created_at}, {e}")

            # 计算互动分数
            engagement_score = self._calculate_engagement_score({
                "like_count": like_count,
                "retweet_count": retweet_count,
                "reply_count": reply_count,
                "quote_count": quote_count
            })

            # 构建推文数据
            tweet = {
                "platform": "twitter",
                "post_id": tweet_id,
                "title": text[:200] if len(text) > 200 else text,  # 标题用前200字符
                "content": text,
                "author_name": author_name,
                "author_id": author_id,
                "author_url": f"https://twitter.com/{author_name}" if author_name else None,
                "view_count": view_count,
                "like_count": like_count,
                "comment_count": reply_count,
                "share_count": retweet_count,
                "favorite_count": quote_count,  # 引用推文数
                "viral_score": engagement_score,  # 使用互动分数作为爆款分数
                "post_url": tweet_data.get("twitterUrl") or tweet_data.get("url") or f"https://twitter.com/i/status/{tweet_id}",
                "published_at": published_at,
                "collected_at": datetime.now(),
                "extra_data": {
                    "quote_count": quote_count,
                    "bookmark_count": bookmark_count
                }
            }

            return tweet

        except Exception as e:
            logger.warning(f"解析推文数据失败: {e}")
            return None

    def _calculate_engagement_score(self, tweet: Dict) -> float:
        """
        计算互动分数
        公式: 点赞 + 转发*2 + 回复*1.5 + 引用*2

        Args:
            tweet: 推文数据

        Returns:
            互动分数
        """
        like_count = tweet.get("like_count", 0)
        retweet_count = tweet.get("retweet_count", 0)
        reply_count = tweet.get("reply_count", 0)
        quote_count = tweet.get("quote_count", 0)

        score = like_count + (retweet_count * 2) + (reply_count * 1.5) + (quote_count * 2)
        return score
