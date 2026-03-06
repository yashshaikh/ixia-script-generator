import streamlit as st

# --- UI Header ---
st.set_page_config(page_title="Ixia Script Generator", page_icon="⚡")
st.title("⚡ Ixia Universal Script Generator")
st.markdown("Generates a robust, version-independent verification script.")

# --- User Inputs ---
with st.sidebar:
    st.header("1. Connection Details")
    vm_ip = st.text_input("Ixia VM IP", value="10.244.134.26")
    port = st.number_input("Rest Port", value=8080)
    
    st.header("2. Traffic Details")
    target_flow = st.text_input("Target Flow Name", value="Traffic Item 2")

    st.header("3. Expectations")
    skip_dur = st.checkbox("Skip Loss Duration Check", value=True)
    if not skip_dur:
        max_dur = st.number_input("Max Loss Duration (ms)", value=0)
    else:
        max_dur = -1
        
    max_pct = st.number_input("Max Loss Percentage (%)", value=0.0, format="%.4f")

# --- The Validated Script Template ---
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
TARGET_FLOW = '{target_flow}'
LIMIT_LOSS_DURATION = {max_dur}
LIMIT_LOSS_PERCENT = {max_pct}

def run_ixia_verification():
    try:
        # Initialize session with SSL bypass
        session = SessionAssistant(IpAddress=IXIA_IP, RestPort=PORT, VerifyCertificates=False)
        ixnetwork = session.Ixnetwork
        print(f"Connected to {{IXIA_IP}}:{{PORT}}.")

        # Find the Statistics View
        ti_view = ixnetwork.Statistics.View.find(Caption='Traffic Item Statistics')
        if not ti_view:
            print("Error: Could not find 'Traffic Item Statistics' view.")
            sys.exit(1)

        ti_view.Refresh()
        print("Monitoring traffic for 10 seconds...")
        time.sleep(10)
        ti_view.Refresh()
        
        # Pull raw headers and data values
        headers = ti_view.Data.ColumnCaptions
        stats_data = ti_view.Data.PageValues
        
        if not stats_data or not stats_data[0]:
            print("Error: No statistics data found.")
            sys.exit(1)
            
        # FIX: Handle double-nested list structure found in lab
        row = stats_data[0][0] 
        
        # Map column names to their numerical indices
        name_idx = headers.index('Traffic Item')
        tx_idx = headers.index('Tx Frames')
        rx_idx = headers.index('Rx Frames')
        loss_pct_idx = headers.index('Loss %')
        
        flow_name = row[name_idx]
        
        if flow_name == TARGET_FLOW:
            tx_frames = row[tx_idx]
            rx_frames = row[rx_idx]
            loss_pct = float(row[loss_pct_idx])
            
            print(f"\\n--- Flow Found: {{flow_name}} ---")
            print(f"Tx Frames: {{tx_frames}}")
            print(f"Rx Frames: {{rx_frames}}")
            print(f"Loss Percent: {{loss_pct}}%")

            # Verification Logic
            status = "PASS"
            # Only fail if not explicitly testing functionality
            if LIMIT_LOSS_PERCENT != 100.0: 
                if rx_frames == 0 or loss_pct > LIMIT_LOSS_PERCENT:
                    status = "FAIL"
            
            if LIMIT_LOSS_DURATION != -1:
                loss_dur_idx = headers.index('Loss Duration (ms)')
                loss_dur = float(row[loss_dur_idx])
                print(f"Loss Duration: {{loss_dur}}ms")
                if loss_dur > LIMIT_LOSS_DURATION:
                    status = "FAIL"

            print(f"\\nFINAL VERDICT: {{status}}")
            sys.exit(0) if status == "PASS" else sys.exit(1)
        else:
            print(f"Warning: Found '{{flow_name}}' but expected '{{TARGET_FLOW}}'.")
            sys.exit(1)

    except Exception as e:
        print(f"Error during execution: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    run_ixia_verification()
"""

st.subheader("Validated Generator Output")
st.code(script_template, language='python')
