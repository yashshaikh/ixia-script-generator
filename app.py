import streamlit as st

# --- UI Header ---
st.set_page_config(page_title="Ixia Multi-Flow Generator", page_icon="⚡")
st.title("⚡ Ixia Universal Multi-Flow Generator")
st.markdown("Generates a version-independent script for multiple traffic items.")

# --- User Inputs ---
with st.sidebar:
    st.header("1. Connection Details")
    vm_ip = st.text_input("Ixia VM IP", value="10.244.134.26")
    port = st.number_input("Rest Port", value=8080)
    
    st.header("2. Traffic Details")
    num_flows = st.number_input("Number of Flows", min_value=1, max_value=20, value=1)
    
    flow_names = []
    for i in range(int(num_flows)):
        name = st.text_input(f"Flow {i+1} Name", value=f"Traffic Item {i+2}")
        flow_names.append(name)

    st.header("3. Expectations")
    skip_dur = st.checkbox("Skip Loss Duration Check", value=True)
    if not skip_dur:
        max_dur = st.number_input("Max Loss Duration (ms)", value=0)
    else:
        max_dur = -1
        
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
        print("Monitoring traffic for 10 seconds...")
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
        name_idx = headers.index('Traffic Item')
        tx_idx = headers.index('Tx Frames')
        rx_idx = headers.index('Rx Frames')
        loss_pct_idx = headers.index('Loss %')
        
        overall_status = "PASS"
        found_count = 0

        for row in rows:
            flow_name = row[name_idx]
            
            if flow_name in FLOWS_TO_CHECK:
                found_count += 1
                tx_frames = row[tx_idx]
                rx_frames = row[rx_idx]
                loss_pct = float(row[loss_pct_idx])
                
                print(f"\\n--- Flow Found: {{flow_name}} ---")
                print(f"Tx Frames: {{tx_frames}}")
                print(f"Rx Frames: {{rx_frames}}")
                print(f"Loss Percent: {{loss_pct}}%")

                # Verification Logic
                # If checking functionality with 100% loss, set Limit to 100.0
                if LIMIT_LOSS_PERCENT != 100.0:
                    if rx_frames == 0 or loss_pct > LIMIT_LOSS_PERCENT:
                        overall_status = "FAIL"
                
                if LIMIT_LOSS_DURATION != -1:
                    loss_dur_idx = headers.index('Loss Duration (ms)')
                    loss_dur = float(row[loss_dur_idx])
                    print(f"Loss Duration: {{loss_dur}}ms")
                    if loss_dur > LIMIT_LOSS_DURATION:
                        overall_status = "FAIL"

        if found_count < len(FLOWS_TO_CHECK):
            print(f"\\nWarning: Only found {{found_count}}/{{len(FLOWS_TO_CHECK)}} target flows.")
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
