"""
数据采集模块
"""
from backend.app.services.collector.rss_collector import RSSCollector
from backend.app.services.collector.api_collector import ArXivCollector, HuggingFaceCollector, PapersWithCodeCollector
from backend.app.services.collector.service import CollectionService

__all__ = [
    "RSSCollector",
    "ArXivCollector",
    "HuggingFaceCollector",
    "PapersWithCodeCollector",
    "CollectionService",
]
