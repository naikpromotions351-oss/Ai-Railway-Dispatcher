import streamlit as st
import pandas as pd
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AI Railway Dispatcher - Train Schedules",
    page_icon="🎫",
    layout="centered"
)

# --- LEAD LOGIC / DATA LOADERS ---
@st.cache_data
def load_data():
    """Loads datasets efficiently with caching to prevent disk-re-reading on every rerun."""
    try:
        trains = pd.read_csv("trains.csv")
        tracks = pd.read_csv("tracks.csv")
        schedules = pd.read_csv("schedules.csv")
        
        # Clean string spaces for accurate matching
        for df in [trains, tracks, schedules]:
            for col in df.select_dtypes(include='object').columns:
                df[col] = df[col].astype(str).str.strip()
        return trains, tracks, schedules
    except FileNotFoundError as e:
        st.error(f"Missing dataset file: {e.filename}. Ensure trains.csv, tracks.csv, and schedules.csv are in the same folder.")
        return None, None, None

trains_df, tracks_df, schedules_df = load_data()

def query_schedule_engine(user_query):
    """
    An efficient rule-based search engine that scans the datasets 
    based on keywords in the user's prompt.
    """
    if trains_df is None or tracks_df is None or schedules_df is None:
        return "System error: Datasets not loaded."
        
    query_lower = user_query.lower()
    
    # 1. Search by Segment ID or Segment Name
    for _, track in tracks_df.iterrows():
        if track['segment_id'].lower() in query_lower or track['segment_name'].lower() in query_lower:
            seg_id = track['segment_id']
            seg_name = track['segment_name']
            
            # Find all schedules on this track segment
            matches = schedules_df[schedules_df['segment_id'] == seg_id]
            if matches.empty:
                return f"Track **{seg_id} ({seg_name})** is currently clear. No trains scheduled."
            
            # Merge to get Train Names
            merged = matches.merge(trains_df, on='train_id', how='left')
            response = f"### Schedule for {seg_name} ({seg_id}):\n"
            for _, row in merged.iterrows():
                response += f"- **{row['scheduled_arrival']} - {row['scheduled_departure']}**: {row['train_name']} ({row['train_id']}) | Type: {row['train_type']}\n"
            return response

    # 2. Search by Train ID or Train Name
    for _, train in trains_df.iterrows():
        if train['train_id'].lower() in query_lower or train['train_name'].lower() in query_lower:
            t_id = train['train_id']
            t_name = train['train_name']
            
            # Find where this train is scheduled
            matches = schedules_df[schedules_df['train_id'] == t_id]
            if matches.empty:
                return f"Train **{t_name} ({t_id})** has no active schedules recorded today."
                
            # Merge to get Track Segment Names
            merged = matches.merge(tracks_df, on='segment_id', how='left')
            response = f"### Schedule itinerary for {t_name} ({t_id}):\n"
            for _, row in merged.iterrows():
                response += f"- **Track {row['segment_id']}** ({row['segment_name']}) | Arrives: {row['scheduled_arrival']} | Departs: {row['scheduled_departure']}\n"
            return response

    # Default fallback message if no entities match
    return ("🤖 *I couldn't isolate a specific Train ID (e.g., TRN_1144) or Track Segment (e.g., SEG_105) in your message.*\n\n"
            "Try asking me:\n"
            "* *'What is the schedule for SEG_105?'*\n"
            "* *'Where is TRN_1144 scheduled to be?'*\n"
            "* *'Show schedule for Express Aurora'*")

# --- USER INTERFACE DESIGN ---
st.title("🎫 Train Schedule Assistant")
st.markdown("Welcome to the Dispatch Schedule Chatbot. Enter a train name, code, or track segment ID below to fetch live itineraries.")

# Initialize chatbot conversation state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your schedule assistant. Ask me about any train (e.g., *Express Aurora*) or track sector (e.g., *SEG_105*) to see timelines."}
    ]

# Display history of chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user chat interaction input
if user_prompt := st.chat_input("Ask about trains or track segments..."):
    # Display user input inside the chat box
    with st.chat_message("user"):
        st.markdown(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    
    # Generate response using backend engine
    bot_reply = query_schedule_engine(user_prompt)
    
    # Display assistant response inside the chat box
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
