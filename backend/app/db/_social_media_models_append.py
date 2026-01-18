"""
临时文件:包含需要追加到models.py的社交平台模型
"""
# 以下内容需要追加到 backend/app db\models.py 文件末尾

SOCIAL_MEDIA_MODELS_APPEND = """

class SocialMediaPost(Base):
    \"\"\"社交平台热帖表\"\"\"
    __tablename__ = "social_media_posts"

    # 复合索引 - 优化常用查询
    __table_args__ = (
        Index('idx_social_platform_date', 'platform', 'published_at'),
        Index('idx_social_collected_date', 'collected_at'),
        Index('idx_social_viral_score', 'platform', 'viral_score'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 基本信息
    platform = Column(String(50), nullable=False, index=True)  # youtube/tiktok/twitter
    post_id = Column(String(200), nullable=False, index=True)  # 平台上的唯一ID
    title = Column(String(1000), nullable=True)  # 标题/描述
    content = Column(Text, nullable=True)  # 内容/正文
    title_zh = Column(String(1000), nullable=True)  # 中文翻译

    # 作者信息
    author_id = Column(String(200), nullable=True)  # 作者ID
    author_name = Column(String(200), nullable=True)  # 作者名称
    author_url = Column(String(1000), nullable=True)  # 作者主页链接
    follower_count = Column(Integer, default=0)  # 作者粉丝数

    # 统计数据
    view_count = Column(Integer, default=0)  # 观看/浏览量
    like_count = Column(Integer, default=0)  # 点赞数
    comment_count = Column(Integer, default=0)  # 评论数
    share_count = Column(Integer, default=0)  # 分享/转发数
    favorite_count = Column(Integer, default=0)  # 收藏数

    # 爆款指标
    viral_score = Column(Float, nullable=True)  # 爆款指数
    viral_metrics = Column(JSON, nullable=True)  # 爆款指标详情

    # 链接信息
    post_url = Column(String(1000), nullable=False)  # 帖子链接
    thumbnail_url = Column(String(1000), nullable=True)  # 缩略图链接

    # 时间信息
    published_at = Column(DateTime, nullable=True, index=True)  # 发布时间
    collected_at = Column(DateTime, default=datetime.now, nullable=False)  # 采集时间

    # AI分析
    has_value = Column(Boolean, nullable=True)  # 是否有信息价值
    value_reason = Column(Text, nullable=True)  # 价值判断理由
    is_processed = Column(Boolean, default=False)  # 是否已AI处理

    # 扩展数据
    extra_data = Column(JSON, nullable=True)  # 额外信息

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<SocialMediaPost(id={self.id}, platform='{self.platform}', title='{self.title[:50] if self.title else ''}...')>"


class SocialMediaReport(Base):
    \"\"\"社交平台热帖日报表\"\"\"
    __tablename__ = "social_media_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_date = Column(DateTime, nullable=False, index=True)  # 报告日期

    # 统计信息
    youtube_count = Column(Integer, default=0)  # YouTube热帖数量
    tiktok_count = Column(Integer, default=0)  # TikTok热帖数量
    twitter_count = Column(Integer, default=0)  # Twitter热帖数量
    reddit_count = Column(Integer, default=0)  # Reddit热帖数量
    total_count = Column(Integer, default=0)  # 总数量

    # 报告内容
    report_content = Column(Text, nullable=False)  # Markdown格式的报告

    # 平台配置
    youtube_enabled = Column(Boolean, default=False)  # 是否启用YouTube采集
    tiktok_enabled = Column(Boolean, default=False)  # 是否启用TikTok采集
    twitter_enabled = Column(Boolean, default=False)  # 是否启用Twitter采集
    reddit_enabled = Column(Boolean, default=False)  # 是否启用Reddit采集

    # 元数据
    model_used = Column(String(100), nullable=True)  # 使用的LLM模型
    generation_time = Column(Float, nullable=True)  # 生成耗时(秒)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<SocialMediaReport(id={self.id}, date={self.report_date}, total={self.total_count})>"
"""
