"""
清空 article_embeddings 表

重要说明：
1. 此操作会删除所有已索引的文章向量
2. 清空后需要重新索引所有文章
3. 建议在迁移 vec_embeddings 表后执行此操作
"""
import sqlite3
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def clear_article_embeddings(db_path: str, confirm: bool = False) -> bool:
    """
    清空 article_embeddings 表
    
    Args:
        db_path: SQLite 数据库文件路径
        confirm: 是否需要确认（如果为 False，会要求交互式确认）
    
    Returns:
        是否成功
    """
    try:
        # 检查数据库文件是否存在
        if not Path(db_path).exists():
            logger.error(f"❌ 数据库文件不存在: {db_path}")
            return False
        
        # 如果没有确认，要求用户确认
        if not confirm:
            print("⚠️  警告：此操作将删除所有已索引的文章向量！")
            print(f"   数据库路径: {db_path}")
            response = input("   确认清空 article_embeddings 表？(yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("❌ 操作已取消")
                return False
        
        # 连接数据库
        conn = sqlite3.connect(db_path)
        
        try:
            with conn:
                # 检查表是否存在
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='article_embeddings'
                """)
                table_exists = cursor.fetchone() is not None
                
                if not table_exists:
                    logger.warning("⚠️  article_embeddings 表不存在")
                    return False
                
                # 获取记录数
                count_cursor = conn.execute("SELECT COUNT(*) FROM article_embeddings")
                count = count_cursor.fetchone()[0]
                logger.info(f"📊 当前 article_embeddings 表中有 {count} 条记录")
                
                if count == 0:
                    logger.info("ℹ️  表已经是空的，无需清空")
                    return True
                
                # 清空表
                logger.info("🗑️  正在清空 article_embeddings 表...")
                conn.execute("DELETE FROM article_embeddings")
                
                # 验证
                verify_cursor = conn.execute("SELECT COUNT(*) FROM article_embeddings")
                verify_count = verify_cursor.fetchone()[0]
                
                if verify_count == 0:
                    logger.info("✅ article_embeddings 表已清空")
                    logger.info("")
                    logger.info("📝 下一步操作：")
                    logger.info("   1. 确保 vec_embeddings 表已使用余弦距离重建")
                    logger.info("   2. 通过 API 重新索引所有文章：")
                    logger.info("      POST /api/v1/rag/index/all?batch_size=10")
                    return True
                else:
                    logger.error(f"❌ 清空失败，表中仍有 {verify_count} 条记录")
                    return False
                
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ 清空失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="清空 article_embeddings 表")
    parser.add_argument(
        "--db-path",
        type=str,
        required=True,
        help="SQLite 数据库文件路径（例如: /path/to/database.db）"
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="跳过确认，直接执行"
    )
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    success = clear_article_embeddings(
        db_path=args.db_path,
        confirm=args.yes
    )
    
    sys.exit(0 if success else 1)
