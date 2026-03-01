import os
import json
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

# Ensure we load environment variables
load_dotenv()

# Set provider to gemini and model to gemini-3-flash-preview
os.environ["LLM_PROVIDER"] = "gemini"
os.environ["LLM_MODEL"] = "gemini-3-flash-preview"

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

    # A "P.Eng. Optimized" response (matches the new technical rigor requirements)
    mock_peng_response = {
        "draft_text": """The site plan has been revised to reduce the laneway suite footprint to comply with the maximum coverage requirements. 

TECHNICAL COMPLIANCE MATRIX (By-law 569-2013):
- Mandatory Cap (150.8.60.20(1)(B)): 45.0 m² 
- Area-Based Limit (150.8.60.20(1)(A)): 30% of lot area (30% of 160m² = 48.0 m²)
- Permitted Limit: Lesser of above = 45.0 m²
- Proposed Footprint: 44.5 m²
- Result: COMPLIANT

Please refer to revised Site Plan (Sheet A101) and updated Zoning Matrix.""",
        "resolution_status": "DRAWING_REVISION_NEEDED",
        "citations": [
            {"bylaw": "569-2013", "section": "150.8.60.1", "version": "Current"},
            {"bylaw": "569-2013", "section": "150.8.60.20", "version": "Current"}
        ],
        "agent_reasoning": "Identified the 'lesser of' dual-constraint. The 45sqm cap is the governing limit for this lot size. Cited both general lot coverage and specific laneway floor area sections."
    }

    print("--- Running Evaluation on GOOD Response ---")
    good_result = evaluator.evaluate_response(mock_deficiency, mock_good_response, mock_gold_citations)
    print(json.dumps(good_result, indent=2))

    print("\nWaiting 20 seconds before next evaluation...")
    time.sleep(20)

    print("\n--- Running Evaluation on P.ENG. OPTIMIZED Response ---")
    peng_result = evaluator.evaluate_response(mock_deficiency, mock_peng_response, mock_gold_citations)
    print(json.dumps(peng_result, indent=2))

    print("\nWaiting 20 seconds before next evaluation...")
    time.sleep(20)

    print("\n--- Running Evaluation on BAD Response ---")
    bad_result = evaluator.evaluate_response(mock_deficiency, mock_bad_response, mock_gold_citations)
    print(json.dumps(bad_result, indent=2))

def run_interactive_eval():
    """Interactive loop for running evaluations."""
    evaluator = EvalPipeline()
    
    print("\n" + "="*60)
    print("🏢 TORONTO PERMIT EVALUATION PIPELINE (P.ENG. INTERACTIVE)")
    print("="*60)
    print(f"Model: {os.getenv('LLM_MODEL', 'gemini-3.1-pro-preview')}")
    print(f"Provider: {os.getenv('LLM_PROVIDER', 'gemini')}")
    print("-"*60)

    while True:
        print("\n[1] Enter new deficiency for evaluation")
        print("[2] Run mock test (Sanity check)")
        print("[q] Quit")
        
        choice = input("\nSelect an option: ").strip().lower()
        
        if choice == 'q':
            break
        
        if choice == '2':
            run_sample_evals()
            continue
            
        if choice == '1':
            print("\n--- STEP 1: DEFICIENCY ---")
            original_deficiency = input("Enter the Examiner's deficiency text: ").strip()
            
            print("\n--- STEP 2: GOLD STANDARD ---")
            gold_standard = input("Enter expected citations (comma separated, e.g. 150.8.60.1, 9.10.20.3): ").strip()
            gold_standard_list = [c.strip() for c in gold_standard.split(",")]
            
            print("\n--- STEP 3: AI RESPONSE TO GRADE ---")
            draft_text = input("Enter the AI's draft response text: ").strip()
            provided_citations = input("Enter citations provided by AI (comma separated): ").strip()
            
            # Format the response for the evaluator
            generated_response = {
                "draft_text": draft_text,
                "resolution_status": "MANUAL_ENTRY",
                "citations": [{"section": c.strip()} for c in provided_citations.split(",")],
                "agent_reasoning": "Manually entered for interactive evaluation."
            }
            
            print("\n" + "-"*30)
            print("🚀 Sending to P.Eng. Evaluator...")
            result = evaluator.evaluate_response(original_deficiency, generated_response, gold_standard_list)
            
            print("\n" + "="*30)
            print("📊 EVALUATION RESULT")
            print("="*30)
            print(f"Citation Accuracy: {result.get('citation_accuracy')}/10")
            print(f"Completeness:      {result.get('completeness')}/10")
            print(f"Professional Tone: {result.get('professional_tone')}/10")
            print(f"OVERALL PASS:      {'✅ YES' if result.get('overall_pass') else '❌ NO'}")
            print(f"\nFEEDBACK:\n{result.get('feedback')}")
            print("="*60)

if __name__ == "__main__":
    run_sample_evals()
