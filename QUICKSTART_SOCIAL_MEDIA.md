# 社交平台热帖采集 - 快速开始指南

## ✅ 系统已成功集成!

所有组件已正确安装并测试通过。

## 📋 已创建的文件

### 核心服务
- `backend/app/services/social_media/youtube_collector.py` - YouTube采集器
- `backend/app/services/social_media/twitter_collector.py` - Twitter采集器
- `backend/app/services/social_media/tiktok_collector.py` - TikTok采集器
- `backend/app/services/social_media/report_generator.py` - 报告生成器
- `backend/app/services/social_media/collector.py` - 统一采集服务

### API接口
- `backend/app/api/v1/endpoints/social_media.py` - API端点

### 数据模型
- `backend/app/db/models.py` - 已添加 `SocialMediaPost` 和 `SocialMediaReport` 模型

### 数据库迁移
- `backend/app/db/migrations/add_social_media_tables.py` - 数据库表创建脚本

## 🚀 快速开始

### 1. 配置API密钥

在 `backend/app/core/settings.py` 或环境变量中添加:

```python
# YouTube Data API v3
YOUTUBE_API_KEY = "your_youtube_api_key_here"

# Twitter API (twitterapi.io)
TWITTER_API_KEY = "your_twitter_api_key_here"

# TikTok API (RapidAPI)
TIKTOK_API_KEY = "your_tiktok_api_key_here"
```

### 2. 创建数据库表

```python
from backend.app.db.migrations.add_social_media_tables import upgrade
from backend.app.db import get_db

db = get_db()
upgrade(db.session)
```

### 3. 启动服务器

```bash
cd backend
python -m app.main
```

### 4. 测试API

#### 采集热帖
```bash
curl -X POST "http://localhost:8000/api/v1/social-media/collect" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "youtube_enabled": true,
    "tiktok_enabled": true,
    "twitter_enabled": true,
    "query": "AI",
    "max_results": 50
  }'
```

#### 生成报告
```bash
curl -X POST "http://localhost:8000/api/v1/social-media/report/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "youtube_enabled": true,
    "tiktok_enabled": true,
    "twitter_enabled": true
  }'
```

#### 查看统计
```bash
curl -X GET "http://localhost:8000/api/v1/social-media/stats"
```

## 📊 API端点列表

| 方法 | 端点 | 说明 |
|-----|------|------|
| POST | `/api/v1/social-media/collect` | 采集热帖 |
| POST | `/api/v1/social-media/report/generate` | 生成日报 |
| GET | `/api/v1/social-media/posts` | 查看热帖列表 |
| GET | `/api/v1/social-media/reports` | 查看报告列表 |
| GET | `/api/v1/social-media/stats` | 获取统计信息 |
| DELETE | `/api/v1/social-media/posts/{id}` | 删除热帖 |
| DELETE | `/api/v1/social-media/reports/{id}` | 删除报告 |

## 🎯 核心功能

### 1. YouTube热帖采集
- 搜索AI相关视频
- 过滤条件:播放量 > 20万
- 获取视频统计信息

### 2. TikTok爆款视频
- 搜索AI相关视频
- 智能爆款指数算法
- 过滤条件:爆款指数 > 8.0

### 3. Twitter热点推文
- 搜索AI相关推文
- 热度评分算法
- 过滤条件:观看量 > 1万 且 热度 > 1000

### 4. 自动报告生成
- Markdown格式日报
- 按平台分组展示
- 包含统计信息和热门排行

## ⚙️ 配置参数

### YouTube
- `youtube_min_view_count`: 最小观看量 (默认: 200000)
- `youtube_max_days`: 采集天数 (默认: 1)
- `max_results`: 最大结果数 (默认: 50)

### TikTok
- `tiktok_min_viral_score`: 最小爆款指数 (默认: 8.0)
- `tiktok_max_days`: 采集天数 (默认: 14)
- `max_results`: 最大结果数 (默认: 50)

### Twitter
- `twitter_min_view_count`: 最小观看量 (默认: 10000)
- `twitter_min_engagement_score`: 最小热度评分 (默认: 1000)
- `max_results`: 最大结果数 (默认: 100)

## 🔍 爆款算法说明

### TikTok爆款指数
```
爆款指数 = (播放/粉丝比 × 3.0) +
          (点赞率 × 1.0) +
          (评论率 × 5.0) +
          (分享率 × 10.0)
```

### Twitter热度评分
```
热度评分 = 点赞数 + (转发数 × 2) + (回复数 × 1.5) + (引用数 × 2)
```

## ⚠️ 注意事项

1. **API限额**: 各平台API都有调用限制,请合理设置采集频率
2. **数据去重**: 系统自动去重,不会重复采集相同的帖子
3. **异步处理**: AI分析采用异步处理,不会阻塞采集流程
4. **错误处理**: 某个平台失败不影响其他平台

## 📚 更多信息

详细文档请参考: `SOCIAL_MEDIA_INTEGRATION.md`

## 🧪 测试

运行测试脚本验证安装:
```bash
python test_social_media.py
```

所有测试应该显示 ✅ 通过!
