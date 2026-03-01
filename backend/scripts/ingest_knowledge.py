import asyncio
import os
import re
import glob
import fitz  # PyMuPDF
from google import genai
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

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

def chunk_by_section(text: str):
    """
    Splits text into chunks based on markdown headers (##, ###).
    Returns a list of dictionaries with content and metadata.
    """
    # Regex to find section headers like ## 150.8.20 Setbacks
    # or ### (1) Definition
    lines = text.split('\n')
    chunks = []
    current_section = "General"
    current_subsection = ""
    current_content = []
    
    section_pattern = re.compile(r'^##\s+([\d\.]+)\s+(.*)')
    subsection_pattern = re.compile(r'^###\s+\(([\d\w]+)\)\s+(.*)')

    for line in lines:
        section_match = section_pattern.match(line)
        subsection_match = subsection_pattern.match(line)
        
        if section_match:
            # Save previous chunk
            if current_content:
                chunks.append({
                    "content": '\n'.join(current_content).strip(),
                    "section": current_section,
                    "subsection": current_subsection
                })
            current_section = section_match.group(1)
            current_subsection = ""
            current_content = [line]
        elif subsection_match:
            # Save previous chunk if it has content beyond the header
            if current_content:
                chunks.append({
                    "content": '\n'.join(current_content).strip(),
                    "section": current_section,
                    "subsection": current_subsection
                })
            current_subsection = subsection_match.group(1)
            current_content = [line]
        else:
            current_content.append(line)
            
    # Add final chunk
    if current_content:
        chunks.append({
            "content": '\n'.join(current_content).strip(),
            "section": current_section,
            "subsection": current_subsection
        })
        
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
    """Ingest a single file using section-aware chunking."""
    print(f"Processing: {file_path}")
    file_name = os.path.basename(file_path)

    # For development, we delete existing chunks for this file to allow re-ingestion with new logic
    stmt_del = delete(KnowledgeChunkDB).where(KnowledgeChunkDB.file_name == file_name)
    await session.execute(stmt_del)

    text = extract_text_from_file(file_path)
    if not text.strip():
        print(f"Skipping {file_name} because it's empty or unsupported.")
        return

    chunks = chunk_by_section(text)
    print(f"Generated {len(chunks)} section-based chunks for {file_name}.")

    for idx, chunk_data in enumerate(chunks):
        content = chunk_data["content"]
        if not content.strip(): continue
        
        embedding = await generate_embedding(content)
        chunk_db = KnowledgeChunkDB(
            file_name=file_name,
            chunk_index=idx,
            content=content,
            metadata_json={
                "source": file_name, 
                "section": chunk_data["section"],
                "subsection": chunk_data["subsection"]
            },
            embedding=embedding
        )
        session.add(chunk_db)

    await session.commit()
    print(f"Successfully ingested {file_name} with section metadata.")

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
