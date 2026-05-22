import streamlit as st
import pandas as pd
import json

# Try to import databricks.sql to connect to the SQL warehouse
try:
    from databricks import sql
    import os
    has_databricks_sql = True
except ImportError:
    has_databricks_sql = False

st.set_page_config(page_title="Health Claims Adjuster Dashboard", layout="wide")

st.title("🏥 Health Claims Adjuster Dashboard")
st.markdown("Review AI-orchestrated claims from the Gold Delta Table.")

@st.cache_data
def load_claims_data():
    if has_databricks_sql and "DATABRICKS_HOST" in os.environ:
        # Real connection
        try:
            connection = sql.connect(
                server_hostname=os.environ["DATABRICKS_HOST"],
                http_path=os.environ["DATABRICKS_HTTP_PATH"],
                access_token=os.environ["DATABRICKS_TOKEN"]
            )
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM main.health_claims_dev.vw_claims_dashboard LIMIT 50")
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                return pd.DataFrame(rows, columns=columns)
        except Exception as e:
            st.error(f"Error connecting to Databricks: {e}")
            return pd.DataFrame()
    else:
        # Mock data if not connected
        return pd.DataFrame({
            "claim_id": ["CLM-2026-10000", "CLM-2026-10001"],
            "pipeline_status": ["COMPLETED", "HALTED_INCOMPLETE"],
            "claimant_name": ["Patient 0", "Patient 1"],
            "diagnosis": ["K35.80", "A90"],
            "fraud_score": [0.15, 0.82],
            "fraud_confidence": ["LOW", "HIGH"],
            "coverage_status": ["COVERED", "NEEDS_REVIEW"],
            "reserve_amount": [45000, 0],
            "assigned_adjuster": ["STP_ELIGIBLE", "SENIOR_FIELD_ADJUSTER"]
        })

df = load_claims_data()

if df.empty:
    st.warning("No claims data available or connection failed.")
else:
    st.dataframe(df, use_container_width=True)
    
    st.subheader("Deep Dive")
    selected_claim = st.selectbox("Select a Claim ID for details", df['claim_id'].tolist())
    
    if selected_claim:
        claim_details = df[df['claim_id'] == selected_claim].iloc[0]
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Fraud Score", f"{claim_details['fraud_score']}", delta=claim_details['fraud_confidence'], delta_color="inverse")
        with col2:
            st.metric("Reserve Estimate", f"₹{claim_details['reserve_amount']}")
        with col3:
            st.metric("Adjuster Tier", claim_details['assigned_adjuster'])
            
        st.write("### Review Decision")
        st.button("Approve (Override)")
        st.button("Deny")
        st.button("Send to Investigation")
