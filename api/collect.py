"""Vercel endpoint for scheduled collection"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from core.db_client import DatabaseClient
from core.collector_manager import CollectorManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def handler(request):
    """Vercel handler function"""
    # Optional protection: if CRON_SECRET is set, require it via query or header
    cron_secret = os.environ.get('CRON_SECRET')
    if cron_secret:
        try:
            # Vercel provides request as a dict-like with 'query' and 'headers' in Python functions
            # Fall back defensively if shape differs
            query = {}
            headers = {}
            if isinstance(request, dict):
                query = (request.get('query') or
                         request.get('queryStringParameters') or {})
                headers = (request.get('headers') or {})

            provided = None
            if isinstance(query, dict):
                provided = query.get('secret') or provided
            if isinstance(headers, dict):
                provided = headers.get('x-cron-secret') or headers.get('X-CRON-SECRET') or provided

            if provided != cron_secret:
                return {
                    'statusCode': 403,
                    'body': {'error': 'Forbidden'}
                }
        except Exception:
            return {
                'statusCode': 403,
                'body': {'error': 'Forbidden'}
            }
    logger.info(f"Collection triggered at {datetime.utcnow()}")

    try:
        db = DatabaseClient()

        if not db.test_connection():
            return {
                'statusCode': 500,
                'body': {'error': 'Database connection failed'}
            }

        manager = CollectorManager(db)
        results = manager.collect_all_sources()

        return {
            'statusCode': 200,
            'body': results
        }

    except Exception as e:
        logger.error(f"Collection failed: {e}")
        return {
            'statusCode': 500,
            'body': {'error': str(e)}
        }


