# 导入错误修复说明

## 问题描述

```
ImportError: attempted relative import beyond top-level package
```

## 原因

Python的相对导入 (`from .module import something`) 在作为脚本直接运行时会失败。

## 解决方案

已将所有相对导入改为绝对导入：

### 修改前（相对导入）
```python
from .service import CollectionService
from ..database import get_db
```

### 修改后（绝对导入）
```python
from collector.service import CollectionService
from database import get_db
```

## 测试方法

### 方法1：快速测试
```bash
cd ai-news-tracker
python quick_test.py
```

### 方法2：测试主程序
```bash
cd ai-news-tracker
python main.py --help
```

### 方法3：测试Web界面
```bash
cd ai-news-tracker
python main.py web
```

## 如果仍然失败

### 方案A：使用模块方式运行
```bash
cd ai-news-tracker
python -m main web
```

### 方案B：设置PYTHONPATH
```bash
# Windows
set PYTHONPATH=D:\ai_projects\auto-work\ai-news-tracker
python main.py web

# Linux/Mac
export PYTHONPATH=/path/to/ai-news-tracker
python main.py web
```

### 方案C：创建启动脚本
创建 `run.bat` (Windows) 或 `run.sh` (Linux/Mac):

**run.bat**:
```bat
@echo off
set PYTHONPATH=%CD%
python main.py %*
```

**run.sh**:
```bash
#!/bin/bash
export PYTHONPATH="$(pwd)"
python main.py "$@"
```

使用：
```bash
run.bat web    # Windows
./run.sh web   # Linux/Mac
```

## 已修复的文件

- ✅ collector/__init__.py
- ✅ collector/service.py
- ✅ analyzer/__init__.py
- ✅ database/__init__.py
- ✅ notification/__init__.py
- ✅ notification/service.py

## 注意事项

1. **main.py**、**scheduler.py**、**web/app.py** 已经正确设置了 `sys.path`，不需要修改
2. 所有导入都使用绝对路径，确保在任何方式运行都能正常工作
3. 测试脚本 `quick_test.py` 可以快速验证导入是否正常

## 验证成功

如果看到以下输出，说明修复成功：

```
测试导入...
============================================================
1. 测试 database...
   ✅ database 导入成功
2. 测试 analyzer...
   ✅ analyzer 导入成功
3. 测试 collector...
   ✅ collector 导入成功
4. 测试 notification...
   ✅ notification 导入成功
============================================================
✅ 所有导入测试通过！
```

现在可以正常使用所有功能了！
