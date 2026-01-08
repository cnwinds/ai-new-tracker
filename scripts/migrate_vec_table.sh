#!/bin/bash
# 迁移 vec_embeddings 表到余弦距离的便捷脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}迁移 vec_embeddings 表到余弦距离${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查是否在 Docker 环境中
if [ -f "docker/docker-compose.yml" ]; then
    echo -e "${YELLOW}检测到 Docker 环境${NC}"
    CONTAINER_NAME="ai-news-tracker-backend"
    DB_PATH="/app/backend/app/data/ai_news.db"
    
    # 检查容器是否运行
    if ! docker ps | grep -q "$CONTAINER_NAME"; then
        echo -e "${RED}错误: 容器 $CONTAINER_NAME 未运行${NC}"
        echo "请先启动容器: docker-compose up -d"
        exit 1
    fi
    
    echo -e "${GREEN}在容器内执行迁移...${NC}"
    docker exec -it "$CONTAINER_NAME" python -m backend.app.db.migrate_vec_table \
        --db-path "$DB_PATH" \
        --embedding-model text-embedding-3-small
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ 迁移成功！${NC}"
        echo ""
        echo -e "${YELLOW}下一步操作：${NC}"
        echo "1. 重启应用: docker-compose restart backend"
        echo "2. 重新索引文章（通过 API 或前端界面）"
    else
        echo -e "${RED}❌ 迁移失败${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}检测到本地环境${NC}"
    DB_PATH="./docker/data/ai_news.db"
    
    if [ ! -f "$DB_PATH" ]; then
        echo -e "${RED}错误: 数据库文件不存在: $DB_PATH${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}在本地执行迁移...${NC}"
    python -m backend.app.db.migrate_vec_table \
        --db-path "$DB_PATH" \
        --embedding-model text-embedding-3-small
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ 迁移成功！${NC}"
        echo ""
        echo -e "${YELLOW}下一步操作：${NC}"
        echo "1. 重启应用"
        echo "2. 重新索引文章（通过 API 或前端界面）"
    else
        echo -e "${RED}❌ 迁移失败${NC}"
        exit 1
    fi
fi
