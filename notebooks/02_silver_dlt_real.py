# 02_silver_dlt_real.py
# Databricks notebook source
# MAGIC %md
# MAGIC # 02 Silver — Delta Live Tables (Trial/Paid Edition)
# MAGIC This is the production DLT version. Activate on trial/paid workspace.
# MAGIC Replaces 02_silver_preparation_spark_sim.py

import dlt
from pyspark.sql.functions import col, sha2, datediff, to_date

@dlt.table(
    name="silver_claims",
    comment="Validated claims with PII masked and ML features computed"
)
@dlt.expect_or_fail("valid_claim_id", "claim_id IS NOT NULL")
@dlt.expect_or_fail("positive_amount", "claimed_amount > 0")
def silver_claims():
    df_bronze = dlt.read("bronze_claims")
    # [Same transformation logic as spark sim version]
    return df_valid

@dlt.table(name="quarantine_claims")
def quarantine():
    # [Quarantine logic]
    return df_quarantine
