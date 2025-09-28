#!/usr/bin/env python3
import argparse
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collectors.readwise import ReadwiseCollector


def main():
    parser = argparse.ArgumentParser(description='Test a collector')
    parser.add_argument('--source', choices=['readwise'], required=True)
    args = parser.parse_args()

    if args.source == 'readwise':
        source_config = {
            'id': 'test-source-id',
            'name': 'Readwise Reader',
            'config': { 'api_token': os.environ.get('READWISE_TOKEN'), 'location': 'archive' },
            'sync_metadata': {}
        }
        collector = ReadwiseCollector(source_config)
        ok = collector.test_connection()
        print(f"Connection OK: {ok}")
        articles, sync = collector.collect()
        print(f"Collected: {len(articles)} articles; sync: {sync}")


if __name__ == '__main__':
    main()


