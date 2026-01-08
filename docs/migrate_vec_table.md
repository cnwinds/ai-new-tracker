# 迁移 vec_embeddings 表到余弦距离

## 概述

由于我们将 `vec_embeddings` 表从默认的 L2 距离改为余弦距离（`DISTANCE_METRIC=cosine`），需要迁移线上数据库。

**重要说明**：
- `vec_embeddings` 是虚拟表（virtual table），真正的向量数据存储在 `article_embeddings` 表中
- 删除 `vec_embeddings` 表**不会丢失数据**，因为数据在 `article_embeddings` 中
- 删除表后，需要重新同步数据到新的 `vec_embeddings` 表

## 方法一：使用迁移脚本（推荐）

### 1. 找到数据库文件路径

根据 `docker-compose.yml` 配置，数据库文件路径为：
- **容器内路径**：`/app/backend/app/data/ai_news.db`
- **宿主机路径**：`./docker/data/ai_news.db`（相对于项目根目录）

### 2. 运行迁移脚本

```bash
# 方式1：在容器内运行（推荐）
docker exec -it ai-news-tracker-backend python -m backend.app.db.migrate_vec_table \
  --db-path /app/backend/app/data/ai_news.db \
  --embedding-model text-embedding-3-small

# 方式2：如果数据库文件在宿主机
cd /path/to/ai-news-tracker
python -m backend.app.db.migrate_vec_table \
  --db-path ./docker/data/ai_news.db \
  --embedding-model text-embedding-3-small
```

### 3. 重启应用

```bash
# Docker 方式
docker-compose restart backend

# 或直接重启容器
docker restart <container_name>
```

### 4. 重新同步数据

重启后，系统会自动开始同步数据。或者手动触发：

```bash
# 通过 API 重新索引所有文章
curl -X POST http://localhost:8000/api/v1/rag/index/all?batch_size=10 \
  -H "Authorization: Bearer <your_token>"
```

## 方法二：手动 SQL 操作

### 1. 连接到数据库

```bash
# Docker 方式（本项目）
docker exec -it ai-news-tracker-backend sqlite3 /app/backend/app/data/ai_news.db

# 或直接连接（如果数据库文件在宿主机）
sqlite3 ./docker/data/ai_news.db
```

### 2. 检查当前表

```sql
-- 检查表是否存在
SELECT name FROM sqlite_master 
WHERE type='table' AND name='vec_embeddings';

-- 查看表中的记录数
SELECT COUNT(*) FROM vec_embeddings;
```

### 3. 删除旧表

```sql
-- 删除旧表（不会丢失数据，因为数据在 article_embeddings 中）
DROP TABLE IF EXISTS vec_embeddings;
```

### 4. 加载 sqlite-vec 扩展并创建新表

```sql
-- 加载扩展（如果使用 sqlite3 命令行工具）
.load sqlite_vec

-- 创建新表（使用余弦距离）
-- 注意：根据您的嵌入模型调整维度
-- text-embedding-3-small: 1024
-- text-embedding-3-large: 3072
-- text-embedding-ada-002: 1536

CREATE VIRTUAL TABLE vec_embeddings USING vec0(
    article_id INTEGER PRIMARY KEY,
    embedding float[1024] DISTANCE_METRIC=cosine
);
```

### 5. 验证新表

```sql
-- 检查表是否创建成功
SELECT name FROM sqlite_master 
WHERE type='table' AND name='vec_embeddings';

-- 退出
.quit
```

### 6. 重启应用并重新同步数据

同方法一的步骤 3 和 4。

## 方法三：通过应用自动重建（最简单）

如果您的应用代码已经更新，可以：

1. **重启应用**：应用启动时会检测表结构
2. **如果检测到维度不匹配**：应用会自动删除并重建表
3. **重新索引**：通过 API 重新索引所有文章

```bash
# 重启应用
docker-compose restart backend

# 等待应用启动后，重新索引
curl -X POST http://localhost:8000/api/v1/rag/index/all?batch_size=10 \
  -H "Authorization: Bearer <your_token>"
```

## 验证迁移

迁移完成后，可以通过以下方式验证：

### 1. 检查表结构

```sql
-- 查看表信息（sqlite-vec 虚拟表可能不显示完整信息）
.schema vec_embeddings
```

### 2. 测试搜索

使用搜索 API 测试，匹配度应该能超过 48%：

```bash
curl -X POST http://localhost:8000/api/v1/rag/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{
    "query": "测试查询",
    "top_k": 5
  }'
```

### 3. 检查日志

查看应用日志，确认表已使用余弦距离：

```
✅ vec0虚拟表创建成功（维度: 1024，使用余弦距离）
```

## 常见问题

### Q: 删除表会丢失数据吗？

**A: 不会**。`vec_embeddings` 是虚拟表，真正的向量数据存储在 `article_embeddings` 表中。删除虚拟表只是删除了索引，数据仍然在 `article_embeddings` 中。

### Q: 如何知道向量维度？

**A: 查看您的嵌入模型配置**：
- `text-embedding-3-small`: 1024 维
- `text-embedding-3-large`: 3072 维
- `text-embedding-ada-002`: 1536 维

### Q: 迁移需要多长时间？

**A: 迁移表本身很快（几秒钟）**。但重新同步数据到新表的时间取决于：
- 已索引的文章数量
- API 调用速度
- 批处理大小

例如：1000 篇文章，批处理大小为 10，大约需要几分钟。

### Q: 可以在生产环境直接操作吗？

**A: 可以**，但建议：
1. 在低峰期操作
2. 先备份数据库（虽然不会丢失数据，但备份是好习惯）
3. 监控应用日志

## 备份数据库（可选但推荐）

```bash
# Docker 方式
docker exec <container_name> sqlite3 /app/data/database.db ".backup /app/data/database.backup.db"

# 或直接复制文件
cp /path/to/database.db /path/to/database.backup.db
```
