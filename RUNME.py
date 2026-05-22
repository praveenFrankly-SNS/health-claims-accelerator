# Databricks notebook source
# MAGIC %md
# MAGIC # Health Claims Multi-Agent Accelerator - RUNME
# MAGIC This notebook runs the full pipeline end-to-end.
# MAGIC Zero manual steps required once configured.

# COMMAND ----------

import time

def run_notebook(path, timeout_seconds=3600, arguments=None):
    if arguments is None:
        arguments = {}
    print(f"Running {path}...")
    start = time.time()
    try:
        # Assuming running within Databricks environment
        result = dbutils.notebook.run(path, timeout_seconds, arguments)
        print(f"Finished {path} in {time.time() - start:.2f} seconds. Result: {result}")
        return result
    except Exception as e:
        print(f"Failed to run {path}. Error: {e}")
        raise e

# COMMAND ----------

# 1. Setup the workspace and Unity Catalog
run_notebook("./notebooks/00_setup")

# COMMAND ----------

# 2. Generate Synthetic Data
# Note: we can run this via run_notebook if it's a notebook, or just %run it
try:
    print("Generating synthetic data...")
    dbutils.notebook.run("./data/generate_synthetic_data.py", 1800)
except Exception as e:
    print("Warning: could not execute synthetic data generator as notebook. You may need to run it directly.")

# COMMAND ----------

# 3. Bronze & Silver Ingestion
run_notebook("./notebooks/01_bronze_ingestion")
run_notebook("./notebooks/02_silver_dlt")

# COMMAND ----------

# 4. We do not deploy the agents as endpoints here.
# The orchestrator notebook will import or run them sequentially.
run_notebook("./notebooks/07_supervisor_orchestrator")

# COMMAND ----------

# 5. Serving
run_notebook("./notebooks/09_gold_serving")

print("Pipeline execution completed successfully.")
