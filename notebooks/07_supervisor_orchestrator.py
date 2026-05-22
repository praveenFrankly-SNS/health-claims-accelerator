# Databricks notebook source
# MAGIC %md
# MAGIC # 07 Supervisor Orchestrator
# MAGIC Uses LangGraph (or simulated equivalent) to orchestrate the 4 agents in memory.

# COMMAND ----------

import os
import sys
import json
from pyspark.sql import SparkSession

# Ensure we can import the agent functions
notebook_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
sys.path.append(os.path.abspath(os.path.join(notebook_dir, "..")))

import importlib

# Dynamic imports since module names start with numbers
agent1_module = importlib.import_module("notebooks.03_agent1_doc_intelligence")
agent1_doc_intelligence = agent1_module.agent1_doc_intelligence

agent2_module = importlib.import_module("notebooks.04_agent2_fraud")
agent2_fraud = agent2_module.agent2_fraud

agent3_module = importlib.import_module("notebooks.05_agent3_coverage")
agent3_coverage = agent3_module.agent3_coverage

agent4_module = importlib.import_module("notebooks.06_agent4_reserve")
agent4_reserve = agent4_module.agent4_reserve

adjuster_module = importlib.import_module("notebooks.08_adjuster_allocation")
allocate_adjuster = adjuster_module.allocate_adjuster

# COMMAND ----------

def process_single_claim(claim_id: str) -> dict:
    """
    Simulates a stateful LangGraph execution.
    State flows through agents in memory. No intermediate DB writes.
    """
    state = {"claim_id": claim_id}
    
    # 1. Document Intelligence
    state = agent1_doc_intelligence(state)
    
    # Conditional Branching
    if state.get("completeness_score", 0) < 0.8:
        print(f"[{claim_id}] Missing fields detected. Halting pipeline.")
        state["pipeline_status"] = "HALTED_INCOMPLETE"
        return state
        
    # 2 & 3. Fraud and Coverage (Simulated Parallel)
    state = agent2_fraud(state)
    state = agent3_coverage(state)
    
    # 4. Reserve
    state = agent4_reserve(state)
    
    # 5. Adjuster Allocation
    state = allocate_adjuster(state)
    
    state["pipeline_status"] = "COMPLETED"
    return state

# COMMAND ----------

spark = SparkSession.builder.getOrCreate()
CATALOG_NAME = "health_claims_dev"
SCHEMA_NAME = "claims"

# Read Silver claims to get claim IDs
silver_table = f"{CATALOG_NAME}.{SCHEMA_NAME}.silver_claims"
try:
    df_silver = spark.table(silver_table)
    claim_ids = [row.claim_id for row in df_silver.select("claim_id").limit(10).collect()]
except Exception as e:
    print(f"Could not read silver table: {e}. Using dummy IDs.")
    claim_ids = ["CLM-2026-10000"]

# Process all claims
results = []
for cid in claim_ids:
    final_state = process_single_claim(cid)
    results.append(final_state)

# Write to Gold Table
if results:
    # Convert dicts to string JSONs to store easily in a single column for the MVP,
    # or flatten it. We will write as JSON to a temp file and read via spark.
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
        temp_path = f.name
        
    df_gold = spark.read.json("file:" + temp_path)
    
    gold_table = f"{CATALOG_NAME}.{SCHEMA_NAME}.gold_claim_decisions"
    print(f"Writing Gold decision packets to {gold_table}...")
    df_gold.write.format("delta").mode("overwrite").saveAsTable(gold_table)
    os.remove(temp_path)
else:
    print("No claims processed.")

print("Orchestration complete.")
