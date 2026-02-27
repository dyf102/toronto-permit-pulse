"""
Base agent interface and specialized validator agents.
Each agent checks a deficiency against a specific regulatory domain
and produces a structured response with citations.
"""
import os
from typing import List, Optional
from abc import ABC, abstractmethod

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel

from app.models.domain import (
    DeficiencyItem,
    GeneratedResponse,
    Citation,
    ResolutionStatus,
    DeficiencyCategory,
)


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")


class AgentResult(BaseModel):
    """Structured output from a validator agent."""
    draft_text: str
    resolution_status: str
    citations: List[dict] = []
    variance_magnitude: Optional[str] = None
    reasoning: str


class BaseValidatorAgent(ABC):
    """Base class for all specialized validator agents."""

    def __init__(self, model: str = "gemini-2.5-flash"):
        self._model = model
        self._llm = None

    @property
    def llm(self):
        """Lazy initialization — only create client when needed."""
        if self._llm is None:
            api_key = os.getenv("GOOGLE_API_KEY", "")
            if not api_key:
                raise RuntimeError("GOOGLE_API_KEY not set")
            self._llm = ChatGoogleGenerativeAI(
                model=self._model,
                google_api_key=api_key,
                temperature=0.1,
            )
        return self._llm

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

    def validate(self, item: DeficiencyItem) -> GeneratedResponse:
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", """Analyze the following deficiency from an Examiner's Notice and draft a correction response.

**Deficiency Text:**
{raw_notice_text}

**Extracted Action Required:**
{extracted_action}

Respond with a JSON object containing:
- "draft_text": The professional response text to submit to the City
- "resolution_status": One of RESOLVED, DRAWING_REVISION_NEEDED, VARIANCE_REQUIRED, LDA_REQUIRED, OUT_OF_SCOPE
- "citations": Array of objects with "bylaw", "section", "version" fields
- "variance_magnitude": If variance needed, describe the magnitude (e.g., "0.3m over maximum height")
- "reasoning": Your internal reasoning for this response
"""),
        ])

        chain = prompt | self.llm
        result = chain.invoke({
            "raw_notice_text": item.raw_notice_text,
            "extracted_action": item.extracted_action,
        })

        # Parse the LLM response into structured output
        import json
        try:
            content = result.content
            # Extract JSON from potential markdown code block
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            parsed = json.loads(content.strip())
        except (json.JSONDecodeError, IndexError):
            parsed = {
                "draft_text": str(result.content),
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
    system_prompt = """You are a specialist in Toronto Zoning By-law 569-2013 as it applies to Garden Suites (Section 150.10) and Laneway Suites (Section 150.8).

Your expertise includes:
- Maximum building dimensions (height, depth, width, GFA)
- Setback requirements from lot lines and existing buildings
- Lot coverage calculations
- Angular plane requirements
- Permitted projections and encroachments

When drafting responses, always cite the specific by-law section and subsection number.
Use the format: "By-law 569-2013, Section X.Y.Z"

If the deficiency requires a minor variance, calculate the magnitude and recommend Committee of Adjustment application."""


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
        super().__init__(model="gemini-2.5-flash")

    system_prompt = """You are a specialist in Toronto's landscaping requirements for Garden and Laneway Suites.

Your expertise includes:
- Soft landscaping minimum percentages
- Permeable surface requirements
- Grading and drainage requirements
- Fencing and screening requirements

When drafting responses, cite By-law 569-2013 landscaping provisions and any applicable site plan requirements."""


class ServicingValidatorAgent(BaseValidatorAgent):
    agent_name = "Servicing_Validator"
    categories = [DeficiencyCategory.SERVICING]
    system_prompt = """You are a specialist in municipal servicing requirements for Garden and Laneway Suites in Toronto.

Your expertise includes:
- Water and sewer connection requirements
- Toronto Water connection permits
- Stormwater management
- Grading and drainage to municipal standards
- Utility easements and right-of-way requirements

When drafting responses, cite relevant Toronto Water and Engineering standards."""


# ---------------------------------------------------------------------------
# Agent Registry
# ---------------------------------------------------------------------------

ALL_AGENTS: List[BaseValidatorAgent] = [
    ZoningValidatorAgent(),
    OBCValidatorAgent(),
    FireAccessValidatorAgent(),
    TreeProtectionAgent(),
    LandscapingValidatorAgent(),
    ServicingValidatorAgent(),
]


def get_agent_for_deficiency(item: DeficiencyItem) -> Optional[BaseValidatorAgent]:
    """Find the right specialist agent for a given deficiency."""
    for agent in ALL_AGENTS:
        if agent.can_handle(item):
            return agent
    return None
