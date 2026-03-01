import json
import logging
import hashlib
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)

class CacheService:
    @staticmethod
    def _generate_key(prefix: str, content: str) -> str:
        """Generates a stable cache key from content."""
        h = hashlib.sha256(content.encode()).hexdigest()
        return f"{prefix}:{h}"

    @classmethod
    async def get(cls, db: AsyncSession, prefix: str, content: str) -> Optional[Any]:
        """Retrieves a cached value if it exists."""
        key = cls._generate_key(prefix, content)
        try:
            # We'll use a simple KV table if it exists, otherwise return None
            # For simplicity, we can use the knowledge_chunks table or a dedicated one
            # Let's assume a dedicated 'cache' table exists or will be created
            query = text("SELECT value FROM cache WHERE key = :key")
            result = await db.execute(query, {"key": key})
            row = result.fetchone()
            if row:
                logger.debug(f"Cache hit for key: {key}")
                return json.loads(row[0])
        except Exception as e:
            logger.debug(f"Cache miss or table missing: {e}")
        return None

    @classmethod
    async def set(cls, db: AsyncSession, prefix: str, content: str, value: Any):
        """Sets a cached value."""
        key = cls._generate_key(prefix, content)
        try:
            # Create cache table if not exists (ideally done in migrations)
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            query = text("""
                INSERT INTO cache (key, value) 
                VALUES (:key, :value)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
            """)
            await db.execute(query, {"key": key, "value": json.dumps(value)})
            await db.commit()
            logger.debug(f"Cached value for key: {key}")
        except Exception as e:
            logger.error(f"Failed to set cache: {e}")
