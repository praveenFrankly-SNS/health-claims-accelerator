# Databricks notebook source
# MAGIC %md
# MAGIC # 04 Agent 2: Fraud Signal Detection
# MAGIC Uses a mock ML model for structured features and LLM for narrative consistency check.

# COMMAND ----------

import os
import sys
import random

try:
    from config.llm_client import llm
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from config.llm_client import llm

def get_ml_fraud_score(claim_state: dict) -> float:
    # In a real scenario, this would load a trained XGBoost model from MLflow Registry
    # and run inference on features like claim velocity, amount/premium ratio, etc.
    # For MVP, we simulate a score based on amount logic.
    amount = claim_state.get("extracted_data", {}).get("claimed_amount", 0)
    if amount is None: amount = 0
    try:
        amount = float(amount)
    except:
        amount = 0
        
    score = 0.1 # base
    if amount > 200000:
        score += 0.3
    if amount > 300000:
        score += 0.2
        
    # random noise
    score += random.uniform(0, 0.15)
    return min(score, 1.0)

def agent2_fraud(claim_state: dict) -> dict:
    """
    Checks for fraud using ML structured features and LLM narrative checking.
    """
    claim_id = claim_state.get("claim_id")
    print(f"[Agent 2] Processing fraud detection for {claim_id}...")

    ml_score = get_ml_fraud_score(claim_state)
    
    # LLM Narrative Check
    file_path = f"./data/raw/unstructured/{claim_id}_discharge_summary.txt"
    document_text = ""
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            document_text = f.read()

    prompt = f"""
    You are an AI Fraud Detection Agent. Analyze the following medical discharge summary for inconsistencies.
    Look for: upcoding, unbundling, inflated room rent, or contradictory statements.
    
    Document:
    {document_text}
    
    Return a JSON object with:
    - llm_fraud_score (float 0-1)
    - narrative_signals (list of strings describing any red flags found, or empty list if none)
    Do NOT output anything except valid JSON.
    """
    
    response_text = llm.generate(prompt, max_tokens=300)
    
    llm_fraud_score = 0.1
    signals = []
    try:
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1
        if start_idx != -1 and end_idx != -1:
            data = json.loads(response_text[start_idx:end_idx])
            llm_fraud_score = data.get("llm_fraud_score", 0.1)
            signals = data.get("narrative_signals", [])
    except Exception as e:
        print(f"[Agent 2] JSON parse error: {e}")

    final_score = (ml_score * 0.6) + (llm_fraud_score * 0.4)
    confidence = "HIGH" if final_score > 0.6 else ("MEDIUM" if final_score > 0.3 else "LOW")
    
    result = {
        "fraud": {
            "fraud_score": round(final_score, 2),
            "confidence": confidence,
            "fraud_signals": signals
        }
    }
    
    claim_state.update(result)
    return claim_state

# COMMAND ----------

# Standalone Test
if __name__ == "__main__":
    test_state = {"claim_id": "CLM-2026-10000", "extracted_data": {"claimed_amount": 250000}}
    res = agent2_fraud(test_state)
    import json
    print(json.dumps(res, indent=2))
