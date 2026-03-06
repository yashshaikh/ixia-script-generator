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
    num_flows = st.number_input("Number of Flows", min_value=1, max_value=20, value=1)
    
    flow_names = []
    for i in range(int(num_flows)):
        name = st.text_input(f"Flow {i+1} Name", value=f"vxlan")
        flow_names.append(name)

    st.header("3. Expectations")
    # Checkbox to skip Duration check
    skip_duration = st.checkbox("Skip Loss Duration Check", value=False)
    if not skip_duration:
        max_loss_duration = st.number_input("Max Loss Duration (ms) allowed", value=0)
    else:
        max_loss_duration = -1 # Flag to skip in script
        
    # Restored Loss Percentage field
    max_loss_percent = st.number_input("Max Loss Percentage (%) allowed", value=0.0, format="%.4f")

# --- The Updated Script Template ---
script_template = f"""
from ixnetwork_restpy import SessionAssistant
import time
import sys
import urllib3

# Silence SSL warnings common in lab environments
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Configuration ---
IXIA_IP = '{vm_ip}'
PORT = {port}
FLOWS_TO_CHECK = {flow_names}
LIMIT_LOSS_DURATION = {max_loss_duration}
LIMIT_LOSS_PERCENT = {max_loss_percent}

def run_ixia_verification():
    try:
        session = SessionAssistant(
            IpAddress=IXIA_IP, 
            RestPort=PORT, 
            VerifyCertificates=False
        )
        ixnetwork = session.Ixnetwork
        print(f"Connected to {{IXIA_IP}}:{{PORT}}.")

        ti_view = ixnetwork.Statistics.View.find(Caption='Traffic Item Statistics')
        if not ti_view:
            print("Error: Could not find 'Traffic Item Statistics' view.")
            sys.exit(1)

        ti_view.Refresh()
        print("Monitoring traffic for 10 seconds...")
        time.sleep(10) 

        ti_view.Refresh()
        stats = ti_view.Data.Read()

        overall_status = "PASS"
        found_any = False

        for row in stats:
            name = row['Traffic Item']
            if name in FLOWS_TO_CHECK:
                found_any = True
                loss_dur = float(row['Loss Duration (ms)'])
                loss_pct = float(row['Loss %'])
                rx_frames = int(row['Rx Frames'])

                print(f"\\n--- Flow: {{name}} ---")
                print(f"Rx Frames: {{rx_frames}}")
                
                # Logic for skipping/checking Duration
                if LIMIT_LOSS_DURATION != -1:
                    print(f"Loss Duration: {{loss_dur}}ms (Limit: {{LIMIT_LOSS_DURATION}}ms)")
                
                print(f"Loss Percent: {{loss_pct}}% (Limit: {{LIMIT_LOSS_PERCENT}}%)")

                # Validation Logic
                if rx_frames == 0:
                    print("RESULT: FAIL (No traffic)")
                    overall_status = "FAIL"
                
                # Only check duration if not skipped
                if LIMIT_LOSS_DURATION != -1 and loss_dur > LIMIT_LOSS_DURATION:
                    print("RESULT: FAIL (Duration exceeded)")
                    overall_status = "FAIL"
                
                # Check percentage
                if loss_pct > LIMIT_LOSS_PERCENT:
                    print("RESULT: FAIL (Percentage exceeded)")
                    overall_status = "FAIL"
                
                if overall_status == "PASS":
                    print("RESULT: PASS")

        if not found_any:
            print(f"\\nWarning: Target flows {{FLOWS_TO_CHECK}} not found.")
            available = [r['Traffic Item'] for r in stats]
            print(f"Available flows: {{available}}")
            overall_status = "FAIL"

        print(f"\\nFINAL VERDICT: {{overall_status}}")
        sys.exit(0) if overall_status == "PASS" else sys.exit(1)

    except Exception as e:
        print(f"Error: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    run_ixia_verification()
"""

st.subheader("Generated Script")
st.code(script_template, language='python')

st.download_button(
    label="Download Updated Script",
    data=script_template,
    file_name="ixia_verify_v3.py",
    mime="text/x-python"
)
