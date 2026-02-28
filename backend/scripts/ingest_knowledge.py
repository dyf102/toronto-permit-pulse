import asyncio
import os
import glob
import fitz  # PyMuPDF
from google import genai
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import sys
from pathlib import Path

# Add backend directory to sys.path to allow imports like 'app.db.database'
backend_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(backend_dir)

from app.db.database import AsyncSessionLocal
from app.models.db_models import KnowledgeChunkDB

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    print("Error: GOOGLE_API_KEY not set.")
    sys.exit(1)

client = genai.Client(api_key=API_KEY)

def chunk_text(text: str, chunk_size=1000, overlap=100):
    """Splits text into chunks with a fixed overlap."""
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        if end >= text_len:
            break
        start = end - overlap
    return chunks

def extract_text_from_file(file_path: str) -> str:
    """Extract text from a file (PDF, TXT, MD)."""
    ext = file_path.lower().split('.')[-1]
    if ext == 'pdf':
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
        return text
    elif ext in ['txt', 'md']:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        return ""

async def generate_embedding(text: str) -> list[float]:
    """Uses Gemini text-embedding model to generate embeddings at 768 dimensions."""
    res = await asyncio.to_thread(
        client.models.embed_content,
        model='gemini-embedding-001',
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=768)
    )
    return res.embeddings[0].values

async def ingest_file(file_path: str, session: AsyncSession):
    """Ingest a single file."""
    print(f"Processing: {file_path}")
    file_name = os.path.basename(file_path)

    # Check if already ingested using an exact match query
    stmt = select(KnowledgeChunkDB).where(KnowledgeChunkDB.file_name == file_name).limit(1)
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        print(f"File {file_name} already ingested. Skipping.")
        return

    text = extract_text_from_file(file_path)
    if not text.strip():
        print(f"Skipping {file_name} because it's empty or unsupported.")
        return

    chunks = chunk_text(text)
    print(f"Generated {len(chunks)} chunks for {file_name}.")

    for idx, chunk_str in enumerate(chunks):
        embedding = await generate_embedding(chunk_str)
        chunk_db = KnowledgeChunkDB(
            file_name=file_name,
            chunk_index=idx,
            content=chunk_str,
            metadata_json={"source": file_name, "chunk": idx},
            embedding=embedding
        )
        session.add(chunk_db)

    await session.commit()
    print(f"Successfully ingested {file_name}.")

async def main():
    data_dir = os.path.join(backend_dir, "data")
    if not os.path.exists(data_dir):
        print(f"Data directory {data_dir} does not exist. Creating it...")
        os.makedirs(data_dir)
        return

    # Find common text/pdf documents
    files = []
    for ext in ("*.pdf", "*.md", "*.txt"):
        files.extend(glob.glob(os.path.join(data_dir, ext)))

    if not files:
        print(f"No files found in {data_dir}.")
        return

    async with AsyncSessionLocal() as session:
        for file in files:
            await ingest_file(file, session)

if __name__ == "__main__":
    asyncio.run(main())
