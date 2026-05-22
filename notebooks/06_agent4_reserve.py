# Databricks notebook source
# MAGIC %md
# MAGIC # 06 Agent 4: Reserve Estimation
# MAGIC Uses regression prototype and LLM severity uplift to set an initial reserve amount.

# COMMAND ----------

import os
import sys

import importlib

notebook_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
sys.path.append(os.path.abspath(os.path.join(notebook_dir, "..")))
import config.llm_client
importlib.reload(config.llm_client)  # Force reload to avoid Databricks caching
from config.llm_client import llm

# Force inject Databricks credentials if running in a Notebook
try:
    ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
    if not llm.workspace_url:
        llm.workspace_url = ctx.apiUrl().get()
    if not llm.databricks_token:
        llm.databricks_token = ctx.apiToken().get()
except Exception:
    pass

def agent4_reserve(claim_state: dict) -> dict:
    claim_id = claim_state.get("claim_id")
    print(f"[Agent 4] Processing reserve estimation for {claim_id}...")
    
    extracted = claim_state.get("extracted_data", {})
    coverage = claim_state.get("coverage", {})
    
    claimed_amount = extracted.get("claimed_amount", 0)
    if claimed_amount is None: claimed_amount = 0
    try:
        claimed_amount = float(claimed_amount)
    except:
        claimed_amount = 0

    # Base reserve is the claimed amount or a percentage of it if partially covered
    base_reserve = claimed_amount
    if coverage.get("coverage_status") == "PARTIAL":
        base_reserve = claimed_amount * 0.8
    elif coverage.get("coverage_status") == "EXCLUDED":
        base_reserve = 0
        
    # LLM Severity Uplift based on diagnosis
    diagnosis = extracted.get("diagnosis_icd_code", "UNKNOWN")
    prompt = f"""
    You are an AI Reserve Estimation Agent. Assess the severity of this medical diagnosis and recommend an uplift multiplier (1.0 to 1.5).
    Diagnosis: {diagnosis}
    
    Return a JSON object with:
    - uplift_multiplier (float)
    - reasoning (string)
    Do NOT output anything except valid JSON.
    """
    
    response_text = llm.generate(prompt, max_tokens=200)
    uplift = 1.0
    reasoning = "Standard reserve applied."
    
    try:
        import json
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1
        if start_idx != -1 and end_idx != -1:
            data = json.loads(response_text[start_idx:end_idx])
            uplift = float(data.get("uplift_multiplier", 1.0))
            reasoning = data.get("reasoning", reasoning)
    except Exception as e:
        print(f"[Agent 4] JSON parse error: {e}")

    final_reserve = base_reserve * uplift
    
    result = {
        "reserve": {
            "initial_reserve_amount": round(final_reserve, 2),
            "confidence_interval": {
                "P10": round(final_reserve * 0.8, 2),
                "P50": round(final_reserve, 2),
                "P90": round(final_reserve * 1.2, 2)
            },
            "reasoning": reasoning
        }
    }
    
    claim_state.update(result)
    return claim_state

# COMMAND ----------

if __name__ == "__main__":
    test_state = {"claim_id": "CLM-2026-10000", "extracted_data": {"claimed_amount": 50000, "diagnosis_icd_code": "J12.9"}, "coverage": {"coverage_status": "COVERED"}}
    res = agent4_reserve(test_state)
    import json
    print(json.dumps(res, indent=2))
