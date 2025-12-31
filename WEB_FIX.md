# Web界面启动修复

## 问题

Streamlit 报错找不到 secrets.toml 文件。

## 解决方案

已修改 `web/app.py`，改为从 `.env` 文件读取配置，不需要 Streamlit secrets。

## 如何启动

### 1. 确保 .env 文件存在

```bash
# 如果不存在，复制示例文件
copy .env.example .env
```

### 2. 编辑 .env 文件

```bash
notepad .env
```

**最小配置**（必需）：
```env
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview
```

### 3. 启动 Web 界面

```bash
python main.py web
```

或使用快捷菜单：
```bash
start.bat
```

选择选项 4：启动Web界面

### 4. 访问

浏览器会自动打开 http://localhost:8501

如果没自动打开，手动访问：http://localhost:8501

## 功能说明

### 控制面板（左侧）
- **开始采集**：手动触发数据采集（包含AI分析）
- **数据统计**：显示总文章数、今日新增、待分析数
- **筛选选项**：按时间、来源、重要性、分类筛选

### 文章列表
- 卡片式展示
- 显示AI总结、关键点、标签
- 可展开查看完整内容
- 重要性用颜色标识：
  - 🔴 高重要性
  - 🟡 中重要性
  - 🟢 低重要性

### 数据统计
- 来源分布图表
- 文章数量统计

## 不配置 API 能用吗？

**可以！** 但功能会受限：

### 有 API Key
- ✅ 自动采集并AI分析
- ✅ 自动生成摘要
- ✅ 智能标签和分类
- ✅ 重要性评分

### 无 API Key
- ✅ 可以采集文章
- ✅ 可以浏览和筛选
- ❌ 没有AI摘要和分析
- ❌ 没有智能标签

**建议**：先不配置API测试界面，配置好API后再启用AI分析。

## 常见问题

### 1. 端口被占用

```
Port 8501 is already in use
```

**解决**：关闭占用端口的程序，或修改端口：
```bash
streamlit run web/app.py --server.port 8502
```

### 2. 采集失败

**可能原因**：
- 网络问题
- API Key无效
- RSS源无法访问

**解决**：查看终端错误信息

### 3. 界面空白

**解决**：
1. 检查浏览器控制台错误
2. 刷新页面
3. 重启Streamlit

## 下一步

1. ✅ 启动Web界面测试
2. ✅ 点击"开始采集"按钮
3. ✅ 浏览文章列表
4. ✅ 尝试筛选功能
5. ✅ 配置好API后重新采集

## 提示

- 首次采集可能需要几分钟
- AI分析会增加采集时间
- 可以定期点击"开始采集"更新数据
- 建议配置定时任务自动采集

现在可以正常使用了！🎉
