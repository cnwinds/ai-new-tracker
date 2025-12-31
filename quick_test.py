"""
快速测试导入是否正常
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("测试导入...")
print("=" * 60)

try:
    print("1. 测试 database...")
    from database import get_db
    print("   ✅ database 导入成功")

    print("2. 测试 analyzer...")
    from analyzer import AIAnalyzer
    print("   ✅ analyzer 导入成功")

    print("3. 测试 collector...")
    from collector import CollectionService, RSSCollector
    print("   ✅ collector 导入成功")

    print("4. 测试 notification...")
    from notification import NotificationService
    print("   ✅ notification 导入成功")

    print("=" * 60)
    print("✅ 所有导入测试通过！")

except Exception as e:
    print("=" * 60)
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
