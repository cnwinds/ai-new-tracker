"""
迁移 vec_embeddings 表：从 L2 距离改为余弦距离

重要说明：
1. vec_embeddings 是虚拟表（virtual table），数据实际存储在 article_embeddings 表中
2. 删除 vec_embeddings 表不会丢失数据，因为真正的向量数据在 article_embeddings 中
3. 删除表后，需要重新同步数据到新的 vec_embeddings 表
"""
import sqlite3
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def get_embedding_dimension(embedding_model: str) -> int:
    """根据嵌入模型名称获取向量维度"""
    model_dimensions = {
        "text-embedding-3-small": 1024,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
        "text-embedding-v4": 1024,
        "text-embedding-v3": 1536,
        "text-embedding-v2": 1536,
        "text-embedding-v1": 1536,
    }
    
    if embedding_model in model_dimensions:
        return model_dimensions[embedding_model]
    
    for model_name, dimension in model_dimensions.items():
        if model_name in embedding_model:
            return dimension
    
    logger.warning(f"⚠️  未知的嵌入模型 '{embedding_model}'，使用默认维度 1536")
    return 1536


def migrate_vec_table(
    db_path: str,
    embedding_model: str = "text-embedding-3-small",
    force: bool = False
) -> bool:
    """
    迁移 vec_embeddings 表：删除旧表并重建为使用余弦距离
    
    Args:
        db_path: SQLite 数据库文件路径
        embedding_model: 嵌入模型名称，用于确定向量维度
        force: 是否强制重建（即使表不存在也会创建）
    
    Returns:
        是否成功
    """
    try:
        # 检查数据库文件是否存在
        if not Path(db_path).exists():
            logger.error(f"❌ 数据库文件不存在: {db_path}")
            return False
        
        # 尝试导入 sqlite_vec 模块
        try:
            import sqlite_vec
        except ImportError:
            logger.error("❌ sqlite-vec 模块未安装，无法迁移")
            logger.error("   请安装: pip install sqlite-vec")
            return False
        
        # 获取向量维度
        dimension = get_embedding_dimension(embedding_model)
        logger.info(f"📊 使用嵌入模型: {embedding_model}，维度: {dimension}")
        
        # 连接数据库
        conn = sqlite3.connect(db_path)
        conn.enable_load_extension(True)
        
        try:
            # 加载 sqlite-vec 扩展
            sqlite_vec.load(conn)
            
            with conn:
                # 检查表是否存在
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='vec_embeddings'
                """)
                table_exists = cursor.fetchone() is not None
                
                if not table_exists and not force:
                    logger.warning("⚠️  vec_embeddings 表不存在，跳过迁移")
                    logger.info("   如果需要创建新表，请使用 force=True")
                    return False
                
                if table_exists:
                    logger.info("🔄 检测到旧的 vec_embeddings 表，准备删除...")
                    # 检查表中是否有数据
                    count_cursor = conn.execute("SELECT COUNT(*) FROM vec_embeddings")
                    count = count_cursor.fetchone()[0]
                    logger.info(f"   当前表中有 {count} 条记录（这些数据会从 article_embeddings 重新同步）")
                    
                    # 删除旧表
                    conn.execute("DROP TABLE IF EXISTS vec_embeddings")
                    logger.info("✅ 旧表已删除")
                
                # 创建新表，使用余弦距离
                logger.info("🔨 正在创建新的 vec_embeddings 表（使用余弦距离）...")
                conn.execute(f"""
                    CREATE VIRTUAL TABLE vec_embeddings USING vec0(
                        article_id INTEGER PRIMARY KEY,
                        embedding float[{dimension}] DISTANCE_METRIC=cosine
                    )
                """)
                logger.info(f"✅ 新表创建成功（维度: {dimension}，使用余弦距离）")
                logger.info("")
                logger.info("📝 下一步操作：")
                logger.info("   1. 重启应用，系统会自动同步数据到新表")
                logger.info("   2. 或者通过 API 重新索引所有文章：")
                logger.info("      POST /api/v1/rag/index/all?batch_size=10")
                logger.info("")
                
                return True
                
        except sqlite3.OperationalError as e:
            if "no such module: vec0" in str(e):
                logger.error("❌ sqlite-vec 扩展加载失败")
                logger.error("   请确保已正确安装 sqlite-vec")
                return False
            else:
                raise
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="迁移 vec_embeddings 表到余弦距离")
    parser.add_argument(
        "--db-path",
        type=str,
        required=True,
        help="SQLite 数据库文件路径（例如: /path/to/database.db）"
    )
    parser.add_argument(
        "--embedding-model",
        type=str,
        default="text-embedding-3-small",
        help="嵌入模型名称（默认: text-embedding-3-small）"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重建表（即使表不存在也会创建）"
    )
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    success = migrate_vec_table(
        db_path=args.db_path,
        embedding_model=args.embedding_model,
        force=args.force
    )
    
    sys.exit(0 if success else 1)
