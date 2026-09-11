import streamlit as st
import pandas as pd

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AI Railway Dispatcher - Emergency Response Room",
    page_icon="🚨",
    layout="centered"
)

# --- DATA LOAD ENGINE ---
@st.cache_data
def load_data():
    """Loads datasets seamlessly without any caching conflicts."""
    try:
        trains = pd.read_csv("trains.csv")
        tracks = pd.read_csv("tracks.csv")
        schedules = pd.read_csv("schedules.csv")
        
        # Standardize formatting to lowercase and remove hidden spacing bugs
        for df in [trains, tracks, schedules]:
            df.columns = df.columns.str.strip().str.lower()
            for col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        return trains, tracks, schedules
    except Exception as e:
        st.error(f"Error loading datasets: {e}. Please ensure trains.csv, tracks.csv, and schedules.csv exist.")
        return None, None, None

trains_df, tracks_df, schedules_df = load_data()

# --- EMERGENCY RE-ROUTING & SAFETY ENGINE ---
def handle_track_emergency(failed_segment_id):
    """
    Core Emergency Logic: Intercepts affected trains, routes passenger trains 
    with priority, halts goods trains, and issues priority dispatch signals to crews.
    """
    if trains_df is None or tracks_df is None or schedules_df is None:
        return "System error: Operational databases are offline."

    # Validate if segment exists
    failed_seg_upper = failed_segment_id.upper()
    track_row = tracks_df[tracks_df['segment_id'].str.upper() == failed_seg_upper]
    if track_row.empty:
        return f"❌ System Error: Segment ID `{failed_segment_id}` not recognized in infrastructure registry."
    
    failed_segment_name = track_row.iloc[0]['segment_name']
    failed_line_name = track_row.iloc[0]['line_name']
    
    # 1. Identify all trains scheduled to pass through the broken segment
    affected_schedules = schedules_df[schedules_df['segment_id'].str.upper() == failed_seg_upper]
    
    # 2. Check for alternate operational segments on the same main route line
    alternate_tracks = tracks_df[
        (tracks_df['line_name'].str.lower() == failed_line_name.lower()) & 
        (tracks_df['segment_id'].str.upper() != failed_seg_upper) & 
        (tracks_df['status'].str.lower() == 'operational')
    ]
    has_alternate_route = not alternate_tracks.empty
    alt_route_id = alternate_tracks.iloc[0]['segment_id'] if has_alternate_route else None
    alt_route_name = alternate_tracks.iloc[0]['segment_name'] if has_alternate_route else None

    # Compile the emergency dispatch strategy report
    passenger_alerts = []
    freight_alerts = []
    
    if not affected_schedules.empty:
        # Merge schedules with trains to process by type
        merged_schedules = affected_schedules.merge(trains_df, on='train_id', how='left')

        for _, row in merged_schedules.iterrows():
            t_id = row['train_id']
            t_name = row['train_name']
            t_type = row['train_type']
            
            if "passenger" in str(t_type).lower() or "high-speed" in str(t_type).lower():
                if has_alternate_route:
                    passenger_alerts.append(f"🔄 **{t_name} ({t_id})** -> **PASSENGER PRIORITY ROUTING DIVERSION**. Train dynamically rerouted via alternate track **{alt_route_name} ({alt_route_id})** to ensure passengers reach their destinations safely with minimal delay.")
                else:
                    passenger_alerts.append(f"🛑 **{t_name} ({t_id})** -> **CRITICAL HALT COMMAND SENT**. No alternative tracks available on {failed_line_name}. Train safely halted at the preceding station to protect passengers until maintenance is complete.")
            else:
                freight_alerts.append(f"🛑 **{t_name} ({t_id})** -> **EMERGENCY HOLD**. Halted safely on sidings to clear network layout and prioritize potential passenger train detours or emergency maintenance crews.")

    # Format the complete output message response
    output = f"### 🚨 AI Control Room Emergency Response Issued\n"
    output += f"**Critical Event:** Sensor detected a structural failure at **{failed_segment_name} ({failed_seg_upper})**.\n"
    output += f"**Emergency Status:** Track segment closed immediately.\n\n"
    
    # ⚙️ WORKER SIGNAL SECTION
    output += f"#### 📡 Crew Signal Dispatch:\n"
    output += (
        f"- ⚡ **[SIGNAL TRANSMITTED]** Emergency work order issued to **Zone Maintenance Crews**.\n"
        f"- 📍 **Target Sector:** {failed_segment_name} (`{failed_seg_upper}`) on the *{failed_line_name}*.\n"
        f"- ⚠️ **Directive:** Immediate track infrastructure repair required. Proceed with absolute priority to clear traffic blocks and resolve passenger hold states as quickly as possible.\n\n"
    )
    
    output += "#### 🎫 Passenger Train Interventions:\n"
    if passenger_alerts:
        for alert in passenger_alerts: output += f"- {alert}\n"
    elif affected_schedules.empty:
        output += "- No passenger trains are scheduled on this line during this block window. System secure.\n"
    else:
        output += "- No passenger trains are scheduled on this line during this block window.\n"
        
    output += "\n#### 📦 Freight (Goods) Train Interventions:\n"
    if freight_alerts:
        for alert in freight_alerts: output += f"- {alert}\n"
    elif affected_schedules.empty:
        output += "- No freight trains are scheduled on this line during this block window. System secure.\n"
    else:
        output += "- No freight trains are scheduled on this line during this block window.\n"
        
    return output

# --- BACKEND CHAT ENGINE ---
def process_emergency_query(user_query):
    if tracks_df is None:
        return "System error: Configuration database unavailable."
        
    query_upper = user_query.upper()
    
    # Scan the user prompt for mentions of a track segment code
    target_segment = None
    for _, track in tracks_df.iterrows():
        if track['segment_id'].upper() in query_upper:
            target_segment = track['segment_id'].upper()
            break
            
    if target_segment:
        return handle_track_emergency(target_segment)
        
    return ("🤖 *I am monitored on the Live Control Room sensor channel.* \n\n"
            "If a field engineer or sensor flags a track layout failure, please type the segment ID directly to trigger automated network protective actions:\n"
            "* *'Sensor detected a failure on SEG_105!'* \n"
            "* *'Track breakage reported at SEG_101'*")

# --- USER INTERFACE DESIGN ---
st.title("🚨 Emergency Rail Dispatch & Control Chatbot")
st.markdown("Automated instantaneous scheduling interventions to protect human passengers and divert traffic dynamically based on infrastructure sensor inputs.")

if "emergency_messages" not in st.session_state:
    st.session_state.emergency_messages = [
        {"role": "assistant", "content": "System Alert: Monitoring active. State the track segment identifier (e.g., *SEG_105*) experiencing a fault to automatically check for passenger detours, freeze line operations, and dispatch maintenance crews."}
    ]

for message in st.session_state.emergency_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_prompt := st.chat_input("Report track sector failure (e.g., SEG_105)..."):
    with st.chat_message("user"):
        st.markdown(user_prompt)
    st.session_state.emergency_messages.append({"role": "user", "content": user_prompt})
    
    bot_reply = process_emergency_query(user_prompt)
    
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.emergency_messages.append({"role": "assistant", "content": bot_reply})
