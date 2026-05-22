# Databricks notebook source
# MAGIC %md
# MAGIC # 02 Silver Data Preparation
# MAGIC Cleans, validates, and standardizes Bronze data.
# MAGIC Implements a quarantine pattern simulating DLT expectations.

# COMMAND ----------

from pyspark.sql.functions import col

CATALOG_NAME = "health_claims_dev"
SCHEMA_NAME = "claims"
spark.sql(f"USE {CATALOG_NAME}.{SCHEMA_NAME}")

bronze_table = "bronze_claims"
silver_table = "silver_claims"
quarantine_table = "quarantine_claims"

# COMMAND ----------

print(f"Reading from {bronze_table}")
df_bronze = spark.table(bronze_table)

# Validation rules
# 1. claim_id must not be null
# 2. claimed_amount must be > 0

valid_condition = col("claim_id").isNotNull() & (col("claimed_amount") > 0)

# Split into valid and quarantine
df_valid = df_bronze.filter(valid_condition)
df_quarantine = df_bronze.filter(~valid_condition)

# COMMAND ----------

# Write to Silver Table
print(f"Writing valid claims to {silver_table}")
df_valid.write.format("delta").mode("overwrite").saveAsTable(silver_table)

# Write to Quarantine Table
print(f"Writing invalid claims to {quarantine_table}")
df_quarantine.write.format("delta").mode("overwrite").saveAsTable(quarantine_table)

print(f"Silver preparation complete. Valid: {df_valid.count()}, Quarantined: {df_quarantine.count()}")
