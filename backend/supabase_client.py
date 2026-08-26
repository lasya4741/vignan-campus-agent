"""Supabase client wrapper and database access layer for VIGNAN campus backend."""

from typing import Any, Dict, List, Optional
from backend.config import settings
from backend.utils.logging import logger

try:
    from supabase import Client, create_client
except ImportError:
    Client = None
    create_client = None


class SupabaseService:
    """Manages Supabase connection and encapsulates table operations."""

    def __init__(self):
        self.client: Optional[Client] = None
        self._initialize()

    def _initialize(self) -> None:
        """Initialize the Supabase client using service role key or anon key."""
        if not create_client:
            logger.warning("Supabase package not installed or unavailable.")
            return

        url = settings.supabase_url
        key = settings.supabase_service_role_key or settings.supabase_anon_key

        if url and key:
            try:
                self.client = create_client(url, key)
                logger.info(f"Supabase client initialized successfully for {url}")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                self.client = None
        else:
            logger.warning("Supabase credentials not fully configured (SUPABASE_URL / KEY).")

    def is_connected(self) -> bool:
        """Check if the Supabase client is initialized."""
        return self.client is not None

    def query_table(
        self,
        table_name: str,
        select_cols: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Generic table query with optional equality filters."""
        if not self.client:
            logger.debug(f"Supabase client not active. Returning empty list for query on '{table_name}'.")
            return []

        try:
            req = self.client.table(table_name).select(select_cols)
            if filters:
                for k, v in filters.items():
                    if v is not None:
                        req = req.eq(k, v)
            response = req.limit(limit).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error querying table '{table_name}': {e}")
            return []

    def insert_record(self, table_name: str, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Insert a single record into a table."""
        if not self.client:
            logger.debug(f"Supabase client not active. Skipping insert into '{table_name}'.")
            return None

        try:
            response = self.client.table(table_name).insert(record).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error inserting record into table '{table_name}': {e}")
            return None

    def upsert_record(self, table_name: str, record: Dict[str, Any], on_conflict: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Upsert a single record into a table."""
        if not self.client:
            logger.debug(f"Supabase client not active. Skipping upsert into '{table_name}'.")
            return None

        try:
            req = self.client.table(table_name)
            if on_conflict:
                response = req.upsert(record, on_conflict=on_conflict).execute()
            else:
                response = req.upsert(record).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error upserting record into table '{table_name}': {e}")
            return None

    def update_record(self, table_name: str, filters: Dict[str, Any], update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update records in a table matching filter."""
        if not self.client:
            logger.debug(f"Supabase client not active. Skipping update into '{table_name}'.")
            return None

        try:
            req = self.client.table(table_name).update(update_data)
            for k, v in filters.items():
                req = req.eq(k, v)
            response = req.execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating record in table '{table_name}': {e}")
            return None


# Global singleton instance
db = SupabaseService()
