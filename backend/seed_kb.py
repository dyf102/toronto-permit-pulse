import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from app.services.knowledge_base import KnowledgeBaseService
from app.models.db_models import KnowledgeChunkDB
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/permit_db")

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

API_KEY = os.getenv("GOOGLE_API_KEY", "")
kb_service = KnowledgeBaseService(api_key=API_KEY) if API_KEY else None

TORONTO_BYLAWS = [
    {
        "category": "ZONING",
        "subcategory": "Maximum Building Height",
        "content": "For an ancillary building containing a laneway suite, the maximum permitted building height is:\n(A) 4.0 metres, if the laneway suite is located less than 3.0 metres from the residential building on the lot;\n(B) 6.0 metres, if the laneway suite is located 3.0 metres to 5.0 metres from the residential building on the lot; and\n(C) 6.3 metres, if the laneway suite is located more than 5.0 metres from the residential building on the lot."
    },
    {
        "category": "ZONING",
        "subcategory": "Rear Yard Setback",
        "content": "An ancillary building containing a laneway suite must be set back from a rear lot line abutting a street or a lane 1.5 metres."
    },
    {
        "category": "ZONING",
        "subcategory": "Laneway Abutment Length",
        "content": "A lot may have an ancillary building containing a laneway suite if it has a rear lot line or side lot line abutting a lane for at least 3.5 metres."
    },
    {
        "category": "OBC",
        "subcategory": "Spatial Separation",
        "content": "Ontario Building Code 3.2.3.1: The percentage of unprotected openings in an exposing building face shall be determined in conformance with Table 3.2.3.1.B or 3.2.3.1.C for the limiting distance and the area of the exposing building face."
    },
    {
        "category": "FIRE_ACCESS",
        "subcategory": "Distance to Hydrant",
        "content": "Fire access route must provide uninterrupted access from the principle street face of the dwelling unit to the entry of the laneway or garden suite. For any new unit lacking lane access, the principal path of travel must be a minimum 0.9m width without overhanging obstructions lower than 2.1m."
    },
    {
        "category": "TREE_PROTECTION",
        "subcategory": "Private Tree By-law",
        "content": "City of Toronto Municipal Code Chapter 813, Article III requires a permit to injure or destroy any tree having a diameter of 30 cm or more, measured at 1.4 metres above ground level. Tree protection zones must be enforced with solid hoarding prior to any development."
    },
    {
        "category": "LANDSCAPING",
        "subcategory": "Soft Landscaping",
        "content": "If the lot area is greater than 100 square metres, a minimum of 85% of the rear yard area not covered by the ancillary building must be maintained as soft landscaping."
    }
]

async def seed_db():
    async with AsyncSessionLocal() as session:
        # Check if table has data
        result = await session.execute(text("SELECT COUNT(*) FROM knowledge_chunks"))
        count = result.scalar()
        if count > 0:
            print("Knowledge base already seeded. Exiting.")
            return

        print("Seeding Knowledge Base with Toronto By-Laws...")
        for i, b in enumerate(TORONTO_BYLAWS):
            print(f"Embedding {b['category']} - {b['subcategory']} ...")
            if kb_service:
                vector = await kb_service.get_embedding(b['content'])
            else:
                vector = [0.0] * 768
                
            chunk = KnowledgeChunkDB(
                file_name="toronto_city_bylaws.txt",
                chunk_index=i,
                content=b['content'],
                metadata_json={"category": b['category'], "subcategory": b['subcategory']},
                embedding=vector
            )
            session.add(chunk)
        
        await session.commit()
        print("Knowledge base seed complete.")

if __name__ == "__main__":
    asyncio.run(seed_db())
