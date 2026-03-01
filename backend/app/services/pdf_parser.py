import fitz  # PyMuPDF
import json
import uuid
import os
import logging
from io import BytesIO
from typing import List, Optional, Callable
from uuid import UUID, uuid4

from app.models.domain import DeficiencyCategory, DeficiencyItem
from app.services.llm_provider import get_llm_provider

logger = logging.getLogger(__name__)

class ExaminerNoticeParserService:
    def __init__(self, api_key: Optional[str] = None):
        self.provider = get_llm_provider()

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extracts raw text from an Examiner's Notice PDF using PyMuPDF."""
        doc = fitz.open(pdf_path)
        full_text = []
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            full_text.append(text)
        doc.close()
        return "\n".join(full_text)

    def parse_examiner_notice(
        self, session_id: UUID, pdf_path: str, on_retry: Optional[Callable] = None
    ) -> List[DeficiencyItem]:
        """
        Extracts text from PDF and uses LLM to structure the deficiencies.
        """
        raw_text = self.extract_text_from_pdf(pdf_path)
        
        system_prompt = "You are an expert at parsing City of Toronto Building Examiner's Notices."
        prompt = f"""Extract every deficiency item from the notice text below.

Return a JSON array of deficiency items. Each item must have:
- "category": one of exactly: ZONING, OBC, FIRE_ACCESS, TREE_PROTECTION, LANDSCAPING, SERVICING, OTHER
- "raw_notice_text": the full original text of the deficiency as written in the notice
- "extracted_action": a concise 1-2 sentence summary of what the applicant must do to resolve it

Rules:
- Return ONLY the JSON array, no markdown, no code fences, no explanation
- Map section letters to categories: A/Zoning→ZONING, B/OBC/Building Code→OBC, C/Tree→TREE_PROTECTION, D/Fire→FIRE_ACCESS, E/Landscape→LANDSCAPING, F/Servicing→SERVICING

Here is the Examiner's Notice text:
<notice>
{raw_text}
</notice>

Return only the JSON array:"""

        if os.getenv("ENVIRONMENT") == "development":
            logger.debug(f"[parser] PROMPT:\n{prompt[:1000]}...")

        content = self.provider.generate_content(
            prompt=prompt,
            system_prompt=system_prompt,
            on_retry=on_retry
        )

        if os.getenv("ENVIRONMENT") == "development":
            logger.debug(f"[parser] RESPONSE:\n{content[:1000]}...")

        # Strip any accidental markdown fences
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        # Sometimes the model wraps in an object, unwrap it
        if content.startswith("{"):
            try:
                obj = json.loads(content)
                if "items" in obj:
                    content = json.dumps(obj["items"])
            except Exception:
                pass

        try:
            items_data = json.loads(content)
            if not isinstance(items_data, list):
                items_data = []
        except json.JSONDecodeError:
            print(f"[parser] JSON decode failed. Raw response:\n{content[:500]}")
            return []

        result = []
        for idx, item in enumerate(items_data):
            try:
                cat_str = item.get("category", "OTHER").upper()
                try:
                    category = DeficiencyCategory(cat_str)
                except ValueError:
                    category = DeficiencyCategory.OTHER

                deficiency = DeficiencyItem(
                    session_id=session_id,
                    category=category,
                    raw_notice_text=item.get("raw_notice_text", ""),
                    extracted_action=item.get("extracted_action", ""),
                    order_index=idx + 1,
                )
                result.append(deficiency)
            except Exception as e:
                print(f"[parser] Skipping item {idx}: {e}")
                continue

        print(f"[parser] Extracted {len(result)} deficiencies from notice")
        return result
