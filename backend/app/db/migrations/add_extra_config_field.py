"""
数据库迁移脚本：为rss_sources表添加extra_config字段
"""
import sqlite3
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def migrate():
    """执行迁移"""
    db_path = Path(__file__).parent.parent.parent / "data" / "ai_news.db"
    
    if not db_path.exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(rss_sources)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "extra_config" in columns:
            print("✅ extra_config 字段已存在，无需迁移")
            conn.close()
            return True
        
        print("🔄 开始迁移: 添加 extra_config 字段到 rss_sources 表...")
        
        cursor.execute("""
            ALTER TABLE rss_sources 
            ADD COLUMN extra_config TEXT
        """)
        
        conn.commit()
        print("✅ 迁移成功: extra_config 字段已添加")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 迁移失败: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 50)
    print("数据库迁移: 添加 extra_config 字段")
    print("=" * 50)
    
    success = migrate()
    
    if success:
        print("\n✅ 迁移完成")
    else:
        print("\n❌ 迁移失败")
