import streamlit as st

# --- UI Header ---
st.set_page_config(page_title="Ixia Multi-Flow Generator", page_icon="⚡")
st.title("⚡ Ixia Universal Multi-Flow Generator")
st.markdown("Generates a version-independent script for any number of traffic items.")

# --- User Inputs ---
with st.sidebar:
    st.header("1. Connection Details")
    vm_ip = st.text_input("Ixia VM IP", value="10.244.134.26")
    port = st.number_input("Rest Port", value=8080)
    
    st.header("2. Traffic Details")
    # Users can now input any number of flows
    num_flows = st.number_input("How many flows to check?", min_value=1, max_value=100, value=1)
    
    flow_names = []
    for i in range(int(num_flows)):
        name = st.text_input(f"Flow {i+1} Name", value=f"Traffic Item {i+2}")
        flow_names.append(name)

    st.header("3. Expectations")
    skip_dur = st.checkbox("Skip Loss Duration Check", value=True)
    max_dur = -1 if skip_dur else st.number_input("Max Loss Duration (ms)", value=0)
    max_pct = st.number_input("Max Loss Percentage (%)", value=0.0, format="%.4f")

# --- The Multi-Flow Script Template ---
script_template = f"""
from ixnetwork_restpy import SessionAssistant
import time
import sys
import urllib3

# Silence SSL warnings for lab environments
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Configuration ---
IXIA_IP = '{vm_ip}'
PORT = {port}
FLOWS_TO_CHECK = {flow_names}
LIMIT_LOSS_DURATION = {max_dur}
LIMIT_LOSS_PERCENT = {max_pct}

def run_ixia_verification():
    try:
        session = SessionAssistant(IpAddress=IXIA_IP, RestPort=PORT, VerifyCertificates=False)
        ixnetwork = session.Ixnetwork
        print(f"Connected to {{IXIA_IP}}:{{PORT}}.")

        ti_view = ixnetwork.Statistics.View.find(Caption='Traffic Item Statistics')
        ti_view.Refresh()
        print(f"Monitoring {{len(FLOWS_TO_CHECK)}} flow(s) for 10 seconds...")
        time.sleep(10)
        ti_view.Refresh()
        
        headers = ti_view.Data.ColumnCaptions
        stats_data = ti_view.Data.PageValues
        
        if not stats_data or not stats_data[0]:
            print("Error: No statistics data found.")
            sys.exit(1)
            
        # The environment returns a list of rows inside stats_data[0]
        rows = stats_data[0] 
        
        # Map column names to their numerical indices
        idx_map = {{
            'name': headers.index('Traffic Item'),
            'tx': headers.index('Tx Frames'),
            'rx': headers.index('Rx Frames'),
            'loss_pct': headers.index('Loss %')
        }}
        
        overall_status = "PASS"
        found_flows = []

        for row in rows:
            flow_name = row[idx_map['name']]
            
            if flow_name in FLOWS_TO_CHECK:
                found_flows.append(flow_name)
                tx_frames = row[idx_map['tx']]
                rx_frames = row[idx_map['rx']]
                loss_pct = float(row[idx_map['loss_pct']])
                
                print(f"\\n--- Flow: {{flow_name}} ---")
                print(f"Tx Frames: {{tx_frames}}")
                print(f"Rx Frames: {{rx_frames}}")
                print(f"Loss Percent: {{loss_pct}}%")

                # Logic: Fail if 100% loss is not intended or if threshold exceeded
                if LIMIT_LOSS_PERCENT != 100.0:
                    if rx_frames == 0 or loss_pct > LIMIT_LOSS_PERCENT:
                        overall_status = "FAIL"
                
                if LIMIT_LOSS_DURATION != -1:
                    loss_dur_idx = headers.index('Loss Duration (ms)')
                    loss_dur = float(row[loss_dur_idx])
                    print(f"Loss Duration: {{loss_dur}}ms")
                    if loss_dur > LIMIT_LOSS_DURATION:
                        overall_status = "FAIL"

        # Check if any requested flows were missing from the Ixia table
        missing = set(FLOWS_TO_CHECK) - set(found_flows)
        if missing:
            print(f"\\nWarning: Missing flows from Ixia statistics: {{list(missing)}}")
            overall_status = "FAIL"

        print(f"\\nFINAL VERDICT: {{overall_status}}")
        sys.exit(0) if overall_status == "PASS" else sys.exit(1)

    except Exception as e:
        print(f"Error during execution: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    run_ixia_verification()
"""

st.subheader("Generated Multi-Flow Script")
st.code(script_template, language='python')
