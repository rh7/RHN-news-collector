"""Manual endpoint to collect from specific source"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from core.db_client import DatabaseClient
from collectors.readwise import ReadwiseCollector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def handler(request):
    """Collect only from Readwise - useful for testing"""
    try:
        db = DatabaseClient()

        source = db.table('sources') \
            .select('*') \
            .eq('type', 'readwise') \
            .eq('enabled', True) \
            .single() \
            .execute()

        if not getattr(source, 'data', None):
            return {
                'statusCode': 404,
                'body': {'error': 'Readwise source not found or disabled'}
            }

        collector = ReadwiseCollector(source.data)
        articles, sync_metadata = collector.collect()

        saved = 0
        for article in articles:
            try:
                db.table('contents').upsert({
                    'source_id': source.data['id'],
                    'external_id': article.external_id,
                    'title': article.title,
                    'url': article.url,
                    'content': article.content,
                    'author': article.author,
                    'published_at': article.published_at.isoformat() if article.published_at else None,
                    'metadata': article.metadata
                }, on_conflict='source_id,external_id').execute()
                saved += 1
            except Exception as e:
                logger.error(f"Failed to save article: {e}")

        db.table('sources').update({
            'last_sync': datetime.utcnow().isoformat(),
            'last_sync_status': 'success',
            'sync_metadata': sync_metadata
        }).eq('id', source.data['id']).execute()

        return {
            'statusCode': 200,
            'body': {
                'articles_collected': saved,
                'total_articles': len(articles)
            }
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': {'error': str(e)}
        }


