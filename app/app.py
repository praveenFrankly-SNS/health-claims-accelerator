import streamlit as st
import pandas as pd
import json
import time

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

# In-memory mock audit trail for demo without DB
if 'audit_trail' not in st.session_state:
    st.session_state.audit_trail = []

@st.cache_data
def load_claims_data():
    if has_databricks_sql and "DATABRICKS_HOST" in os.environ:
        try:
            connection = sql.connect(
                server_hostname=os.environ["DATABRICKS_HOST"],
                http_path=os.environ["DATABRICKS_HTTP_PATH"],
                access_token=os.environ["DATABRICKS_TOKEN"]
            )
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM health_claims_dev.claims.vw_claims_dashboard LIMIT 50")
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                return pd.DataFrame(rows, columns=columns)
        except Exception as e:
            st.error(f"Error connecting to Databricks: {e}")
            return pd.DataFrame()
    else:
        # Mock data if not connected
        return pd.DataFrame({
            "claim_id": ["CLM-2026-10000", "CLM-2026-10001", "CLM-2026-10002"],
            "pipeline_status": ["COMPLETED", "HALTED_INCOMPLETE", "COMPLETED"],
            "claimant_name": ["Patient 0", "Patient 1", "Patient 2"],
            "diagnosis": ["K35.80", "A90", "J18.9"],
            "fraud_score": [0.15, 0.82, 0.20],
            "fraud_confidence": ["LOW", "HIGH", "LOW"],
            "coverage_status": ["COVERED", "NEEDS_REVIEW", "PARTIAL"],
            "reserve_amount": [45000, 0, 98000],
            "assigned_adjuster": ["STP_ELIGIBLE", "SENIOR_FIELD_ADJUSTER", "STAFF_ADJUSTER"]
        })

def record_decision(claim_id, decision, reason):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    user = "Adjuster_Jane"
    
    st.session_state.audit_trail.insert(0, {
        "timestamp": timestamp,
        "claim_id": claim_id,
        "user": user,
        "action": decision,
        "reason": reason
    })
    
    if has_databricks_sql and "DATABRICKS_HOST" in os.environ:
        try:
            connection = sql.connect(
                server_hostname=os.environ["DATABRICKS_HOST"],
                http_path=os.environ["DATABRICKS_HTTP_PATH"],
                access_token=os.environ["DATABRICKS_TOKEN"]
            )
            with connection.cursor() as cursor:
                # Write to audit table
                query = f"""
                INSERT INTO health_claims_dev.audit.setup_log (event, catalog, schema, env, timestamp, run_by)
                VALUES ('ADJUSTER_{decision}', 'health_claims_dev', 'claims', 'dev', '{timestamp}', '{user}')
                """
                cursor.execute(query)
        except Exception as e:
            st.error(f"Failed to write to audit log: {e}")

df = load_claims_data()

tab1, tab2 = st.tabs(["Claims Queue", "Audit Trail"])

with tab1:
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
            reason = st.text_input("Reason / Notes (Optional)")
            
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            with col_btn1:
                if st.button("Approve (Override)", type="primary"):
                    record_decision(selected_claim, "APPROVE", reason)
                    st.success(f"Claim {selected_claim} Approved.")
            with col_btn2:
                if st.button("Deny"):
                    record_decision(selected_claim, "DENY", reason)
                    st.error(f"Claim {selected_claim} Denied.")
            with col_btn3:
                if st.button("Send to Investigation"):
                    record_decision(selected_claim, "INVESTIGATE", reason)
                    st.warning(f"Claim {selected_claim} flagged for Investigation.")

with tab2:
    st.subheader("Immutable Audit Trail")
    if len(st.session_state.audit_trail) == 0:
        st.info("No decisions recorded in this session.")
    else:
        st.dataframe(pd.DataFrame(st.session_state.audit_trail), use_container_width=True)
