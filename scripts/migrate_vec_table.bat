@echo off
REM 迁移 vec_embeddings 表到余弦距离的便捷脚本（Windows）

echo ========================================
echo 迁移 vec_embeddings 表到余弦距离
echo ========================================
echo.

REM 检查是否在 Docker 环境中
if exist "docker\docker-compose.yml" (
    echo 检测到 Docker 环境
    set CONTAINER_NAME=ai-news-tracker-backend
    set DB_PATH=/app/backend/app/data/ai_news.db
    
    REM 检查容器是否运行
    docker ps | findstr "%CONTAINER_NAME%" >nul
    if errorlevel 1 (
        echo 错误: 容器 %CONTAINER_NAME% 未运行
        echo 请先启动容器: docker-compose up -d
        exit /b 1
    )
    
    echo 在容器内执行迁移...
    docker exec -it %CONTAINER_NAME% python -m backend.app.db.migrate_vec_table --db-path %DB_PATH% --embedding-model text-embedding-3-small
    
    if errorlevel 1 (
        echo 迁移失败
        exit /b 1
    ) else (
        echo.
        echo 迁移成功！
        echo.
        echo 下一步操作：
        echo 1. 重启应用: docker-compose restart backend
        echo 2. 重新索引文章（通过 API 或前端界面）
    )
) else (
    echo 检测到本地环境
    set DB_PATH=.\docker\data\ai_news.db
    
    if not exist "%DB_PATH%" (
        echo 错误: 数据库文件不存在: %DB_PATH%
        exit /b 1
    )
    
    echo 在本地执行迁移...
    python -m backend.app.db.migrate_vec_table --db-path %DB_PATH% --embedding-model text-embedding-3-small
    
    if errorlevel 1 (
        echo 迁移失败
        exit /b 1
    ) else (
        echo.
        echo 迁移成功！
        echo.
        echo 下一步操作：
        echo 1. 重启应用
        echo 2. 重新索引文章（通过 API 或前端界面）
    )
)

pause
