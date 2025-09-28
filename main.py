#!/usr/bin/env python3
import logging
import sys
from datetime import datetime
from core.db_client import DatabaseClient
from core.collector_manager import CollectorManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main collection process"""
    logger.info(f"Starting collection run at {datetime.utcnow()}")

    try:
        db = DatabaseClient()

        if not db.test_connection():
            logger.error("Failed to connect to database")
            return 1

        manager = CollectorManager(db)
        results = manager.collect_all_sources()

        logger.info(f"Collection completed: {results}")

        if results.get('errors'):
            logger.warning(f"Some sources failed: {results['errors']}")
            return 1

        return 0

    except Exception as e:
        logger.error(f"Collection failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())


