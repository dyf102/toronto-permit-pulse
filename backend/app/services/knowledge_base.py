import asyncio
import os
import logging
from google import genai
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.db_models import KnowledgeChunkDB

logger = logging.getLogger(__name__)

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
        Retrieves the top_k most similar knowledge chunks and their parent sections.
        """
        query_embedding = await self.get_embedding(query)
        
        # 1. Get initial relevant chunks
        stmt = (
            select(KnowledgeChunkDB)
            .order_by(KnowledgeChunkDB.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )
        
        results = await db.execute(stmt)
        initial_chunks = results.scalars().all()
        
        all_chunks = {chunk.id: chunk for chunk in initial_chunks}
        parent_sections_needed = set()
        
        # 2. Identify parent sections from metadata
        for chunk in initial_chunks:
            if chunk.metadata_json:
                section = chunk.metadata_json.get("section")
                if section:
                    # Parent section is usually the first 2 segments (e.g., 150.8)
                    parts = section.split('.')
                    if len(parts) > 2:
                        parent_id = '.'.join(parts[:2])
                        parent_sections_needed.add(parent_id)
                    # Also include the "General" section for that chapter
                    parent_sections_needed.add('.'.join(parts[:1]) + ".10") # e.g., 150.10

        # 3. Fetch parent/contextual chunks
        if parent_sections_needed:
            # Look for chunks where metadata->'section' starts with or equals the parent_id
            # This is a bit simplified; in production, we'd use a JSONB query
            parent_stmt = select(KnowledgeChunkDB).where(
                KnowledgeChunkDB.file_name == initial_chunks[0].file_name # Same file context
            )
            parent_results = await db.execute(parent_stmt)
            all_file_chunks = parent_results.scalars().all()
            
            for chunk in all_file_chunks:
                if chunk.metadata_json:
                    sec = chunk.metadata_json.get("section", "")
                    if sec in parent_sections_needed or any(sec.startswith(p) for p in parent_sections_needed):
                        all_chunks[chunk.id] = chunk

        # Return sorted list of unique content (keeping original order + parents)
        sorted_chunks = sorted(all_chunks.values(), key=lambda x: (x.file_name, x.chunk_index))
        return [chunk.content for chunk in sorted_chunks]
