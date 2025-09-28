import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timezone
import time
import requests
from bs4 import BeautifulSoup

from .base import BaseCollector, Article


logger = logging.getLogger(__name__)


class HackerNewsCollector(BaseCollector):
    """Collect stories from Hacker News API"""

    API_BASE = "https://hacker-news.firebaseio.com/v0"
    WEB_ITEM_BASE = "https://news.ycombinator.com/item?id="

    def validate_config(self) -> bool:
        # No credentials needed; optional config keys
        return True

    def test_connection(self) -> bool:
        try:
            r = requests.get(f"{self.API_BASE}/.json", timeout=5)
            return r.status_code == 200
        except Exception as e:
            logger.error(f"HN connection test failed: {e}")
            return False

    def collect(self) -> Tuple[List[Article], Dict[str, Any]]:
        """Fetch recent stories from HN.

        Config options (optional):
        - list: 'new' | 'top' | 'best' (default: 'new')
        - max_items: int (default: 50)
        """
        list_type = (self.config.get('list') or 'new').lower()
        max_items = int(self.config.get('max_items', 50))

        list_endpoint = {
            'new': 'newstories',
            'top': 'topstories',
            'best': 'beststories'
        }.get(list_type, 'newstories')

        try:
            ids = self._get_story_ids(list_endpoint)
        except Exception as e:
            logger.error(f"Failed to fetch HN {list_endpoint}: {e}")
            return [], self.sync_metadata

        # Incremental sync: filter by time > last_sync_unix (if present)
        last_sync_unix = None
        if 'last_sync_unix' in self.sync_metadata:
            try:
                last_sync_unix = int(self.sync_metadata['last_sync_unix'])
            except Exception:
                last_sync_unix = None

        articles: List[Article] = []
        fetched = 0

        for story_id in ids:
            if fetched >= max_items:
                break
            item = self._get_item(story_id)
            if not item:
                continue

            if item.get('type') != 'story':
                continue

            story_time = item.get('time') or 0
            if last_sync_unix is not None and story_time <= last_sync_unix:
                # Skip older or equal items when doing incremental sync
                continue

            article = self._parse_story(item)
            if article:
                articles.append(article)
                fetched += 1

        updated_sync = dict(self.sync_metadata)
        # Update sync time to current max time among collected or now
        if articles:
            max_story_time = max(int(item.published_at.replace(tzinfo=timezone.utc).timestamp())
                                 if item.published_at else int(time.time())
                                 for item in articles)
            updated_sync['last_sync_unix'] = max_story_time
            updated_sync['last_story_count'] = len(articles)
        else:
            updated_sync['last_sync_unix'] = int(time.time())

        logger.info(f"Collected {len(articles)} stories from Hacker News")
        return articles, updated_sync

    def _get_story_ids(self, list_endpoint: str) -> List[int]:
        r = requests.get(f"{self.API_BASE}/{list_endpoint}.json", timeout=10)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list):
            return []
        return [int(x) for x in data[:500]]  # hard cap for safety

    def _get_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        try:
            r = requests.get(f"{self.API_BASE}/item/{item_id}.json", timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.warning(f"Failed to fetch HN item {item_id}: {e}")
            return None

    def _parse_story(self, item: Dict[str, Any]) -> Optional[Article]:
        try:
            title = item.get('title') or 'Untitled'
            url = item.get('url') or f"{self.WEB_ITEM_BASE}{item.get('id')}"
            author = item.get('by')
            ts = item.get('time')
            published_at = datetime.fromtimestamp(ts, tz=timezone.utc) if ts else None

            # HN "text" is optional and may contain HTML; clean to plain text
            raw_text = item.get('text') or ''
            content = self._clean_text(raw_text)

            metadata: Dict[str, Any] = {
                'hn_id': item.get('id'),
                'hn_permalink': f"{self.WEB_ITEM_BASE}{item.get('id')}",
                'score': item.get('score'),
                'comments': item.get('descendants'),
                'kids': item.get('kids', []),
                'source': 'hackernews'
            }

            return Article(
                external_id=str(item.get('id')),
                title=title,
                url=url,
                content=content[:10000] if content else None,
                author=author,
                published_at=published_at,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error parsing HN story {item.get('id')}: {e}")
            return None

    def _clean_text(self, html_text: str) -> str:
        if not html_text:
            return ''
        try:
            soup = BeautifulSoup(html_text, 'html.parser')
            text = soup.get_text("\n")
            # Normalize whitespace
            lines = [line.strip() for line in text.split('\n')]
            return '\n'.join([ln for ln in lines if ln])
        except Exception:
            return html_text


