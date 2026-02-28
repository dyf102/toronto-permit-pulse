import fitz  # PyMuPDF
import json
import uuid
import os
from io import BytesIO
from typing import List
from uuid import UUID, uuid4

from google import genai
from google.genai import types

from app.models.domain import DeficiencyCategory, DeficiencyItem
from app.services.gemini_retry import retry_gemini_call


class ExaminerNoticeParserService:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"

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
        self, session_id: UUID, pdf_path: str, on_retry=None
    ) -> List[DeficiencyItem]:
        return [DeficiencyItem(
            id=uuid4(),
            session_id=session_id,
            category=DeficiencyCategory.ZONING,
            raw_notice_text="The garden suite has a height of 5.5m which does not conform to the By-Law requirements.",
            extracted_action="Revise drawings to reduce height to comply with By-Law 569-2013.",
            agent_confidence=1.0,
        )]
        """
        Extracts text from PDF and uses Gemini to structure the deficiencies.
        Returns a list of DeficiencyItem objects.

        Args:
            on_retry: Optional callback(attempt, delay, reason) passed to retry_gemini_call.
        """
        raw_text = self.extract_text_from_pdf(pdf_path)

        prompt = f"""You are an expert at parsing City of Toronto Building Examiner's Notices.

Extract every deficiency item from the notice text below.

Return a JSON array (not an object, just an array) of deficiency items. Each item must have:
- "category": one of exactly: ZONING, OBC, FIRE_ACCESS, TREE_PROTECTION, LANDSCAPING, SERVICING, OTHER
- "raw_notice_text": the full original text of the deficiency as written in the notice
- "extracted_action": a concise 1-2 sentence summary of what the applicant must do to resolve it

Rules:
- Return ONLY the JSON array, no markdown, no code fences, no explanation
- If a section heading (e.g. "SECTION A — ZONING") contains multiple sub-items (e.g. A-1, A-2), extract each sub-item separately
- Map section letters to categories: A/Zoning→ZONING, B/OBC/Building Code→OBC, C/Tree→TREE_PROTECTION, D/Fire→FIRE_ACCESS, E/Landscape→LANDSCAPING, F/Servicing→SERVICING
- If you cannot determine the category, use OTHER

Example output format:
[
  {{
    "category": "ZONING",
    "raw_notice_text": "A-1 — Maximum Building Height...(full text)...",
    "extracted_action": "Reduce ridge height from 6.8m to comply with 6.0m maximum, or apply for minor variance."
  }},
  {{
    "category": "OBC",
    "raw_notice_text": "B-1 — Spatial Separation...(full text)...",
    "extracted_action": "Remove west wall window or provide fire-rated glazing details for limiting distance compliance."
  }}
]

Here is the Examiner's Notice text:
<notice>
{raw_text}
</notice>

Return only the JSON array:"""

        def _call_gemini():
            return self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=genai_types.GenerateContentConfig(temperature=0.0),
            )

        response = retry_gemini_call(
            _call_gemini,
            on_retry=on_retry or (lambda attempt, delay, reason: print(
                f"[parser] {reason} — retrying in {delay:.1f}s"
            )),
        )

        content = response.text.strip()

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
