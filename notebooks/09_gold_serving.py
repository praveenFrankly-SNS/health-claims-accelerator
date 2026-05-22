# Databricks notebook source
# MAGIC %md
# MAGIC # 09 Gold Serving
# MAGIC Optimizes the Gold table for serving downstream to the Databricks App and external systems.

# COMMAND ----------

CATALOG_NAME = "health_claims_dev"
SCHEMA_NAME = "claims"
spark.sql(f"USE {CATALOG_NAME}.{SCHEMA_NAME}")

gold_table = "gold_claim_decisions"

# COMMAND ----------

# Optimize table using ZORDER by claim_id to improve point lookup latency
print(f"Optimizing {gold_table}...")
try:
    spark.sql(f"OPTIMIZE {gold_table} ZORDER BY (claim_id)")
    print(f"Optimization complete on {gold_table}.")
except Exception as e:
    print(f"Optimization failed (expected if local / limited environment): {e}")

# COMMAND ----------

# Creating a dashboard view that unpacks JSON for Streamlit UI
view_query = f"""
CREATE OR REPLACE VIEW vw_claims_dashboard AS
SELECT
    claim_id,
    pipeline_status,
    extracted_data.claimant_name as claimant_name,
    extracted_data.diagnosis_icd_code as diagnosis,
    fraud.fraud_score as fraud_score,
    fraud.confidence as fraud_confidence,
    coverage.coverage_status as coverage_status,
    reserve.initial_reserve_amount as reserve_amount,
    adjuster_allocation as assigned_adjuster
FROM {gold_table}
"""

try:
    spark.sql(view_query)
    print("Dashboard view 'vw_claims_dashboard' created.")
except Exception as e:
    print(f"Failed to create view: {e}")

print("Gold Serving Complete.")
