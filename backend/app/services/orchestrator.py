"""
Orchestrator that coordinates the full pipeline:
  Parse → Route → Validate → Draft → Package
"""
from typing import List, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import os
import asyncio

from app.models.domain import (
    DeficiencyItem,
    GeneratedResponse,
    PermitSession,
    SessionStatus,
    DeficiencyCategory,
)
from app.services.agents import get_agent_for_deficiency, BaseValidatorAgent
from app.services.knowledge_base import KnowledgeBaseService


class OrchestratorService:
    """
    Coordinates the full permit correction response pipeline.
    Takes parsed deficiencies and routes them to specialized agents.
    """

    async def process_deficiencies(
        self, session: PermitSession, items: List[DeficiencyItem], db: AsyncSession
    ) -> Dict:
        """
        Process all deficiency items through the agent pipeline asynchronously.
        Returns structured results grouped by category.
        """
        results: List[Dict] = []
        unhandled: List[Dict] = []
        
        api_key = os.getenv("GOOGLE_API_KEY", "")
        kb_service = KnowledgeBaseService(api_key) if api_key else None
        
        loop = asyncio.get_event_loop()

        for item in items:
            agent = get_agent_for_deficiency(item)
            if agent:
                try:
                    # Retrieve relevant context from Knowledge Base
                    context_text = ""
                    if kb_service:
                        query = f"{item.raw_notice_text} {item.extracted_action}"
                        chunks = await kb_service.search_context(query, db, top_k=2)
                        context_text = "\n\n".join(chunks)

                    # Agent validation runs synchronously, so dispatch to thread
                    response = await loop.run_in_executor(
                        None, agent.validate, item, context_text
                    )
                    
                    # Audit step: Ensure technical rigor
                    from app.services.agents import ReviewerAgent
                    auditor = ReviewerAgent()
                    audit_result = await loop.run_in_executor(
                        None, auditor.audit, item, response.draft_text, context_text
                    )
                    
                    if audit_result.get("status") == "REJECT_AND_REVISE" and audit_result.get("revised_draft"):
                        response.draft_text = audit_result["revised_draft"]
                        response.reasoning = f"{response.reasoning}\n\n[AUDIT FEEDBACK]: {audit_result.get('feedback')}"

                    results.append({
                        "deficiency": item.dict(),
                        "response": response.dict(),
                        "agent": agent.agent_name,
                    })
                except Exception as e:
                    results.append({
                        "deficiency": item.dict(),
                        "response": None,
                        "agent": agent.agent_name,
                        "error": str(e),
                    })
            else:
                unhandled.append({
                    "deficiency": item.dict(),
                    "reason": f"No agent registered for category: {item.category}",
                })

        # Summary statistics
        summary = {
            "total_deficiencies": len(items),
            "processed": len(results),
            "unhandled": len(unhandled),
            "by_category": {},
        }

        for item in items:
            cat = item.category.value
            summary["by_category"][cat] = summary["by_category"].get(cat, 0) + 1

        return {
            "session_id": str(session.id),
            "suite_type": session.suite_type.value,
            "property_address": session.property_address,
            "summary": summary,
            "results": results,
            "unhandled": unhandled,
        }
