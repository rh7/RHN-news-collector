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


