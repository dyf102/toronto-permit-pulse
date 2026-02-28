import sys
import httpx
import json

def test():
    print("Testing pipeline/run...")
    url = "http://localhost:8000/api/v1/pipeline/run"
    
    data = {
        "property_address": "123 RAG Test St",
        "suite_type": "GARDEN",
        "laneway_abutment_length": "10.0"
    }

    # Create a dummy PDF 
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
    
    try:
        response = httpx.post(
            url,
            data=data,
            files={"file": ("dummy.pdf", pdf_content, "application/pdf")},
            timeout=120.0
        )
        print("Status Code:", response.status_code)
        
        if response.status_code == 200:
            res_json = response.json()
            for r in res_json.get("results", []):
                agent = r.get("agent")
                reasoning = r.get("response", {}).get("agent_reasoning")
                print(f"Agent: {agent}\nReasoning: {reasoning}\n")
        else:
            print("Response:", response.text)
            
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test()
