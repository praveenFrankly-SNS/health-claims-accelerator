import os
import json
import requests
# Try to import dbutils if running in Databricks
try:
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.getOrCreate()
    # Databricks allows getting secrets via dbutils
    def get_dbutils(spark):
        try:
            from pyspark.dbutils import DBUtils
            dbutils = DBUtils(spark)
        except ImportError:
            import IPython
            dbutils = IPython.get_ipython().user_ns.get("dbutils")
        return dbutils
    dbutils = get_dbutils(spark)
except Exception:
    dbutils = None

class LLMClient:
    def __init__(self, mode="databricks", model_name="databricks-meta-llama-3-1-70b-instruct"):
        """
        mode: 'databricks' or 'external'
        model_name: Foundation model endpoint name or external model name
        """
        self.mode = mode
        self.model_name = model_name
        self.workspace_url = os.environ.get("DATABRICKS_HOST", "")
        self.databricks_token = os.environ.get("DATABRICKS_TOKEN", "")
        
        # If running inside a Databricks notebook, fetch from context dynamically
        if not self.workspace_url or not self.databricks_token:
            if dbutils:
                try:
                    ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
                    if not self.workspace_url:
                        self.workspace_url = ctx.apiUrl().get()
                    if not self.databricks_token:
                        self.databricks_token = ctx.apiToken().get()
                except Exception as e:
                    pass
        
        if self.mode == "external":
            if dbutils:
                try:
                    self.external_api_key = dbutils.secrets.get(scope="health_claims_scope", key="external_llm_api_key")
                except Exception as e:
                    print(f"Warning: Could not get secret. Ensure health_claims_scope is setup. {e}")
                    self.external_api_key = os.environ.get("EXTERNAL_LLM_API_KEY", "")
            else:
                self.external_api_key = os.environ.get("EXTERNAL_LLM_API_KEY", "")

    def generate(self, prompt, system_prompt="You are a helpful assistant.", max_tokens=1000):
        if self.mode == "databricks":
            return self._call_databricks_foundation_model(prompt, system_prompt, max_tokens)
        else:
            return self._call_external_model(prompt, system_prompt, max_tokens)

    def _call_databricks_foundation_model(self, prompt, system_prompt, max_tokens):
        # We use the REST API of the serving endpoint
        # If running inside databricks notebook, DATABRICKS_TOKEN and HOST might not be directly available in env
        # A common pattern is to use the context
        url = f"{self.workspace_url}/serving-endpoints/{self.model_name}/invocations"
        headers = {
            "Authorization": f"Bearer {self.databricks_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.1
        }
        
        # If token/url isn't set, this is a fallback for local testing that raises error
        if not self.workspace_url or not self.databricks_token:
            print("Warning: DATABRICKS_HOST or DATABRICKS_TOKEN missing. Trying to simulate via Langchain if installed.")
            # fallback for simulation
            return f"[Simulated Response for {self.model_name}]\nReceived prompt: {prompt[:50]}..."

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
        else:
            print(f"Error calling Databricks API: {response.text}")
            # Fallback
            return None

    def _call_external_model(self, prompt, system_prompt, max_tokens):
        # Simple simulated abstraction for external model (e.g. Claude)
        print(f"Calling external model (e.g., Claude/OpenAI) using provided API key.")
        # In a real scenario, use Anthropic or OpenAI SDK here.
        # This is a placeholder since we don't know the exact external provider.
        return f"[External Model Output] Response to: {prompt[:50]}..."

# Singleton instance for easy import
llm = LLMClient()
