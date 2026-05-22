# Databricks notebook source
# MAGIC %md
# MAGIC # 08 Adjuster Allocation
# MAGIC Deterministic rule-based function to route claims to the correct adjuster tier.

# COMMAND ----------

def allocate_adjuster(claim_state: dict) -> dict:
    """
    Rule-based routing logic. No LLM involved.
    """
    fraud_score = claim_state.get("fraud", {}).get("fraud_score", 0)
    reserve_amount = claim_state.get("reserve", {}).get("initial_reserve_amount", 0)
    coverage_status = claim_state.get("coverage", {}).get("coverage_status", "NEEDS_REVIEW")
    
    print(f"[Adjuster Allocation] Routing claim {claim_state.get('claim_id')}")
    
    # Simple thresholds (would normally read from config/thresholds.yml)
    if fraud_score > 0.70 or reserve_amount > 500000:
        adjuster = "SENIOR_FIELD_ADJUSTER"
    elif coverage_status == "NEEDS_REVIEW":
        adjuster = "MEDICAL_EXAMINER"
    elif fraud_score < 0.30 and reserve_amount < 50000 and coverage_status == "COVERED":
        adjuster = "STP_ELIGIBLE"  # Straight-Through Processing
    else:
        adjuster = "STAFF_ADJUSTER"
        
    result = {
        "adjuster_allocation": adjuster
    }
    
    claim_state.update(result)
    return claim_state

# COMMAND ----------

if __name__ == "__main__":
    test_state = {"fraud": {"fraud_score": 0.8}, "reserve": {"initial_reserve_amount": 100000}}
    res = allocate_adjuster(test_state)
    print(res["adjuster_allocation"])
