"""
添加 Reddit 字段到社交平台报告表
"""
from sqlalchemy import text


def upgrade(db):
    """添加 reddit_count 和 reddit_enabled 字段到 social_media_reports 表"""
    
    # 检查字段是否已存在（SQLite 不支持直接检查，所以使用 try-except）
    try:
        # 添加 reddit_count 字段
        db.execute(text("""
            ALTER TABLE social_media_reports 
            ADD COLUMN reddit_count INTEGER DEFAULT 0
        """))
    except Exception:
        # 字段可能已存在，忽略错误
        pass
    
    try:
        # 添加 reddit_enabled 字段
        db.execute(text("""
            ALTER TABLE social_media_reports 
            ADD COLUMN reddit_enabled BOOLEAN DEFAULT 0
        """))
    except Exception:
        # 字段可能已存在，忽略错误
        pass
    
    # 更新现有记录的默认值
    db.execute(text("""
        UPDATE social_media_reports 
        SET reddit_count = 0 
        WHERE reddit_count IS NULL
    """))
    
    db.execute(text("""
        UPDATE social_media_reports 
        SET reddit_enabled = 0 
        WHERE reddit_enabled IS NULL
    """))
    
    db.commit()


def downgrade(db):
    """移除 reddit_count 和 reddit_enabled 字段"""
    # SQLite 不支持直接删除列，需要重建表
    # 这里只提供说明，实际降级需要更复杂的操作
    # 对于生产环境，建议备份数据后再操作
    pass
