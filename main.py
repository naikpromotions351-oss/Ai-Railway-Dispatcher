import streamlit as st
import importlib.util
import os

# --- PAGE CONFIGURATION & JURY BRANDING ---
st.set_page_config(
    page_title="Team Phoenix - AI Block Planner",
    page_icon="🚂",
    layout="centered"
)

# --- SIH JURY SIDEBAR BRANDING PANEL ---
# Removed the unsupported parameter to fix the crash completely
st.sidebar.title("🚀 Smart India Hackathon 2026")
st.sidebar.markdown("**Team Name:** Phoenix")
st.sidebar.markdown("**Problem Statement ID:** SIH26027")
st.sidebar.markdown("**Project Title:** AI-Powered Automatic Block Planning")
st.sidebar.markdown("---")

st.sidebar.subheader("🎯 Navigation Control Hub")
app_choice = st.sidebar.selectbox(
    "Select Sub-System Module:",
    ["Module 1: Baseline Schedule Tracker", 
     "Module 2: Maintenance Block Optimizer", 
     "Module 3: Emergency Dispatch & Signal Hub"]
)

# --- RUN CHATBOT SUB-SYSTEMS SAFELY WITHOUT ALTERING ORIGINALS ---
def run_module(file_name):
    """Executes the targeted app file logic directly within the main framework."""
    if os.path.exists(file_name):
        try:
            with open(file_name, "r", encoding="utf-8") as f:
                code_content = f.read()
            exec(code_content, globals())
        except Exception as e:
            st.error(f"Execution handling error on {file_name}: {e}")
    else:
        st.error(f"System Error: `{file_name}` could not be located in the current workspace directory.")

# --- NAVIGATION ROUTING LOGIC ---
if app_choice == "Module 1: Baseline Schedule Tracker":
    run_module("app1.py")

elif app_choice == "Module 2: Maintenance Block Optimizer":
    run_module("app2.py")

elif app_choice == "Module 3: Emergency Dispatch & Signal Hub":
    run_module("app3.py")
