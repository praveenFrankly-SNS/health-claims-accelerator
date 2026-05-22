# Databricks notebook source
# MAGIC %md
# MAGIC # 05 Agent 3: Coverage Eligibility
# MAGIC Simulates RAG against policy forms to determine if the claim is covered.

# COMMAND ----------

import os
import sys

try:
    from config.llm_client import llm
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from config.llm_client import llm

def retrieve_policy_chunks(policy_number: str) -> str:
    # In a real scenario, this queries Databricks Vector Search using the policy_number
    # For MVP, we mock the retrieved policy document.
    return """
    Section 4.2 - Room Rent Limit
    The policy covers room rent up to 1% of the Base Sum Insured per day.
    
    Section 5.1 - Exclusions
    Treatment for congenital diseases, cosmetic surgery, and unproven treatments are excluded.
    
    Section 7.1 - Network Hospital Coverage
    Claims from network hospitals are eligible for cashless processing. Non-network hospitals are reimbursement only with a 10% co-pay.
    """

def agent3_coverage(claim_state: dict) -> dict:
    claim_id = claim_state.get("claim_id")
    print(f"[Agent 3] Processing coverage eligibility for {claim_id}...")
    
    extracted = claim_state.get("extracted_data", {})
    policy_number = extracted.get("policy_number", "UNKNOWN")
    diagnosis = extracted.get("diagnosis_icd_code", "UNKNOWN")
    
    policy_text = retrieve_policy_chunks(policy_number)
    
    prompt = f"""
    You are an AI Coverage Eligibility Agent. Determine if the claim is covered based on the policy text.
    
    Claim Facts:
    - Policy Number: {policy_number}
    - Diagnosis: {diagnosis}
    - Hospital: {extracted.get('hospital_name', 'Unknown')}
    - Claimed Amount: {extracted.get('claimed_amount', 0)}
    
    Policy Document Excerpts:
    {policy_text}
    
    Return a JSON object with:
    - coverage_status (COVERED, EXCLUDED, PARTIAL, NEEDS_REVIEW)
    - coverage_amount_estimate (number)
    - exclusions_triggered (list of strings)
    - notes (string)
    Do NOT output anything except valid JSON.
    """
    
    response_text = llm.generate(prompt, max_tokens=400)
    
    coverage_result = {
        "coverage_status": "NEEDS_REVIEW",
        "coverage_amount_estimate": 0,
        "exclusions_triggered": [],
        "notes": "Failed to parse LLM response"
    }
    
    try:
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1
        if start_idx != -1 and end_idx != -1:
            coverage_result = json.loads(response_text[start_idx:end_idx])
    except Exception as e:
        print(f"[Agent 3] JSON parse error: {e}")

    result = {
        "coverage": coverage_result
    }
    
    claim_state.update(result)
    return claim_state

# COMMAND ----------

# Standalone Test
if __name__ == "__main__":
    test_state = {"claim_id": "CLM-2026-10000", "extracted_data": {"policy_number": "POL-123", "claimed_amount": 50000}}
    res = agent3_coverage(test_state)
    import json
    print(json.dumps(res, indent=2))
