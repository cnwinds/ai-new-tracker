"""
PDF 处理器 - 将 PDF 文件转换为 Markdown 文本
"""
import io
import logging
from typing import Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class PDFProcessor:
    """PDF 文件处理器"""

    def __init__(self):
        """初始化 PDF 处理器"""
        try:
            import PyPDF2
            self.pypdf2_available = True
        except ImportError:
            self.pypdf2_available = False
            logger.warning("⚠️  PyPDF2 未安装，PDF 处理功能将不可用")

        try:
            import pdfplumber
            self.pdfplumber_available = True
        except ImportError:
            self.pdfplumber_available = False
            logger.warning("⚠️  pdfplumber 未安装，将使用 PyPDF2 作为备选")

    def is_pdf_url(self, url: str) -> bool:
        """
        检查 URL 是否指向 PDF 文件

        Args:
            url: 要检查的 URL

        Returns:
            是否是 PDF URL
        """
        if not url:
            return False

        # 检查 URL 路径是否以 .pdf 结尾
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()

        return path.endswith('.pdf')

    def fetch_and_extract_pdf(self, url: str, timeout: int = 30) -> Tuple[Optional[str], Optional[str]]:
        """
        从 URL 获取 PDF 文件并提取文本内容

        Args:
            url: PDF 文件的 URL
            timeout: 请求超时时间（秒）

        Returns:
            (提取的文本内容, 错误信息) 的元组，如果成功则错误信息为 None
        """
        try:
            import requests
            logger.info(f"📄 正在下载 PDF 文件: {url}")

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(url, headers=headers, timeout=timeout, stream=True)
            response.raise_for_status()

            # 检查 Content-Type 是否为 PDF
            content_type = response.headers.get('Content-Type', '')
            if 'pdf' not in content_type.lower():
                logger.warning(f"⚠️  URL 的 Content-Type 不是 PDF: {content_type}")

            # 读取 PDF 内容
            pdf_file = io.BytesIO(response.content)

            # 提取文本
            text = self.extract_pdf_text(pdf_file)

            if text:
                logger.info(f"✅ 成功提取 PDF 文本，长度: {len(text)} 字符")
                return text, None
            else:
                return None, "PDF 文本提取失败或文件为空"

        except requests.RequestException as e:
            error_msg = f"下载 PDF 文件失败: {e}"
            logger.error(f"❌ {error_msg}")
            return None, error_msg
        except Exception as e:
            error_msg = f"处理 PDF 文件失败: {e}"
            logger.error(f"❌ {error_msg}")
            return None, error_msg

    def extract_pdf_text(self, pdf_file) -> str:
        """
        从 PDF 文件对象提取文本内容

        Args:
            pdf_file: PDF 文件对象（类文件对象）

        Returns:
            提取的文本内容
        """
        # 优先使用 pdfplumber（提取效果更好）
        if self.pdfplumber_available:
            return self._extract_with_pdfplumber(pdf_file)
        # 备选使用 PyPDF2
        elif self.pypdf2_available:
            return self._extract_with_pypdf2(pdf_file)
        else:
            logger.error("❌ 没有可用的 PDF 处理库，请安装 pdfplumber 或 PyPDF2")
            return ""

    def _extract_with_pdfplumber(self, pdf_file) -> str:
        """
        使用 pdfplumber 提取文本

        Args:
            pdf_file: PDF 文件对象

        Returns:
            提取的文本
        """
        try:
            import pdfplumber

            text_parts = []
            with pdfplumber.open(pdf_file) as pdf:
                total_pages = len(pdf.pages)
                logger.info(f"📖 PDF 共 {total_pages} 页，开始提取...")

                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            # 清理文本
                            page_text = self._clean_text(page_text)
                            text_parts.append(f"## 第 {page_num} 页\n\n{page_text}\n")

                            # 每处理10页记录一次进度
                            if page_num % 10 == 0:
                                logger.info(f"  📄 已处理 {page_num}/{total_pages} 页...")

                    except Exception as e:
                        logger.warning(f"⚠️  第 {page_num} 页提取失败: {e}")
                        continue

            extracted_text = "\n".join(text_parts)
            logger.info(f"✅ pdfplumber 提取完成，共 {len(extracted_text)} 字符")
            return extracted_text

        except Exception as e:
            logger.error(f"❌ pdfplumber 提取失败: {e}")
            # 回退到 PyPDF2
            if self.pypdf2_available:
                logger.info("🔄 回退到 PyPDF2...")
                return self._extract_with_pypdf2(pdf_file)
            return ""

    def _extract_with_pypdf2(self, pdf_file) -> str:
        """
        使用 PyPDF2 提取文本

        Args:
            pdf_file: PDF 文件对象

        Returns:
            提取的文本
        """
        try:
            import PyPDF2

            text_parts = []
            reader = PyPDF2.PdfReader(pdf_file)
            total_pages = len(reader.pages)
            logger.info(f"📖 PDF 共 {total_pages} 页，开始提取...")

            for page_num in range(total_pages):
                try:
                    page = reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        # 清理文本
                        page_text = self._clean_text(page_text)
                        text_parts.append(f"## 第 {page_num + 1} 页\n\n{page_text}\n")

                        # 每处理10页记录一次进度
                        if (page_num + 1) % 10 == 0:
                            logger.info(f"  📄 已处理 {page_num + 1}/{total_pages} 页...")

                except Exception as e:
                    logger.warning(f"⚠️  第 {page_num + 1} 页提取失败: {e}")
                    continue

            extracted_text = "\n".join(text_parts)
            logger.info(f"✅ PyPDF2 提取完成，共 {len(extracted_text)} 字符")
            return extracted_text

        except Exception as e:
            logger.error(f"❌ PyPDF2 提取失败: {e}")
            return ""

    def _clean_text(self, text: str) -> str:
        """
        清理提取的文本

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        if not text:
            return ""

        # 移除多余的空行
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]

        # 重新组合，保留段落结构
        cleaned = '\n'.join(lines)

        return cleaned

    def pdf_to_markdown(self, url: str, title: str = "", timeout: int = 30) -> Tuple[str, Optional[str]]:
        """
        将 PDF 文件转换为 Markdown 格式

        Args:
            url: PDF 文件的 URL
            title: 文档标题（可选）
            timeout: 请求超时时间

        Returns:
            (Markdown 内容, 错误信息) 的元组
        """
        try:
            # 提取 PDF 文本
            text, error = self.fetch_and_extract_pdf(url, timeout)

            if error:
                return "", error

            # 构建 Markdown 格式
            markdown_parts = []

            if title:
                markdown_parts.append(f"# {title}\n")

            markdown_parts.append(text)

            markdown_content = "\n".join(markdown_parts)

            logger.info(f"✅ PDF 转 Markdown 完成，总长度: {len(markdown_content)} 字符")
            return markdown_content, None

        except Exception as e:
            error_msg = f"PDF 转 Markdown 失败: {e}"
            logger.error(f"❌ {error_msg}")
            return "", error_msg


# 全局单例实例
_pdf_processor = None


def get_pdf_processor() -> PDFProcessor:
    """
    获取 PDF 处理器单例

    Returns:
        PDFProcessor 实例
    """
    global _pdf_processor
    if _pdf_processor is None:
        _pdf_processor = PDFProcessor()
    return _pdf_processor
