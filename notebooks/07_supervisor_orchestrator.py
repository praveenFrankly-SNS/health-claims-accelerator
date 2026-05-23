# Databricks notebook source
# MAGIC %md
# MAGIC # 07 Supervisor Orchestrator
# MAGIC Uses LangGraph to orchestrate the 4 agents.
# MAGIC Agents 2 and 3 run sequentially.

# COMMAND ----------
# MAGIC %pip install langgraph sentence-transformers xgboost

# COMMAND ----------

import os
import sys
import json
import yaml
from pyspark.sql import SparkSession
from langgraph.graph import StateGraph, END
from typing import TypedDict, Dict, Any
import runpy

# Ensure we can import the agent functions
notebook_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
sys.path.append(os.path.abspath(os.path.join(notebook_dir, "..")))

def load_agent_function(filename, func_name):
    filepath = os.path.join(notebook_dir, filename)
    module_dict = runpy.run_path(filepath)
    return module_dict[func_name]

agent1_doc_intelligence = load_agent_function("03_agent1_doc_intelligence.py", "agent1_doc_intelligence")
agent2_fraud = load_agent_function("04_agent2_fraud.py", "agent2_fraud")
agent3_coverage = load_agent_function("05_agent3_coverage.py", "agent3_coverage")
agent4_reserve = load_agent_function("06_agent4_reserve.py", "agent4_reserve")
allocate_adjuster = load_agent_function("08_adjuster_allocation.py", "allocate_adjuster")

# Load thresholds
repo_root = ".." if os.path.exists("../config/thresholds.yml") else "."
with open(f"{repo_root}/config/thresholds.yml", "r") as f:
    thresholds = yaml.safe_load(f)

# COMMAND ----------

# LangGraph State definition
class ClaimState(TypedDict):
    claim_id: str
    extracted_data: dict
    completeness_score: float
    missing_fields: list
    cross_validation_status: str
    fraud: dict
    coverage: dict
    reserve: dict
    adjuster_allocation: str
    pipeline_status: str
    
# Node wrappers
def node_agent1(state: ClaimState):
    print(f"\n[Orchestrator] Running Agent 1 for {state['claim_id']}")
    return agent1_doc_intelligence(dict(state))

def node_agent2(state: ClaimState):
    print(f"\n[Orchestrator] Running Agent 2 for {state['claim_id']}")
    return agent2_fraud(dict(state))

def node_agent3(state: ClaimState):
    print(f"\n[Orchestrator] Running Agent 3 for {state['claim_id']}")
    return agent3_coverage(dict(state))

def node_agent4(state: ClaimState):
    print(f"\n[Orchestrator] Running Agent 4 for {state['claim_id']}")
    # Merge states since Agent 2 and 3 sequentially enriched the state
    return agent4_reserve(dict(state))

def node_allocate(state: ClaimState):
    print(f"\n[Orchestrator] Running Allocation for {state['claim_id']}")
    return allocate_adjuster(dict(state))

def node_halt(state: ClaimState):
    print(f"\n[Orchestrator] Halting pipeline for {state['claim_id']}")
    return {"pipeline_status": "HALTED_INCOMPLETE"}

def node_post_doc_check(state: ClaimState):
    print(f"\n[Orchestrator] Post-Doc Check passed for {state['claim_id']}. Proceeding to subsequent agents.")
    return state

# COMMAND ----------

# Define the Graph
workflow = StateGraph(ClaimState)

workflow.add_node("agent1", node_agent1)
workflow.add_node("post_doc_check", node_post_doc_check)
workflow.add_node("agent2", node_agent2)
workflow.add_node("agent3", node_agent3)
workflow.add_node("agent4", node_agent4)
workflow.add_node("allocate", node_allocate)
workflow.add_node("halt", node_halt)

# Conditional edge after Agent 1
def should_continue(state: ClaimState) -> str:
    # Use thresholds config
    min_score = thresholds.get("completeness_score_min", 0.80)
    if state.get("completeness_score", 0) < min_score or state.get("cross_validation_status") != "PASSED":
        return "halt"
    return "continue"

workflow.set_entry_point("agent1")

# Add conditional edges from agent1
workflow.add_conditional_edges(
    "agent1",
    should_continue,
    {
        "halt": "halt",
        "continue": "post_doc_check" 
    }
)

# Sequential flow for the remaining agents
workflow.add_edge("post_doc_check", "agent2")
workflow.add_edge("agent2", "agent3")
workflow.add_edge("agent3", "agent4")

workflow.add_edge("agent4", "allocate")
workflow.add_edge("allocate", END)
workflow.add_edge("halt", END)

app = workflow.compile()

# COMMAND ----------

spark = SparkSession.builder.getOrCreate()
CATALOG_NAME = "health_claims_dev"
SCHEMA_NAME = "claims"

# Read Silver claims to get claim IDs
silver_table = f"{CATALOG_NAME}.{SCHEMA_NAME}.silver_claims"
try:
    df_silver = spark.table(silver_table)
    # Convert to list of dicts to pass full rows into the orchestrator state
    claims_to_process = [row.asDict() for row in df_silver.limit(3).collect()]
except Exception as e:
    print(f"Could not read silver table: {e}. Using dummy IDs.")
    claims_to_process = [{"claim_id": "CLM-2026-10000"}]

# Process all claims
results = []
for claim in claims_to_process:
    initial_state = {
        "claim_id": claim.get("claim_id"),
        "days_since_inception": claim.get("days_since_inception", 500),
        "claim_velocity": claim.get("claim_velocity", 0),
        "amount_to_premium_ratio": claim.get("amount_to_premium_ratio", 0)
    }
    
    # Run the compiled LangGraph app
    final_state = app.invoke(initial_state)
    
    if final_state.get("pipeline_status") != "HALTED_INCOMPLETE":
        final_state["pipeline_status"] = "COMPLETED"
        
    results.append(final_state)

# Write to Gold Table
if results:
    from pyspark.sql import Row
    rows = [Row(claim_id=r.get("claim_id", "UNKNOWN"), payload=json.dumps(r)) for r in results]
    df_gold = spark.createDataFrame(rows)
    
    gold_table = f"{CATALOG_NAME}.{SCHEMA_NAME}.gold_claim_decisions"
    print(f"Writing {len(rows)} Gold decision packets to {gold_table}...")
    df_gold.write.format("delta").mode("overwrite").saveAsTable(gold_table)
else:
    print("No claims processed.")

print("Orchestration complete.")
