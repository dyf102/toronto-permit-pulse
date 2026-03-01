import asyncio
import os
from google import genai
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.db_models import KnowledgeChunkDB

class KnowledgeBaseService:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY", "")
        self.client = genai.Client(api_key=api_key) if api_key else None

    async def get_embedding(self, text: str) -> list[float]:
        res = await asyncio.to_thread(
            self.client.models.embed_content,
            model='gemini-embedding-001',
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=768)
        )
        return res.embeddings[0].values

    async def search_context(self, query: str, db: AsyncSession, top_k: int = 3) -> list[str]:
        """
        Retrieves the top_k most similar knowledge chunks for the given query.
        Returns a list of chunk contents.
        """
        query_embedding = await self.get_embedding(query)
        
        # pgvector uses cosine distance '<=>' for the vector Type
        # Lower distance means higher similarity
        stmt = (
            select(KnowledgeChunkDB)
            .order_by(KnowledgeChunkDB.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )
        
        results = await db.execute(stmt)
        chunks = results.scalars().all()
        return [chunk.content for chunk in chunks]
