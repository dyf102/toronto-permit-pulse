import fitz  # PyMuPDF
from typing import List
from uuid import UUID
import json

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from app.models.domain import ExaminerNoticeExtractionResult, DeficiencyItem

class ExaminerNoticeParserService:
    def __init__(self, api_key: str):
        # We model the text parsing using Gemini 2.5 Pro equivalent
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro", # Adapting to Gemini series
            google_api_key=api_key,
            temperature=0.0
        )
        self.parser = PydanticOutputParser(pydantic_object=ExaminerNoticeExtractionResult)

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extracts raw text from an Examiner's Notice PDF.
        """
        doc = fitz.open(pdf_path)
        full_text = []
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            full_text.append(text)
            
        doc.close()
        return "\n".join(full_text)

    def parse_examiner_notice(self, session_id: UUID, pdf_path: str) -> List[DeficiencyItem]:
        """
        Extracts text from PDF and uses Gemini to structure the deficiencies.
        """
        raw_text = self.extract_text_from_pdf(pdf_path)

        prompt = PromptTemplate(
            template="""You are an expert municipal zoning and building code AI agent.
Your task is to parse the raw text of a City of Toronto Examiner's Notice for an architectural permit and extract every deficiency item listed.

{format_instructions}

Here is the raw text of the Examiner's Notice:
<examiner_notice>
{raw_text}
</examiner_notice>
""",
            input_variables=["raw_text"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )

        chain = prompt | self.llm | self.parser
        
        # Note: In production we use actual session_id to propagate the ID to the items
        result: ExaminerNoticeExtractionResult = chain.invoke({"raw_text": raw_text})
        
        # Inject the session_id into the extracted items since the LLM won't know it
        for idx, item in enumerate(result.items):
            item.session_id = session_id
            item.order_index = idx + 1
            
        return result.items
