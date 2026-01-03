"""
统一配置管理模块
"""
import os
import json
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """应用配置类"""

    def __init__(self):
        self._load_env()

    def _load_env(self):
        """加载环境变量"""
        # 首先设置项目根目录（从 backend/app/core/settings.py 计算）
        # __file__ = backend/app/core/settings.py
        # .parent = backend/app/core/
        # .parent = backend/app/
        # .parent = backend/
        # .parent = 项目根目录
        self.PROJECT_ROOT: Path = Path(__file__).parent.parent.parent.parent
        self.DATA_DIR: Path = self.PROJECT_ROOT / "backend" / "app" / "data"
        self.CONFIG_DIR: Path = self.PROJECT_ROOT / "backend" / "app"

        # 确保必要目录存在
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # OpenAI API配置
        self.OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
        self.OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

        # 飞书机器人配置
        self.FEISHU_BOT_WEBHOOK: str = os.getenv("FEISHU_BOT_WEBHOOK", "")

        # 数据库配置（默认使用 backend/app/data/ai_news.db）
        default_db_path = str(self.DATA_DIR / "ai_news.db")
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{default_db_path}")

        # 定时任务配置
        self.COLLECTION_CRON: str = os.getenv("COLLECTION_CRON", "0 */1 * * *")
        self.DAILY_SUMMARY_CRON: str = os.getenv("DAILY_SUMMARY_CRON", "0 9 * * *")

        # 采集配置
        self.MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "3"))
        self.REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
        self.MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
        self.MAX_ARTICLES_PER_SOURCE: int = int(os.getenv("MAX_ARTICLES_PER_SOURCE", "50"))

        # Web配置
        self.WEB_HOST: str = os.getenv("WEB_HOST", "0.0.0.0")
        self.WEB_PORT: int = int(os.getenv("WEB_PORT", "8501"))

        # 日志配置
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FILE: Optional[str] = os.getenv("LOG_FILE")
        
        # 文章过滤配置（从配置文件读取，支持运行时修改）
        self._load_collection_settings()
        
        # 总结配置（从配置文件读取，支持运行时修改）
        self._load_summary_settings()

    def is_ai_enabled(self) -> bool:
        """检查AI分析是否启用"""
        return bool(self.OPENAI_API_KEY)

    def is_feishu_enabled(self) -> bool:
        """检查飞书通知是否启用"""
        return bool(self.FEISHU_BOT_WEBHOOK)
    
    def _load_collection_settings(self):
        """加载采集配置（从JSON文件读取，支持运行时修改）"""
        collection_settings_path = self.CONFIG_DIR / "collection_settings.json"
        try:
            with open(collection_settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
                self.MAX_ARTICLE_AGE_DAYS: int = int(settings.get("max_article_age_days", 30))
                self.MAX_ANALYSIS_AGE_DAYS: int = int(settings.get("max_analysis_age_days", 7))
                # 自动采集配置
                self.AUTO_COLLECTION_ENABLED: bool = settings.get("auto_collection_enabled", False)
                self.AUTO_COLLECTION_TIME: str = settings.get("auto_collection_time", "09:00")
        except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as e:
            # 如果文件不存在或解析失败，使用默认值
            self.MAX_ARTICLE_AGE_DAYS: int = int(os.getenv("MAX_ARTICLE_AGE_DAYS", "30"))
            self.MAX_ANALYSIS_AGE_DAYS: int = int(os.getenv("MAX_ANALYSIS_AGE_DAYS", "7"))
            self.AUTO_COLLECTION_ENABLED: bool = False
            self.AUTO_COLLECTION_TIME: str = "09:00"
    
    def save_collection_settings(self, max_article_age_days: int, max_analysis_age_days: int):
        """保存采集配置到JSON文件"""
        collection_settings_path = self.CONFIG_DIR / "collection_settings.json"
        # 先读取现有配置（如果存在）
        existing_settings = {}
        try:
            with open(collection_settings_path, "r", encoding="utf-8") as f:
                existing_settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        settings = {
            "max_article_age_days": max_article_age_days,
            "max_analysis_age_days": max_analysis_age_days,
            # 保留自动采集配置
            "auto_collection_enabled": existing_settings.get("auto_collection_enabled", False),
            "auto_collection_time": existing_settings.get("auto_collection_time", "09:00"),
        }
        try:
            with open(collection_settings_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            # 重新加载配置
            self._load_collection_settings()
            return True
        except Exception as e:
            print(f"保存采集配置失败: {e}")
            return False
    
    def save_auto_collection_settings(self, enabled: bool, time: str):
        """保存自动采集配置到JSON文件"""
        collection_settings_path = self.CONFIG_DIR / "collection_settings.json"
        # 先读取现有配置（如果存在）
        existing_settings = {}
        try:
            with open(collection_settings_path, "r", encoding="utf-8") as f:
                existing_settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        settings = {
            "max_article_age_days": existing_settings.get("max_article_age_days", 30),
            "max_analysis_age_days": existing_settings.get("max_analysis_age_days", 7),
            "auto_collection_enabled": enabled,
            "auto_collection_time": time,
        }
        try:
            with open(collection_settings_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            # 重新加载配置
            self._load_collection_settings()
            return True
        except Exception as e:
            print(f"保存自动采集配置失败: {e}")
            return False
    
    def _load_summary_settings(self):
        """加载总结配置（从JSON文件读取，支持运行时修改）"""
        collection_settings_path = self.CONFIG_DIR / "collection_settings.json"
        try:
            with open(collection_settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
                # 每日总结配置
                self.DAILY_SUMMARY_ENABLED: bool = settings.get("daily_summary_enabled", True)
                self.DAILY_SUMMARY_TIME: str = settings.get("daily_summary_time", "09:00")
                # 每周总结配置
                self.WEEKLY_SUMMARY_ENABLED: bool = settings.get("weekly_summary_enabled", True)
                self.WEEKLY_SUMMARY_TIME: str = settings.get("weekly_summary_time", "09:00")
        except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as e:
            # 如果文件不存在或解析失败，使用默认值
            self.DAILY_SUMMARY_ENABLED: bool = True
            self.DAILY_SUMMARY_TIME: str = "09:00"
            self.WEEKLY_SUMMARY_ENABLED: bool = True
            self.WEEKLY_SUMMARY_TIME: str = "09:00"
    
    def save_summary_settings(self, daily_enabled: bool, daily_time: str, weekly_enabled: bool, weekly_time: str):
        """保存总结配置到JSON文件"""
        collection_settings_path = self.CONFIG_DIR / "collection_settings.json"
        # 先读取现有配置（如果存在）
        existing_settings = {}
        try:
            with open(collection_settings_path, "r", encoding="utf-8") as f:
                existing_settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        settings = {
            # 保留采集配置
            "max_article_age_days": existing_settings.get("max_article_age_days", 30),
            "max_analysis_age_days": existing_settings.get("max_analysis_age_days", 7),
            "auto_collection_enabled": existing_settings.get("auto_collection_enabled", False),
            "auto_collection_time": existing_settings.get("auto_collection_time", "09:00"),
            # 总结配置
            "daily_summary_enabled": daily_enabled,
            "daily_summary_time": daily_time,
            "weekly_summary_enabled": weekly_enabled,
            "weekly_summary_time": weekly_time,
        }
        try:
            with open(collection_settings_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            # 重新加载配置
            self._load_summary_settings()
            return True
        except Exception as e:
            print(f"保存总结配置失败: {e}")
            return False
    
    def get_auto_collection_cron(self) -> str:
        """根据自动采集时间生成cron表达式"""
        if not self.AUTO_COLLECTION_ENABLED:
            return None
        
        try:
            hour, minute = self.AUTO_COLLECTION_TIME.split(":")
            hour = int(hour)
            minute = int(minute)
            # cron格式: 分 时 日 月 周
            return f"{minute} {hour} * * *"
        except (ValueError, AttributeError):
            return None
    
    def get_daily_summary_cron(self) -> str:
        """根据每日总结时间生成cron表达式"""
        if not self.DAILY_SUMMARY_ENABLED:
            return None
        
        try:
            hour, minute = self.DAILY_SUMMARY_TIME.split(":")
            hour = int(hour)
            minute = int(minute)
            # cron格式: 分 时 日 月 周（每天执行）
            return f"{minute} {hour} * * *"
        except (ValueError, AttributeError):
            return None
    
    def get_weekly_summary_cron(self) -> str:
        """根据每周总结时间生成cron表达式（周六执行）"""
        if not self.WEEKLY_SUMMARY_ENABLED:
            return None
        
        try:
            hour, minute = self.WEEKLY_SUMMARY_TIME.split(":")
            hour = int(hour)
            minute = int(minute)
            # cron格式: 分 时 日 月 周（周六执行，6表示周六）
            return f"{minute} {hour} * * 6"
        except (ValueError, AttributeError):
            return None


# 全局配置实例
settings = Settings()

