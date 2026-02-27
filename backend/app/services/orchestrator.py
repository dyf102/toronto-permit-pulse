"""
Orchestrator that coordinates the full pipeline:
  Parse → Route → Validate → Draft → Package
"""
from typing import List, Dict
from uuid import UUID

from app.models.domain import (
    DeficiencyItem,
    GeneratedResponse,
    PermitSession,
    SessionStatus,
    DeficiencyCategory,
)
from app.services.agents import get_agent_for_deficiency, BaseValidatorAgent


class OrchestratorService:
    """
    Coordinates the full permit correction response pipeline.
    Takes parsed deficiencies and routes them to specialized agents.
    """

    def process_deficiencies(
        self, session: PermitSession, items: List[DeficiencyItem]
    ) -> Dict:
        """
        Process all deficiency items through the agent pipeline.
        Returns structured results grouped by category.
        """
        results: List[Dict] = []
        unhandled: List[Dict] = []

        for item in items:
            agent = get_agent_for_deficiency(item)
            if agent:
                try:
                    response = agent.validate(item)
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
