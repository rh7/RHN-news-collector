import logging
from typing import Dict, List, Type, Any
from datetime import datetime
import importlib
from collectors.base import BaseCollector, Article

logger = logging.getLogger(__name__)


class CollectorManager:
    """Manages and orchestrates all content collectors"""

    COLLECTOR_REGISTRY: Dict[str, str] = {
        'readwise': 'collectors.readwise.ReadwiseCollector',
        'hackernews': 'collectors.hackernews.HackerNewsCollector',
    }

    def __init__(self, db_client):
        self.db = db_client
        self.collectors: Dict[str, Type[BaseCollector]] = {}
        self._load_collectors()

    def _load_collectors(self):
        """Dynamically load available collectors"""
        for name, import_path in self.COLLECTOR_REGISTRY.items():
            try:
                module_path, class_name = import_path.rsplit('.', 1)
                module = importlib.import_module(module_path)
                collector_class = getattr(module, class_name)
                self.collectors[name] = collector_class
                logger.info(f"Loaded collector: {name}")
            except Exception as e:
                logger.warning(f"Failed to load collector {name}: {e}")

    def collect_all_sources(self) -> Dict[str, Any]:
        """Run collection for all enabled sources"""
        sources_response = self.db.table('sources') \
            .select('*') \
            .eq('enabled', True) \
            .execute()

        if not getattr(sources_response, 'data', None):
            logger.info("No enabled sources found")
            return {'sources_processed': 0, 'total_articles': 0}

        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'sources_processed': 0,
            'total_articles': 0,
            'errors': [],
            'source_results': []
        }

        for source in sources_response.data:
            source_result = self._collect_single_source(source)
            results['source_results'].append(source_result)

            if source_result['status'] == 'success':
                results['sources_processed'] += 1
                results['total_articles'] += source_result['articles_collected']
            else:
                if source_result.get('error'):
                    results['errors'].append(source_result['error'])

        logger.info(
            f"Collection complete: {results['sources_processed']} sources, "
            f"{results['total_articles']} articles"
        )
        return results

    def _collect_single_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """Collect from a single source"""
        source_result = {
            'source_name': source['name'],
            'source_type': source['type'],
            'status': 'pending',
            'articles_collected': 0,
            'error': None
        }

        try:
            if source['type'] not in self.collectors:
                raise ValueError(f"No collector found for type: {source['type']}")

            collector_class = self.collectors[source['type']]
            collector = collector_class(source)

            if not collector.validate_config():
                raise ValueError("Invalid source configuration")

            if not collector.test_connection():
                logger.warning(f"Connection test failed for {source['name']}")

            articles, updated_sync_metadata = collector.collect()

            saved_count = self._save_articles(articles, source['id'])

            self.db.table('sources').update({
                'last_sync': datetime.utcnow().isoformat(),
                'last_sync_status': 'success',
                'sync_metadata': updated_sync_metadata
            }).eq('id', source['id']).execute()

            source_result['status'] = 'success'
            source_result['articles_collected'] = saved_count

            logger.info(
                f"Successfully collected {saved_count} articles from {source['name']}"
            )

        except Exception as e:
            error_msg = f"Failed to collect from {source['name']}: {str(e)}"
            logger.error(error_msg)

            self.db.table('sources').update({
                'last_sync': datetime.utcnow().isoformat(),
                'last_sync_status': 'failed'
            }).eq('id', source['id']).execute()

            source_result['status'] = 'failed'
            source_result['error'] = error_msg

        return source_result

    def _save_articles(self, articles: List[Article], source_id: str) -> int:
        """Save articles to database"""
        saved_count = 0

        for article in articles:
            try:
                article_data = {
                    'source_id': source_id,
                    'external_id': article.external_id,
                    'title': article.title,
                    'url': article.url,
                    'content': article.content,
                    'author': article.author,
                    'published_at': article.published_at.isoformat() if article.published_at else None,
                    'metadata': article.metadata
                }

                self.db.table('contents').upsert(
                    article_data,
                    on_conflict='source_id,external_id'
                ).execute()

                saved_count += 1

            except Exception as e:
                logger.error(f"Failed to save article '{article.title}': {e}")

        return saved_count


