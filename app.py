import streamlit as st

# --- UI Header ---
st.set_page_config(page_title="Ixia Script Generator", page_icon="📝")
st.title("🛠️ Ixia Verification Script Generator")
st.markdown("Enter your test parameters to generate a custom Python validation script.")

# --- User Inputs ---
with st.sidebar:
    st.header("1. Connection Details")
    vm_ip = st.text_input("Ixia VM IP", value="10.244.134.26")
    
    st.header("2. Traffic Details")
    num_flows = st.number_input("Number of Flows", min_value=1, max_value=20, value=1)
    
    flow_names = []
    for i in range(int(num_flows)):
        name = st.text_input(f"Flow {i+1} Name", value=f"VXLAN_FLOW_{i+1}")
        flow_names.append(name)

    st.header("3. Expectations (Pass/Fail)")
    max_loss_duration = st.number_input("Max Loss Duration (ms) allowed", value=0)
    max_loss_percent = st.number_input("Max Loss Percentage (%) allowed", value=0.0, format="%.4f")

# --- The Script Template ---
# This is what will be generated for the user
script_template = f"""
from ixnetwork_restpy import SessionAssistant
import time
import sys

# --- Generated Configuration ---
IXIA_IP = '{vm_ip}'
FLOWS_TO_CHECK = {flow_names}
LIMIT_LOSS_DURATION = {max_loss_duration}
LIMIT_LOSS_PERCENT = {max_loss_percent}

def run_ixia_verification():
    try:
        # Connect to Ixia
        session = SessionAssistant(IpAddress=IXIA_IP, RestPort=443)
        ixnetwork = session.Ixnetwork
        print(f"Connected to {{IXIA_IP}}. Starting verification...")

        # Clear stats and wait for a clean monitoring window
        ixnetwork.Traffic.Statistics.Clear()
        print("Monitoring traffic for 10 seconds...")
        time.sleep(10) 

        # Get Statistics View
        view = ixnetwork.Statistics.View.find(Caption='Traffic Item Statistics')
        view.Refresh()
        stats = view.Data.Read()

        overall_status = "PASS"

        for row in stats:
            name = row['Traffic Item']
            if name in FLOWS_TO_CHECK:
                loss_dur = float(row['Loss Duration (ms)'])
                loss_pct = float(row['Loss %'])
                rx_frames = int(row['Rx Frames'])

                print(f"\\n--- Flow: {{name}} ---")
                print(f"Rx Frames: {{rx_frames}}")
                print(f"Loss Duration: {{loss_dur}}ms (Limit: {{LIMIT_LOSS_DURATION}}ms)")
                print(f"Loss Percent: {{loss_pct}}% (Limit: {{LIMIT_LOSS_PERCENT}}%)")

                # Validation Logic
                if rx_frames == 0:
                    print("RESULT: FAIL (No traffic received)")
                    overall_status = "FAIL"
                elif loss_dur > LIMIT_LOSS_DURATION or loss_pct > LIMIT_LOSS_PERCENT:
                    print("RESULT: FAIL (Threshold exceeded)")
                    overall_status = "FAIL"
                else:
                    print("RESULT: PASS")

        print(f"\\nFINAL VERDICT: {{overall_status}}")
        sys.exit(0) if overall_status == "PASS" else sys.exit(1)

    except Exception as e:
        print(f"Error: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    run_ixia_verification()
"""

# --- Display and Download ---
st.subheader("Generated Script")
st.code(script_template, language='python')

st.download_button(
    label="Download .py Script",
    data=script_template,
    file_name="ixia_verify.py",
    mime="text/x-python"
)
