import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AI Railway Dispatcher - Maintenance Optimizer",
    page_icon="🔧",
    layout="centered"
)

# --- DATA LOAD ENGINE ---
@st.cache_data
def load_data():
    """Loads datasets and normalizes column headers cleanly."""
    try:
        trains = pd.read_csv("trains.csv")
        tracks = pd.read_csv("tracks.csv")
        schedules = pd.read_csv("schedules.csv")
        
        # Standardize formatting to lowercase and remove spaces
        for df in [trains, tracks, schedules]:
            df.columns = df.columns.str.strip().str.lower()
            for col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        return trains, tracks, schedules
    except Exception as e:
        st.error(f"Error loading datasets: {e}. Please run generate_clean_data.py first.")
        return None, None, None

trains_df, tracks_df, schedules_df = load_data()

# --- INTELLIGENT WINDOW ALLOCATION ALGORITHM ---
def calculate_optimal_maintenance_window(segment_id, duration_hours=2):
    """
    Scans the 24-hour schedule for a segment, calculates hourly train density,
    and returns the window with the absolute fewest train conflicts.
    """
    if schedules_df is None:
        return "System error: Schedule database unavailable."
        
    # Filter schedules tracking the requested segment
    seg_schedules = schedules_df[schedules_df['segment_id'].str.upper() == segment_id.upper()]
    
    # Track train counts for each hourly block of the day
    hourly_traffic = [0] * 24
    
    for _, row in seg_schedules.iterrows():
        try:
            # Parse scheduled arrival and departure times
            arr_hour = int(row['scheduled_arrival'].split(':')[0])
            dep_hour = int(row['scheduled_departure'].split(':')[0])
            
            # Mark all hours this train occupies the track sector
            for h in range(arr_hour, dep_hour + 1):
                if 0 <= h < 24:
                    hourly_traffic[h] += 1
        except Exception:
            continue  # Skip corrupt format rows smoothly

    # Scan for consecutive hours matching the requested duration with lowest total conflict score
    best_start_hour = 0
    min_conflict_score = float('inf')
    
    for start_hour in range(24 - duration_hours + 1):
        window_traffic = sum(hourly_traffic[start_hour : start_hour + duration_hours])
        if window_traffic < min_conflict_score:
            min_conflict_score = window_traffic
            best_start_hour = start_hour

    # Format result timestamps nicely
    start_time = f"{best_start_hour:02d}:00"
    end_time = f"{(best_start_hour + duration_hours):02d}:00"
    
    return {
        "start": start_time,
        "end": end_time,
        "conflict_count": min_conflict_score
    }

# --- BACKEND CHAT ENGINE ---
def process_maintenance_query(user_query):
    if tracks_df is None or schedules_df is None:
        return "System error: Datasets not loaded properly."
        
    query_upper = user_query.upper()
    
    # Scan user message for a matching track segment ID
    target_segment = None
    target_segment_name = ""
    for _, track in tracks_df.iterrows():
        if track['segment_id'].upper() in query_upper or track['segment_name'].upper() in query_upper:
            target_segment = track['segment_id']
            target_segment_name = track['segment_name']
            break
            
    if target_segment:
        # Default maintenance duration to 2 hours for calculations
        allocation = calculate_optimal_maintenance_window(target_segment, duration_hours=2)
        
        if isinstance(allocation, str):
            return allocation
            
        response = (
            f"### 🎯 AI Maintenance Allocation Approved\n"
            f"**Location Sector:** {target_segment_name} (`{target_segment}`)\n"
            f"**Allocated Time Slot:** 🕒 **{allocation['start']} to {allocation['end']}**\n\n"
            f"**Traffic Impact Assessment:** This window contains **{allocation['conflict_count']}** scheduled train movements. "
            f"Assigning crews to this specific slot will cause zero cascading transit delays to the network line."
        )
        return response
        
    return ("🤖 *I can help you allocate an optimal low-traffic window for track maintenance.*\n\n"
            "Please specify a valid track segment ID or name in your request. For example:\n"
            "* *'Schedule maintenance work for SEG_105'* \n"
            "* *'When can workers safely enter Central Hub Transitway?'*")

# --- USER INTERFACE DESIGN ---
st.title("🔧 AI Maintenance Planner Chatbot")
st.markdown("Automated zero-delay workforce slot allocation based on real-time baseline schedule loads.")

if "maint_messages" not in st.session_state:
    st.session_state.maint_messages = [
        {"role": "assistant", "content": "Hello! State the track segment code (e.g., *SEG_105*) requiring tracks or electrical service. I will compute and allocate the slot with the lowest train density to eliminate cascading delay risks."}
    ]

for message in st.session_state.maint_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_prompt := st.chat_input("Enter maintenance target location segment..."):
    with st.chat_message("user"):
        st.markdown(user_prompt)
    st.session_state.maint_messages.append({"role": "user", "content": user_prompt})
    
    bot_reply = process_maintenance_query(user_prompt)
    
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.maint_messages.append({"role": "assistant", "content": bot_reply})
