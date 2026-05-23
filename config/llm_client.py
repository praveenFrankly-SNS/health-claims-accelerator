import os
import json
import urllib.request
import urllib.error

class GenericLLMClient:
    """
    A generic OpenAI-compatible LLM client for Databricks FMAPI or local testing.
    """
    def __init__(self):
        self.workspace_url = os.environ.get("DATABRICKS_HOST", "")
        self.databricks_token = os.environ.get("DATABRICKS_TOKEN", "")
        # Fallback to OpenAI if Databricks is not configured
        self.openai_key = os.environ.get("OPENAI_API_KEY", "")

    def generate(self, prompt: str, max_tokens: int = 400) -> str:
        # If we have Databricks credentials
        if self.workspace_url and self.databricks_token:
            # Simple wrapper around Databricks Foundation Model API (e.g. DBRX or Llama-3)
            # using urllib to avoid heavy dependencies in the accelerator
            url = f"{self.workspace_url.rstrip('/')}/serving-endpoints/databricks-dbrx-instruct/invocations"
            headers = {
                "Authorization": f"Bearer {self.databricks_token}",
                "Content-Type": "application/json"
            }
            data = {
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens
            }
            
            req = urllib.request.Request(url, headers=headers, data=json.dumps(data).encode('utf-8'))
            try:
                with urllib.request.urlopen(req) as response:
                    res_body = json.loads(response.read().decode('utf-8'))
                    return res_body.get("choices", [{}])[0].get("message", {}).get("content", "")
            except Exception as e:
                print(f"[LLM Client] Databricks FMAPI Error: {e}")
                
        # If we have OpenAI key (local testing)
        if self.openai_key:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens
            }
            req = urllib.request.Request(url, headers=headers, data=json.dumps(data).encode('utf-8'))
            try:
                with urllib.request.urlopen(req) as response:
                    res_body = json.loads(response.read().decode('utf-8'))
                    return res_body.get("choices", [{}])[0].get("message", {}).get("content", "")
            except Exception as e:
                print(f"[LLM Client] OpenAI API Error: {e}")

        # Fallback Mock if no keys provided (critical for the MVP running out of the box locally)
        print("[LLM Client] WARNING: No API keys configured. Returning mocked response.")
        if "Coverage Eligibility Agent" in prompt or "Agent 3" in prompt:
            return '{"coverage_status": "COVERED", "coverage_amount_estimate": 0, "exclusions_triggered": [], "policy_sections_cited": ["Section 4.2", "Section 5.1"], "notes": "Mocked response"}'
        elif "Fraud Detection Agent" in prompt or "Agent 2" in prompt:
            return '{"fraud_score": 0.1, "confidence": "HIGH", "reasoning": "Mocked response: Claim appears normal.", "flags": []}'
        elif "Document Intelligence Agent" in prompt or "Agent 1" in prompt:
            return '{"policy_number": "MOCK-POL", "claimant_name": "Mock Patient", "admission_date": "2026-01-01", "discharge_date": "2026-01-05", "hospital_name": "Apollo Hospital Coimbatore", "diagnosis_icd_code": "J18.9", "claimed_amount": 50000, "attending_physician_registration_number": "MC-5544"}'
        return '{"result": "Mocked fallback response"}'

llm = GenericLLMClient()
