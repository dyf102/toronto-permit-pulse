import fitz  # PyMuPDF
import json
from typing import List
from uuid import UUID

from google import genai
from google.genai import types as genai_types

from app.models.domain import ExaminerNoticeExtractionResult, DeficiencyItem


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
        self, session_id: UUID, pdf_path: str
    ) -> List[DeficiencyItem]:
        """
        Extracts text from PDF and uses Gemini to structure the deficiencies.
        Returns a list of DeficiencyItem objects.
        """
        raw_text = self.extract_text_from_pdf(pdf_path)

        # Build the Pydantic schema hint for the LLM
        schema = ExaminerNoticeExtractionResult.model_json_schema()

        prompt = f"""You are an expert municipal zoning and building code AI agent.
Your task is to parse the raw text of a City of Toronto Examiner's Notice for an architectural permit
and extract every deficiency item listed.

Respond ONLY with a valid JSON object matching this schema (no markdown fences):
{json.dumps(schema, indent=2)}

Categories must be one of: ZONING, OBC, FIRE_ACCESS, TREE_PROTECTION, LANDSCAPING, SERVICING, OTHER

Here is the raw text of the Examiner's Notice:
<examiner_notice>
{raw_text}
</examiner_notice>
"""

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=genai_types.GenerateContentConfig(temperature=0.0),
        )

        content = response.text.strip()

        # Strip accidental markdown fences
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        try:
            parsed_data = json.loads(content)
            result = ExaminerNoticeExtractionResult(**parsed_data)
        except (json.JSONDecodeError, Exception) as e:
            # Return empty list if parsing fails rather than crashing
            return []

        # Inject session_id and ordering
        for idx, item in enumerate(result.items):
            item.session_id = session_id
            item.order_index = idx + 1

        return result.items
