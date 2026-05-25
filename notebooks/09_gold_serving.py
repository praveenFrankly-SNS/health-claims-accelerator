# Databricks notebook source
# MAGIC %md
# MAGIC # 09 Gold Serving
# MAGIC Optimizes the Gold table for serving downstream to the Databricks App and external systems.
# MAGIC Contains a Lakehouse Monitoring stub.

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
    get_json_object(payload, '$.pipeline_status') as pipeline_status,
    get_json_object(payload, '$.extracted_data.claimant_name') as claimant_name,
    get_json_object(payload, '$.extracted_data.diagnosis_icd') as diagnosis,
    cast(get_json_object(payload, '$.fraud.fraud_score') as double) as fraud_score,
    get_json_object(payload, '$.fraud.confidence') as fraud_confidence,
    get_json_object(payload, '$.coverage.coverage_status') as coverage_status,
    cast(get_json_object(payload, '$.reserve.initial_reserve_amount') as double) as reserve_amount,
    get_json_object(payload, '$.adjuster_allocation') as assigned_adjuster
FROM {gold_table}
"""

try:
    spark.sql(view_query)
    print("Dashboard view 'vw_claims_dashboard' created.")
except Exception as e:
    print(f"Failed to create view: {e}")

# COMMAND ----------
# DBTITLE 1,Lakehouse Monitoring Stub
print("Configuring Lakehouse Monitoring...")
try:
    # This is a stub for the Lakehouse Monitoring setup
    # In a full deployment, this creates a metric table monitoring data drift on the Gold table
    stub_query = f"""
    -- CREATE MONITOR {CATALOG_NAME}.{SCHEMA_NAME}.gold_monitor
    -- ON {CATALOG_NAME}.{SCHEMA_NAME}.{gold_table}
    -- SCHEDULE CRON '0 0 * * *'
    -- ASSETS DIR 'dbfs:/lakehouse_monitors/{CATALOG_NAME}/{SCHEMA_NAME}/gold'
    """
    # spark.sql(stub_query)
    print("Lakehouse Monitor stub executed successfully. Enable in Paid/Trial workspaces.")
except Exception as e:
    print(f"Failed to configure monitoring: {e}")

print("Gold Serving Complete.")
