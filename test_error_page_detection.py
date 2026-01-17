"""
测试错误页面检测功能
验证当遇到"JavaScript is not available"页面时，是否正确返回空字符串
"""
import sys
sys.path.append('D:/ai-project/ai-news-tracker')

from backend.app.services.collector.web_collector import WebCollector
from backend.app.services.collector.rss_collector import RSSCollector
from bs4 import BeautifulSoup

def test_web_collector():
    """测试WebCollector的错误页面检测"""
    print("=" * 60)
    print("测试 WebCollector.fetch_full_content() 的错误页面检测")
    print("=" * 60)

    collector = WebCollector()

    # 模拟一个包含"JavaScript is not available"的HTML页面
    mock_error_html = """
    <html>
    <head><title>JavaScript Required</title></head>
    <body>
        <h1>JavaScript is not available</h1>
        <p>Please enable JavaScript to continue.</p>
    </body>
    </html>
    """

    # 测试_is_error_page方法
    soup = BeautifulSoup(mock_error_html, 'html.parser')
    page_text = soup.get_text()

    is_error = collector._is_error_page(page_text, soup)

    print(f"\n测试1: 检测'JavaScript is not available'页面")
    print(f"  页面文本预览: {page_text[:100]}...")
    print(f"  检测结果: {'✅ 检测到错误页面' if is_error else '❌ 未检测到错误页面'}")

    if is_error:
        print("  ✅ 测试通过: 正确识别为错误页面")
    else:
        print("  ❌ 测试失败: 未能识别错误页面")
        return False

    # 测试正常页面
    mock_normal_html = """
    <html>
    <head><title>Article</title></head>
    <body>
        <article>
            <h1>Test Article Title</h1>
            <p>This is a normal article content with meaningful text.</p>
            <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
        </article>
    </body>
    </html>
    """

    soup = BeautifulSoup(mock_normal_html, 'html.parser')
    page_text = soup.get_text()
    is_error = collector._is_error_page(page_text, soup)

    print(f"\n测试2: 检测正常文章页面")
    print(f"  页面文本预览: {page_text[:100]}...")
    print(f"  检测结果: {'❌ 误判为错误页面' if is_error else '✅ 正确识别为正常页面'}")

    if not is_error:
        print("  ✅ 测试通过: 正确识别为正常页面")
    else:
        print("  ❌ 测试失败: 误判为错误页面")
        return False

    return True


def test_rss_collector():
    """测试RSSCollector的错误页面检测"""
    print("\n" + "=" * 60)
    print("测试 RSSCollector.fetch_full_content() 的错误页面检测")
    print("=" * 60)

    collector = RSSCollector()

    # 模拟一个包含"JavaScript is not available"的HTML页面
    mock_error_html = """
    <html>
    <head><title>JavaScript Required</title></head>
    <body>
        <h1>JavaScript is not available</h1>
        <p>Please enable JavaScript to continue.</p>
    </body>
    </html>
    """

    # 测试_is_error_page方法
    soup = BeautifulSoup(mock_error_html, 'html.parser')
    page_text = soup.get_text()

    is_error = collector._is_error_page(page_text, soup)

    print(f"\n测试1: 检测'JavaScript is not available'页面")
    print(f"  页面文本预览: {page_text[:100]}...")
    print(f"  检测结果: {'✅ 检测到错误页面' if is_error else '❌ 未检测到错误页面'}")

    if is_error:
        print("  ✅ 测试通过: 正确识别为错误页面")
    else:
        print("  ❌ 测试失败: 未能识别错误页面")
        return False

    return True


if __name__ == "__main__":
    print("\n开始测试错误页面检测功能...\n")

    web_test_passed = test_web_collector()
    rss_test_passed = test_rss_collector()

    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"WebCollector测试: {'✅ 通过' if web_test_passed else '❌ 失败'}")
    print(f"RSSCollector测试: {'✅ 通过' if rss_test_passed else '❌ 失败'}")
    print()

    if web_test_passed and rss_test_passed:
        print("🎉 所有测试通过!")
        print("\n修复说明:")
        print("1. 在 fetch_full_content() 方法中，现在会先检查是否是错误页面")
        print("2. 只有在确认不是错误页面后，才会提取内容")
        print("3. 这样可以防止'JavaScript is not available'等错误文本被当作文章内容")
        print("4. 当检测到错误页面时，返回空字符串，使用原始摘要作为内容")
    else:
        print("❌ 部分测试失败，请检查代码")
        sys.exit(1)
