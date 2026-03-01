import os
import json
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

# Ensure we load environment variables
load_dotenv()

# We default to gemini if not specified
provider = os.getenv("LLM_PROVIDER", "gemini").lower()
model = os.getenv("LLM_MODEL", "gemini-3.1-pro-preview") # Use Gemini 3.1 Pro for high-quality grading

from app.services.llm_provider import get_llm_provider

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class EvalPipeline:
    def __init__(self):
        self.provider = get_llm_provider()
        
    def evaluate_response(self, original_deficiency: str, generated_response: Dict[str, Any], gold_standard_citations: List[str]) -> Dict[str, Any]:
        """
        Evaluates a generated response against the original deficiency and a gold standard.
        """
        system_prompt = """You are a senior Professional Engineer (P.Eng.) with over 10 years of experience specializing in City of Toronto building permit reviews, specifically for Garden Suites and Laneway Suites. 

You have deep technical knowledge of:
- Toronto Zoning By-law 569-2013 (Section 150.7 and 150.8)
- Ontario Building Code (OBC) Part 9 and Part 7 (Plumbing)
- Toronto Fire Services access requirements
- Toronto Municipal Code Chapter 813 (Trees)

Your job is to rigorously evaluate an AI-generated correction response. You do not accept "almost correct" answers. A wrong citation or a missing technical detail can cause a 3-month delay for a homeowner. Grading must be strict, technical, and professional.

You must grade the response on three criteria:
1. Citation Accuracy (Score 0-10): Did the response cite the exact By-law or OBC section required? Deduct points for missing subsections or fabricated numbers.
2. Completeness (Score 0-10): Did the response fully address the examiner's deficiency with technical precision (e.g., providing calculated percentages or referring to specific drawing changes)?
3. Professional Tone (Score 0-10): Is the response formatted professionally, with the authoritative tone of a BCIN-qualified designer or Architect?

Return your evaluation strictly as a JSON object:
{
    "citation_accuracy": <int>,
    "completeness": <int>,
    "professional_tone": <int>,
    "overall_pass": <boolean>, // True ONLY if all scores >= 9 (We have zero tolerance for regulatory errors)
    "feedback": "<string explaining specific technical deductions based on Toronto regulations>"
}"""

        prompt = f"""
### Original Examiner Deficiency:
{original_deficiency}

### Expected Gold Standard Citations:
{', '.join(gold_standard_citations)}

### AI Generated Response to Evaluate:
Draft Text: {generated_response.get('draft_text')}
Resolution Status: {generated_response.get('resolution_status')}
Citations Provided: {json.dumps(generated_response.get('citations'))}
Reasoning: {generated_response.get('agent_reasoning')}

Evaluate the response and return the JSON object:"""

        logger.info(f"Evaluating response for deficiency: {original_deficiency[:50]}...")
        
        try:
            content = self.provider.generate_content(prompt=prompt, system_prompt=system_prompt)

            # More robust JSON extraction
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                content = content[json_start:json_end]

            result = json.loads(content)
            logger.info(f"Evaluation complete. Pass: {result.get('overall_pass')}")
            return result
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return {
                "citation_accuracy": 0,
                "completeness": 0,
                "professional_tone": 0,
                "overall_pass": False,
                "feedback": f"Evaluation script error: {str(e)}"
            }

def run_sample_evals():
    """Run a basic sanity check on the eval pipeline using a mock gold standard."""
    import time
    print("Waiting 40 seconds to clear Gemini Pro rate limits...")
    time.sleep(40)

    evaluator = EvalPipeline()

    # Mock data representing a typical Laneway Suite FSI/Coverage deficiency
    mock_deficiency = "Laneway suite exceeds maximum permitted lot coverage. Provide revised site plan showing compliance."
    mock_gold_citations = ["By-law 569-2013, Section 150.8.60.1", "By-law 569-2013, Section 150.8.60.20"]

    # A "Good" mock response
    mock_good_response = {
        "draft_text": "The site plan has been revised to reduce the laneway suite footprint, ensuring it does not exceed the maximum 30% lot coverage requirement.",
        "resolution_status": "DRAWING_REVISION_NEEDED",
        "citations": [{"bylaw": "569-2013", "section": "150.8.60.20", "version": "Current"}],
        "agent_reasoning": "Identified coverage issue and requested drawing revision."
    }

    # A "Bad" mock response (hallucinated citation)
    mock_bad_response = {
        "draft_text": "The lot coverage is fine.",
        "resolution_status": "RESOLVED",
        "citations": [{"bylaw": "Fake-Bylaw", "section": "999.1", "version": "Old"}],
        "agent_reasoning": "I think it's okay."
    }

    print("--- Running Evaluation on GOOD Response ---")
    good_result = evaluator.evaluate_response(mock_deficiency, mock_good_response, mock_gold_citations)
    print(json.dumps(good_result, indent=2))

    print("\nWaiting 20 seconds before next evaluation...")
    time.sleep(20)

    print("\n--- Running Evaluation on BAD Response ---")
    bad_result = evaluator.evaluate_response(mock_deficiency, mock_bad_response, mock_gold_citations)
    print(json.dumps(bad_result, indent=2))

if __name__ == "__main__":
    run_sample_evals()
