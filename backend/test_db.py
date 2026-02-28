import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.db.database import get_db, AsyncSessionLocal
from app.models.db_models import PermitSessionDB, DeficiencyItemDB
from app.models.domain import SessionStatus, SuiteType, DeficiencyCategory

async def test_insert():
    async with AsyncSessionLocal() as session:
        db_session = PermitSessionDB(
            id=uuid.uuid4(),
            property_address="123 Test St",
            suite_type=SuiteType.GARDEN,
            laneway_abutment_length=None,
            status=SessionStatus.ANALYZING,
        )
        
        db_def = DeficiencyItemDB(
            id=uuid.uuid4(),
            session_id=db_session.id,
            category=DeficiencyCategory.ZONING,
            raw_notice_text="Test def",
            extracted_action="Test action",
            agent_confidence=0.99,
            order_index=0,
        )
        db_session.deficiencies.append(db_def)

        session.add(db_session)
        await session.commit()
        print(f"Inserted PermitSession: {db_session.id} with 1 deficiency")

if __name__ == "__main__":
    asyncio.run(test_insert())
