import requests
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
from .base import BaseCollector, Article

logger = logging.getLogger(__name__)


class ReadwiseCollector(BaseCollector):
    """Collect articles from Readwise Reader API"""

    API_BASE_URL = "https://readwise.io/api/v3"

    def validate_config(self) -> bool:
        """Ensure API token is present"""
        return bool(self.config.get('api_token'))

    def test_connection(self) -> bool:
        """Test Readwise API connectivity"""
        try:
            headers = {'Authorization': f"Token {self.config['api_token']}"}
            response = requests.get(
                f"{self.API_BASE_URL}/auth/",
                headers=headers,
                timeout=5
            )
            return response.status_code == 204
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def collect(self) -> Tuple[List[Article], Dict[str, Any]]:
        """Fetch articles from Readwise Reader"""
        articles: List[Article] = []
        updated_sync_metadata = dict(self.sync_metadata)

        headers = { 'Authorization': f"Token {self.config['api_token']}" }

        params: Dict[str, Any] = { 'category': 'article' }

        if 'location' in self.config:
            params['location'] = self.config['location']

        if 'last_sync_date' in self.sync_metadata:
            params['updated__gt'] = self.sync_metadata['last_sync_date']

        next_url = f"{self.API_BASE_URL}/list/"
        total_fetched = 0

        while next_url and total_fetched < 1000:
            try:
                response = requests.get(
                    next_url,
                    headers=headers,
                    params=params if next_url == f"{self.API_BASE_URL}/list/" else None,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()

                for item in data.get('results', []):
                    article = self._parse_article(item)
                    if article:
                        articles.append(article)
                        total_fetched += 1

                next_url = data.get('next')

            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching from Readwise: {e}")
                break

        if articles:
            updated_sync_metadata['last_sync_date'] = datetime.utcnow().isoformat()
            updated_sync_metadata['last_article_count'] = len(articles)

        logger.info(f"Collected {len(articles)} articles from Readwise")
        return articles, updated_sync_metadata

    def _parse_article(self, item: Dict[str, Any]) -> Optional[Article]:
        """Parse Readwise item into Article object"""
        try:
            if item.get('category') != 'article':
                return None

            content = self._extract_content(item)

            published_at = None
            if item.get('published_date'):
                try:
                    published_at = datetime.fromisoformat(
                        item['published_date'].replace('Z', '+00:00')
                    )
                except Exception:
                    published_at = None

            return Article(
                external_id=str(item['id']),
                title=item.get('title', 'Untitled'),
                url=item.get('url'),
                content=content,
                author=item.get('author'),
                published_at=published_at,
                metadata={
                    'readwise_url': item.get('reader_url'),
                    'word_count': item.get('word_count'),
                    'reading_progress': item.get('reading_progress', 0),
                    'tags': item.get('tags', []),
                    'highlights_count': len(item.get('highlights', [])),
                    'summary': item.get('summary'),
                    'location': item.get('location'),
                }
            )
        except Exception as e:
            logger.error(f"Error parsing article {item.get('id')}: {e}")
            return None

    def _extract_content(self, item: Dict[str, Any]) -> str:
        """Extract and clean content from Readwise item"""
        content = item.get('content', '')

        if not content:
            content = item.get('summary', '')

        if not content and item.get('highlights'):
            highlights = [h['text'] for h in item['highlights'] if 'text' in h]
            if highlights:
                content = '\n\n---\n\n'.join(highlights)

        if content:
            lines = [line.strip() for line in content.split('\n')]
            content = '\n'.join(line for line in lines if line)

        return content[:10000]


