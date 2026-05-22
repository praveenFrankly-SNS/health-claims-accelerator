# Databricks notebook source
# Databricks notebook source
# MAGIC %md
# MAGIC # 00 — Setup
# MAGIC **Purpose:** Create Unity Catalog resources (catalog, schemas, volumes) for the Health Claims Accelerator.
# MAGIC **Run this once per environment before any other notebook.**
# MAGIC **Author:** SNS Square | **Version:** 1.0 | **Last Updated:** May 2026
# MAGIC **Prerequisites:** Unity Catalog enabled, CREATE CATALOG privilege on metastore.

# COMMAND ----------
# DBTITLE 1,Parameters — edit via widgets, never hardcode
dbutils.widgets.text("catalog", "health_claims_dev", "Catalog Name")
dbutils.widgets.text("schema", "claims", "Schema Name")
dbutils.widgets.text("env", "dev", "Environment (dev/staging/prod)")

catalog = dbutils.widgets.get("catalog")
schema  = dbutils.widgets.get("schema")
env     = dbutils.widgets.get("env")

print(f"Setting up: {catalog}.{schema} (env={env})")

# COMMAND ----------
# DBTITLE 1,Create catalog
spark.sql(f"CREATE CATALOG IF NOT EXISTS `{catalog}`")
spark.sql(f"USE CATALOG `{catalog}`")
print(f"✓ Catalog '{catalog}' ready")

# COMMAND ----------
# DBTITLE 1,Create schemas
for s in ["claims", "ml_models", "vectors", "audit"]:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{s}`")
    print(f"✓ Schema '{catalog}.{s}' ready")

# COMMAND ----------
# DBTITLE 1,Create Unity Catalog Volumes (for PDFs and unstructured docs)
spark.sql(f"""
    CREATE VOLUME IF NOT EXISTS `{catalog}`.`claims`.`raw_documents`
    COMMENT 'Raw claim documents — discharge summaries, hospital bills, prescriptions'
""")

spark.sql(f"""
    CREATE VOLUME IF NOT EXISTS `{catalog}`.`claims`.`policy_forms`
    COMMENT 'Health insurance policy form documents for Coverage RAG agent'
""")

spark.sql(f"""
    CREATE VOLUME IF NOT EXISTS `{catalog}`.`claims`.`synthetic_data`
    COMMENT 'Generated synthetic claims and policy data for MVP'
""")

print("✓ UC Volumes ready")

# COMMAND ----------
# DBTITLE 1,Tag catalog with environment metadata
spark.sql(f"ALTER CATALOG `{catalog}` SET TAGS ('env' = '{env}', 'project' = 'health-claims-accelerator', 'owner' = 'sns-square')")
print("✓ Catalog tagged")

# COMMAND ----------
# DBTITLE 1,Verify setup — print summary
summary = spark.sql(f"""
    SELECT schema_name 
    FROM `{catalog}`.information_schema.schemata
    ORDER BY schema_name
""").collect()

print(f"\n=== Setup Complete: {catalog} ===")
for row in summary:
    print(f"  Schema: {row.schema_name}")

volumes = spark.sql(f"SHOW VOLUMES IN `{catalog}`.`claims`").collect()
for row in volumes:
    print(f"  Volume: {row.volume_name}")

# COMMAND ----------
# DBTITLE 1,Write setup completion record to audit log
from datetime import datetime
import json

audit_data = [{
    "event": "SETUP_COMPLETE",
    "catalog": catalog,
    "schema": schema,
    "env": env,
    "timestamp": datetime.utcnow().isoformat(),
    "run_by": spark.sql("SELECT current_user()").collect()[0][0]
}]

(spark.createDataFrame(audit_data)
     .write
     .format("delta")
     .mode("append")
     .saveAsTable(f"`{catalog}`.`audit`.`setup_log`"))

print("✓ Audit log entry written")
print("\nRun notebooks in this order next: 01 → 02 → 03 → 04 → 05 → 06 → 07")

# COMMAND ----------

# MAGIC %md
# MAGIC # 00 Setup: Unity Catalog & Database Initialization
# MAGIC This notebook ensures the catalog, schema, and volumes are created.

# COMMAND ----------

CATALOG_NAME = catalog
SCHEMA_NAME = schema
VOLUME_NAME = volume_name

# COMMAND ----------

# 1. Create Schema
print(f"Ensuring schema {CATALOG_NAME}.{SCHEMA_NAME} exists...")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG_NAME}.{SCHEMA_NAME}")
spark.sql(f"USE {CATALOG_NAME}.{SCHEMA_NAME}")

# COMMAND ----------

# 2. Create Volume for unstructured data
print(f"Ensuring volume {VOLUME_NAME} exists...")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG_NAME}.{SCHEMA_NAME}.{VOLUME_NAME}")

# COMMAND ----------

print("Setup Complete.")
