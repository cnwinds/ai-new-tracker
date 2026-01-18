"""
添加社交平台热帖表
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


def upgrade(db):
    """添加社交平台相关表"""

    # 创建社交平台热帖表
    db.execute("""
    CREATE TABLE IF NOT EXISTS social_media_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform VARCHAR(50) NOT NULL,
        post_id VARCHAR(200) NOT NULL,
        title VARCHAR(1000),
        content TEXT,
        title_zh VARCHAR(1000),
        author_id VARCHAR(200),
        author_name VARCHAR(200),
        author_url VARCHAR(1000),
        follower_count INTEGER DEFAULT 0,
        view_count INTEGER DEFAULT 0,
        like_count INTEGER DEFAULT 0,
        comment_count INTEGER DEFAULT 0,
        share_count INTEGER DEFAULT 0,
        favorite_count INTEGER DEFAULT 0,
        viral_score FLOAT,
        viral_metrics JSON,
        post_url VARCHAR(1000) NOT NULL,
        thumbnail_url VARCHAR(1000),
        published_at DATETIME,
        collected_at DATETIME NOT NULL,
        has_value BOOLEAN,
        value_reason TEXT,
        is_processed BOOLEAN DEFAULT 0,
        extra_data JSON,
        created_at DATETIME,
        updated_at DATETIME
    )
    """)

    # 创建索引
    db.execute("CREATE INDEX IF NOT EXISTS idx_social_platform_date ON social_media_posts(platform, published_at)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_social_collected_date ON social_media_posts(collected_at)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_social_viral_score ON social_media_posts(platform, viral_score)")

    # 创建社交平台报告表
    db.execute("""
    CREATE TABLE IF NOT EXISTS social_media_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_date DATETIME NOT NULL,
        youtube_count INTEGER DEFAULT 0,
        tiktok_count INTEGER DEFAULT 0,
        twitter_count INTEGER DEFAULT 0,
        reddit_count INTEGER DEFAULT 0,
        total_count INTEGER DEFAULT 0,
        report_content TEXT NOT NULL,
        youtube_enabled BOOLEAN DEFAULT 0,
        tiktok_enabled BOOLEAN DEFAULT 0,
        twitter_enabled BOOLEAN DEFAULT 0,
        reddit_enabled BOOLEAN DEFAULT 0,
        model_used VARCHAR(100),
        generation_time FLOAT,
        created_at DATETIME,
        updated_at DATETIME
    )
    """)

    db.execute("CREATE INDEX IF NOT EXISTS idx_social_report_date ON social_media_reports(report_date)")

    db.commit()


def downgrade(db):
    """删除社交平台相关表"""
    db.execute("DROP TABLE IF EXISTS social_media_reports")
    db.execute("DROP TABLE IF EXISTS social_media_posts")
    db.commit()
