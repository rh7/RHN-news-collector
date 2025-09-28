#!/usr/bin/env python3
"""Initialize sources in the database"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db_client import DatabaseClient


def setup_sources():
    """Add or update source configurations"""
    db = DatabaseClient()

    sources = [
        {
            'type': 'readwise',
            'name': 'Readwise Reader',
            'enabled': True,
            'config': {
                'api_token': os.environ.get('READWISE_TOKEN'),
                'location': 'feed',
                'max_items': int(os.environ.get('READER_FEED_MAX_ITEMS', '100')),
            }
        },
        {
            'type': 'hackernews',
            'name': 'Hacker News',
            'enabled': True,
            'config': {
                'list': os.environ.get('HN_LIST', 'top'),
                'max_items': int(os.environ.get('HN_MAX_ITEMS', '50'))
            }
        }
    ]

    for source in sources:
        existing = db.table('sources') \
            .select('id') \
            .eq('type', source['type']) \
            .eq('name', source['name']) \
            .execute()

        if getattr(existing, 'data', None):
            db.table('sources') \
                .update(source) \
                .eq('id', existing.data[0]['id']) \
                .execute()
            print(f"Updated: {source['name']}")
        else:
            db.table('sources').insert(source).execute()
            print(f"Added: {source['name']}")


if __name__ == '__main__':
    setup_sources()


