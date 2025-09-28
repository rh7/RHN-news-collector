from supabase import create_client, Client
import os
from typing import Optional


class DatabaseClient:
    """Wrapper for Supabase client"""

    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        self.url = url or os.environ.get('SUPABASE_URL')
        self.key = key or os.environ.get('SUPABASE_SERVICE_KEY')

        if not self.url or not self.key:
            raise ValueError("Supabase URL and key must be provided")

        self.client: Client = create_client(self.url, self.key)

    def table(self, table_name: str):
        """Access a table"""
        return self.client.table(table_name)

    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            self.table('sources').select('id').limit(1).execute()
            return True
        except Exception:
            return False


