"""
Base agent interface and specialized validator agents.
Each agent checks a deficiency against a specific regulatory domain
and produces a structured response with citations.
"""
import os
import json
from typing import List, Optional
from abc import ABC, abstractmethod

import os
import json
import logging
from typing import List, Optional
from abc import ABC, abstractmethod

from pydantic import BaseModel

from app.models.domain import (
    DeficiencyItem,
    GeneratedResponse,
    Citation,
    ResolutionStatus,
    DeficiencyCategory,
)
from app.services.llm_provider import get_llm_provider

logger = logging.getLogger(__name__)

class BaseValidatorAgent(ABC):
    """Base class for all specialized validator agents."""

    def __init__(self, model: Optional[str] = None):
        self._provider = get_llm_provider()
        if model:
             # Override if specific model requested
             os.environ["LLM_MODEL"] = model
             self._provider = get_llm_provider()

    def _generate(self, prompt: str, on_retry: Optional[Callable] = None) -> str:
        if os.getenv("ENVIRONMENT") == "development":
            logger.debug(f"[{self.agent_name}] PROMPT:\n{prompt}")
        
        content = self._provider.generate_content(
            prompt=prompt,
            system_prompt=self.system_prompt,
            on_retry=on_retry
        )

        if os.getenv("ENVIRONMENT") == "development":
            logger.debug(f"[{self.agent_name}] RESPONSE:\n{content}")
            
        return content

    @property
    @abstractmethod
    def agent_name(self) -> str:
        ...

    @property
    @abstractmethod
    def categories(self) -> List[DeficiencyCategory]:
        """Which deficiency categories this agent handles."""
        ...

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        ...

    def can_handle(self, item: DeficiencyItem) -> bool:
        return item.category in self.categories

    def validate(self, item: DeficiencyItem, retrieved_context: str = "", on_retry: Optional[Callable] = None) -> GeneratedResponse:
        context_block = f"\n**Relevant By-law/Code Context:**\n{retrieved_context}\n" if retrieved_context else ""
        
        prompt = f"""Analyze the following deficiency from an Examiner's Notice and draft a correction response.

**REQUIRED TECHNICAL RIGOR:**
1. **Quantitative Data:** You MUST provide specific numerical evidence (e.g., "Reduced from 48.5m² to 44.2m²"). Qualitative statements like "reduced" or "compliant" without numbers are grounds for rejection.
2. **Technical Matrix:** Every response addressing a measurement must include a small text-based comparison table:
   - Required: [Value]
   - Proposed: [Value]
   - Result: [Pass/Fail/Variance Requested]
3. **Dual-Constraint Check:** Verify if the regulation has a "lesser of" or "greater of" rule. (e.g., Laneway footprint is the lesser of 30% lot area OR 45.0m²). 
4. **Citation Hierarchy:** Always cite the primary governing section (e.g., 150.8.60.1) in addition to the specific subsection.

{context_block}
**Deficiency Text:**
{item.raw_notice_text}

**Extracted Action Required:**
{item.extracted_action}

Respond ONLY with a valid JSON object (no markdown fences) containing:
- "draft_text": The professional, data-driven response text
- "resolution_status": One of RESOLVED, DRAWING_REVISION_NEEDED, VARIANCE_REQUIRED, LDA_REQUIRED, OUT_OF_SCOPE
- "citations": Array of objects with "bylaw", "section", "version" fields
- "variance_magnitude": If variance needed, describe the magnitude (e.g., "0.3m over maximum height"), else null
- "reasoning": Your internal technical logic, specifically noting how you checked for dual-constraints"""

        content = self._generate(prompt, on_retry=on_retry)

        # More robust JSON extraction
        try:
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                content = content[json_start:json_end]
            
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = {
                "draft_text": content,
                "resolution_status": "OUT_OF_SCOPE",
                "citations": [],
                "variance_magnitude": None,
                "reasoning": "Failed to parse structured response from AI",
            }

        citations = [
            Citation(
                bylaw=c.get("bylaw", "Unknown"),
                section=c.get("section", "Unknown"),
                version=c.get("version", "Current"),
            )
            for c in parsed.get("citations", [])
        ]

        return GeneratedResponse(
            deficiency_id=item.id,
            draft_text=parsed.get("draft_text", ""),
            citations=citations,
            resolution_status=ResolutionStatus(parsed.get("resolution_status", "OUT_OF_SCOPE")),
            variance_magnitude=parsed.get("variance_magnitude"),
            agent_reasoning=parsed.get("reasoning", ""),
        )


# ---------------------------------------------------------------------------
# Specialized Agents
# ---------------------------------------------------------------------------

class ZoningValidatorAgent(BaseValidatorAgent):
    agent_name = "Zoning_Validator"
    categories = [DeficiencyCategory.ZONING]
    system_prompt = """You are a senior specialist in Toronto Zoning By-law 569-2013 as it applies to Garden Suites (Section 150.10) and Laneway Suites (Section 150.8).

Your technical review process MUST follow this hierarchy:
1. **Identify Parent Section:** Determine the primary governing section (e.g., 150.8.60.1 for lot coverage).
2. **Scan for Logic Operators:** Explicitly check for "lesser of", "greater of", or "AND" conditions in the by-law text. (CRITICAL: 150.8.60.20 requires the lesser of 30% area OR 45.0m²).
3. **Generate Quantitative Proof:** Calculate the exact proposed area vs. the allowed limit.
4. **Draft Matrix:** Present the final result in a technical matrix format.

Expertise areas:
- Maximum building dimensions (height, depth, width, GFA)
- Setback requirements and permitted encroachments
- Lot coverage and angular plane requirements

When drafting responses, cite exactly: "By-law 569-2013, Section X.Y.Z"."""


class OBCValidatorAgent(BaseValidatorAgent):
    agent_name = "OBC_Validator"
    categories = [DeficiencyCategory.OBC]
    system_prompt = """You are a specialist in the Ontario Building Code (OBC) as applied to ancillary dwelling units in Toronto.

Your expertise includes:
- Part 9 housing requirements
- Structural requirements for detached accessory buildings
- Plumbing and drainage (Part 7)
- HVAC requirements
- Energy efficiency (SB-12)
- Accessibility (barrier-free design where applicable)

When drafting responses, cite OBC sections in the format: "OBC Part X, Section X.Y.Z"
Note any SB-12 supplementary standard references where applicable."""


class FireAccessValidatorAgent(BaseValidatorAgent):
    agent_name = "Fire_Access_Validator"
    categories = [DeficiencyCategory.FIRE_ACCESS]
    system_prompt = """You are a specialist in fire access and life safety for Garden and Laneway Suites in Toronto.

Key requirements:
- Garden Suites: minimum 1.0m unobstructed fire access path
- Laneway Suites: minimum 0.9m unobstructed fire access path
- Fire separation between principal dwelling and suite
- Smoke/CO alarm requirements
- Exit requirements and travel distances

When drafting responses, cite Toronto Fire Services requirements and OBC Part 9 fire safety sections.
Be precise about the specific width requirements for the suite type in question."""


class TreeProtectionAgent(BaseValidatorAgent):
    agent_name = "Tree_Protection_Assessor"
    categories = [DeficiencyCategory.TREE_PROTECTION]

    def __init__(self):
        # Use the cheaper model for simpler rule checks
        super().__init__(model="gemini-2.5-flash")

    system_prompt = """You are a specialist in Toronto's tree protection requirements for construction projects.

Your expertise includes:
- Toronto Municipal Code Chapter 813 (Trees)
- Tree Protection Zone (TPZ) calculations
- Arborist report requirements
- Injury/removal permit requirements for trees with DBH >= 30cm
- Tree planting requirements for new construction

When a tree conflict is identified, recommend either:
1. Design modification to avoid the TPZ
2. Tree preservation plan with arborist supervision
3. Tree injury/removal permit application with replacement planting"""


class LandscapingValidatorAgent(BaseValidatorAgent):
    agent_name = "Landscaping_Validator"
    categories = [DeficiencyCategory.LANDSCAPING]

    def __init__(self):
        super().__init__()

    system_prompt = """You are a specialist in Toronto's landscaping requirements for Garden and Laneway Suites under By-law 569-2013.

Your expertise must strictly enforce these rules:
- Laneway Suites (>6m frontage): At least 85% of the area between the rear main wall of the residence and the front main wall of the laneway suite MUST be soft landscaping (excluding a permitted walkway up to 1.5m wide).
- Laneway Suites (<=6m frontage): At least 60% of the same area MUST be soft landscaping.
- Garden Suites: At least 50% of the rear yard MUST remain permeable soft landscaping.

When drafting responses, explicitly state the required percentage based on the suite type and lot frontage, cite the applicable By-law 569-2013 section, and calculate whether the proposed soft landscaping meets the requirement."""


class ReviewerAgent(BaseValidatorAgent):
    agent_name = "Logic_Auditor"
    categories = [] # Internal agent, not routed via category

    def __init__(self):
        # We use the Pro model for the auditor to ensure maximum rigor
        super().__init__(model="gemini-3.1-pro-preview")

    system_prompt = """You are a senior Professional Engineer (P.Eng.) acting as a Peer Reviewer for building permit correction responses.

Your task is to audit a draft response for technical rigor and regulatory compliance. You have ZERO TOLERANCE for missing quantitative data or incomplete logic.

**CRITICAL AUDIT CHECKLIST:**
1. **Technical Matrix:** Does the response include a comparison matrix (Required vs Proposed)?
2. **Quantitative Data:** Are there specific numbers (metres, percentages)? "Compliant" or "Reduced" alone is a FAIL.
3. **Dual-Constraint Logic:** Did the drafter check for "lesser of" or "greater of" rules (e.g., 45.0m2 cap)?
4. **Citation Hierarchy:** Are both the general parent section and the specific subsection cited correctly?

Respond ONLY with a JSON object:
{
    "status": "APPROVED" | "REJECT_AND_REVISE",
    "feedback": "Specific technical feedback for the drafter",
    "revised_draft": "The corrected version of the response (if REJECTED)"
}"""

    def audit(self, item: DeficiencyItem, draft_response: str, context: str) -> dict:
        prompt = f"""AUDIT REQUEST:
### Original Deficiency:
{item.raw_notice_text}

### Draft Response to Audit:
{draft_response}

### Regulatory Context:
{context}

Perform your audit and return the JSON result:"""
        
        content = self._generate(prompt)
        
        # Robust JSON extraction
        try:
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                content = content[json_start:json_end]
            return json.loads(content)
        except Exception:
            return {"status": "APPROVED", "feedback": "Audit failed to parse", "revised_draft": draft_response}



# ---------------------------------------------------------------------------
# Agent Registry — lazy factory, no module-level construction
# ---------------------------------------------------------------------------

_AGENT_CLASSES = [
    ZoningValidatorAgent,
    OBCValidatorAgent,
    FireAccessValidatorAgent,
    TreeProtectionAgent,
    LandscapingValidatorAgent,
    ServicingValidatorAgent,
]


def get_agent_for_deficiency(item: DeficiencyItem) -> Optional[BaseValidatorAgent]:
    """Find and instantiate the right specialist agent for a given deficiency."""
    for AgentClass in _AGENT_CLASSES:
        agent = AgentClass()
        if agent.can_handle(item):
            return agent
    return None
