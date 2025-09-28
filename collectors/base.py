from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass


@dataclass
class Article:
    """Common article format all collectors must provide"""
    external_id: str
    title: str
    url: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseCollector(ABC):
    """Abstract base class for all content collectors"""

    def __init__(self, source_config: Dict[str, Any]):
        self.source_id = source_config['id']
        self.source_name = source_config['name']
        self.config = source_config.get('config', {})
        self.sync_metadata = source_config.get('sync_metadata', {})

    @abstractmethod
    def collect(self) -> Tuple[List[Article], Dict[str, Any]]:
        """
        Collect articles from the source
        Returns: (list of articles, updated sync_metadata for incremental sync)
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """Validate that required configuration fields are present"""
        pass

    def test_connection(self) -> bool:
        """Optional: Test if the source is accessible"""
        return True


