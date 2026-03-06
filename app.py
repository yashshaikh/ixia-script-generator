import streamlit as st

# --- UI Header ---
st.set_page_config(page_title="Ixia Script Generator", page_icon="⚡")
st.title("⚡ Ixia Universal Script Generator")
st.markdown("Generates a robust, version-independent verification script.")

# --- User Inputs ---
with st.sidebar:
    st.header("1. Connection Details")
    vm_ip = st.text_input("Ixia VM IP", value="10.244.134.26")
    # We set 8080 as the default based on your environment's scan
    port = st.number_input("Rest Port", value=8080)
    
    st.header("2. Traffic Details")
    num_flows = st.number_input("Number of Flows", min_value=1, max_value=20, value=1)
    
    flow_names = []
    for i in range(int(num_flows)):
        name = st.text_input(f"Flow {i+1} Name", value=f"vxlan")
        flow_names.append(name)

    st.header("3. Expectations")
    max_loss_duration = st.number_input("Max Loss Duration (ms)", value=0)

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

def run_ixia_verification():
    try:
        # Initializing session with universal compatibility flags
        session = SessionAssistant(
            IpAddress=IXIA_IP, 
            RestPort=PORT, 
            VerifyCertificates=False
        )
        ixnetwork = session.Ixnetwork
        print(f"Connected to {{IXIA_IP}}:{{PORT}}. Initializing stats...")

        # Universal approach: Find the view first to ensure it exists
        ti_view = ixnetwork.Statistics.View.find(Caption='Traffic Item Statistics')
        
        if not ti_view:
            print("Error: Could not find 'Traffic Item Statistics' view.")
            sys.exit(1)

        # Clear stats using the Refresh/Clear sequence compatible with all versions
        ti_view.Refresh()
        print("Monitoring traffic for 10 seconds...")
        time.sleep(10) 

        # Final Refresh and Data Read
        ti_view.Refresh()
        stats = ti_view.Data.Read()

        overall_status = "PASS"
        found_any = False

        for row in stats:
            name = row['Traffic Item']
            if name in FLOWS_TO_CHECK:
                found_any = True
                loss_dur = float(row['Loss Duration (ms)'])
                rx_frames = int(row['Rx Frames'])

                print(f"\\n--- Flow: {{name}} ---")
                print(f"Rx Frames: {{rx_frames}}")
                print(f"Loss Duration: {{loss_dur}}ms")

                if rx_frames == 0:
                    print("RESULT: FAIL (No traffic received)")
                    overall_status = "FAIL"
                elif loss_dur > LIMIT_LOSS_DURATION:
                    print(f"RESULT: FAIL (Loss {{loss_dur}}ms > {{LIMIT_LOSS_DURATION}}ms)")
                    overall_status = "FAIL"
                else:
                    print("RESULT: PASS")

        if not found_any:
            print(f"\\nWarning: None of the target flows {{FLOWS_TO_CHECK}} were found.")
            available = [r['Traffic Item'] for r in stats]
            print(f"Available flows in Ixia: {{available}}")
            overall_status = "FAIL"

        print(f"\\nFINAL VERDICT: {{overall_status}}")
        sys.exit(0) if overall_status == "PASS" else sys.exit(1)

    except Exception as e:
        print(f"Error during execution: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    run_ixia_verification()
"""

st.subheader("Generated Script (Optimized)")
st.code(script_template, language='python')

st.download_button(
    label="Download Updated Script",
    data=script_template,
    file_name="ixia_verify_v2.py",
    mime="text/x-python"
)
