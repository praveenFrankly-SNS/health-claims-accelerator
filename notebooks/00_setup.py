# Databricks notebook source
# MAGIC %md
# MAGIC # 00 Setup: Unity Catalog & Database Initialization
# MAGIC This notebook ensures the catalog, schema, and volumes are created.

# COMMAND ----------

CATALOG_NAME = "main"
SCHEMA_NAME = "health_claims_dev"
VOLUME_NAME = "documents"

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
