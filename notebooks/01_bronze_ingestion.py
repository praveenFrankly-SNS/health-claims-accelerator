# Databricks notebook source
# MAGIC %md
# MAGIC # 01 Bronze Ingestion
# MAGIC Ingests structured claims from raw CSV to a Bronze Delta Table and copies unstructured text to UC Volumes.

# COMMAND ----------

import os
from pyspark.sql.functions import current_timestamp, lit

CATALOG_NAME = "main"
SCHEMA_NAME = "health_claims_dev"
VOLUME_NAME = "documents"

spark.sql(f"USE {CATALOG_NAME}.{SCHEMA_NAME}")

# COMMAND ----------

# 1. Ingest Structured CSV to Bronze Table
raw_csv_path = "file:" + os.path.abspath("./data/raw/structured/claims.csv")
print(f"Reading from {raw_csv_path}")

df_raw = spark.read.csv(raw_csv_path, header=True, inferSchema=True)
df_bronze = df_raw.withColumn("ingested_at", current_timestamp()) \
                  .withColumn("source", lit(raw_csv_path))

# Write to Bronze Delta Table (Append-only)
bronze_table = f"{CATALOG_NAME}.{SCHEMA_NAME}.bronze_claims"
print(f"Writing to {bronze_table}")
df_bronze.write.format("delta").mode("append").saveAsTable(bronze_table)

# COMMAND ----------

# 2. Copy unstructured data to UC Volume
# In a real scenario, Auto Loader / external system would land files directly in the Volume.
# Here, we copy our synthetic text files to the volume path.
# Databricks volume paths look like /Volumes/catalog/schema/volume/
volume_path = f"/Volumes/{CATALOG_NAME}/{SCHEMA_NAME}/{VOLUME_NAME}/"

# For local development simulation if /Volumes is not accessible directly in file system:
print(f"Simulating copy of unstructured data to {volume_path}")
try:
    # If dbutils.fs is available, we copy to the volume
    dbutils.fs.mkdirs(volume_path)
    local_unstructured_dir = "file:" + os.path.abspath("./data/raw/unstructured")
    dbutils.fs.cp(local_unstructured_dir, volume_path, recurse=True)
    print("Files copied to Unity Catalog Volume successfully.")
except Exception as e:
    print(f"Could not copy files to volume (expected if running outside Databricks). {e}")

print("Bronze ingestion complete.")
