# Databricks notebook source
# MAGIC %md
# MAGIC # 03 Agent 1: Document Intelligence
# MAGIC Extracts structured data and computes completeness score from unstructured claims submissions (PDFs/Text).

# COMMAND ----------

import os
import json
import sys

# In a real environment, you'd add the repo path to sys.path if not running as a package
# We assume config.llm_client is available
try:
    from config.llm_client import llm
except ImportError:
    # Fallback for notebook standalone run
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from config.llm_client import llm

def agent1_doc_intelligence(claim_state: dict) -> dict:
    """
    Reads the discharge summary from the local volume/path and uses the LLM to extract fields.
    """
    claim_id = claim_state.get("claim_id")
    if not claim_id:
        return {"error": "No claim_id provided"}

    print(f"[Agent 1] Processing document extraction for {claim_id}...")
    
    # Simulate reading from UC Volume
    file_path = f"./data/raw/unstructured/{claim_id}_discharge_summary.txt"
    try:
        with open(file_path, "r") as f:
            document_text = f.read()
    except FileNotFoundError:
        return {"completeness_score": 0.0, "missing_fields": ["discharge_summary"], "extracted_data": {}}

    prompt = f"""
    You are an AI Document Intelligence Agent for health insurance.
    Extract the following fields from the discharge summary provided:
    - policy_number
    - claimant_name
    - admission_date
    - discharge_date
    - hospital_name
    - diagnosis_icd_code
    - claimed_amount
    - attending_physician_registration_number
    
    Return a JSON object containing these keys. If a field is not found, leave it as null.
    Do NOT output anything except valid JSON.
    
    Document:
    {document_text}
    """
    
    response_text = llm.generate(prompt, max_tokens=500)
    
    # Simple JSON extraction
    extracted_data = {}
    try:
        # Very simple parse (assuming LLM returns pure JSON)
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1
        if start_idx != -1 and end_idx != -1:
            extracted_data = json.loads(response_text[start_idx:end_idx])
    except Exception as e:
        print(f"[Agent 1] JSON parse error: {e}")

    # Calculate completeness score based on required fields
    required_fields = ["policy_number", "claimant_name", "admission_date", "discharge_date", 
                       "hospital_name", "diagnosis_icd_code", "claimed_amount", "attending_physician_registration_number"]
    
    missing_fields = [f for f in required_fields if not extracted_data.get(f)]
    
    completeness_score = (len(required_fields) - len(missing_fields)) / len(required_fields)
    
    result = {
        "completeness_score": round(completeness_score, 2),
        "missing_fields": missing_fields,
        "extracted_data": extracted_data
    }
    
    # Update the claim state
    claim_state.update(result)
    return claim_state

# COMMAND ----------

# Standalone Test
if __name__ == "__main__":
    test_state = {"claim_id": "CLM-2026-10000"}
    res = agent1_doc_intelligence(test_state)
    print(json.dumps(res, indent=2))
