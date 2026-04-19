import streamlit as st
import os
from datetime import datetime, timedelta
import pandas as pd
from difflib import get_close_matches

# --- APP CONFIG ---
st.set_page_config(page_title="CCSS School Portal", page_icon="🏫", layout="wide")

# --- SCHOOL THEMEING (CSS) ---
st.markdown("""
    <style>
    /* Main App Background */
    .stApp {
        background-color: #FFFFFF;
    }

    /* Red Header Accent */
    header[data-testid="stHeader"] {
        background-color: #D32F2F;
        color: white;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #F8F9FA;
        border-right: 2px solid #D32F2F;
    }

    /* Titles and Headers */
    h1, h2, h3 {
        color: #D32F2F !important;
        font-family: 'Georgia', serif;
    }

    /* Input Box Borders */
    .stTextInput>div>div>input {
        border-color: #D32F2F;
    }

    /* Custom Strike Styling */
    .strike-card {
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #D32F2F;
        background-color: #FFF5F5;
        text-align: center;
        margin-bottom: 20px;
    }

    /* Metric Styling */
    [data-testid="stMetricValue"] {
        color: #D32F2F !important;
    }
    
    /* Buttons */
    div.stButton > button:first-child {
        background-color: #D32F2F;
        color: white;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE LOADERS ---
@st.cache_data
def load_students():
    students_dict = {}
    try:
        if os.path.exists("student.txt"):
            with open("student.txt", "r") as f:
                for line in f:
                    if "," in line:
                        name, room = line.strip().split(",")
                        students_dict[name.lower().strip()] = room.strip()
    except Exception as e:
        st.error(f"Error loading student.txt: {e}")
    return students_dict

def load_detention_data():
    if os.path.exists("detention.txt"):
        try:
            if os.stat("detention.txt").st_size == 0:
                return pd.DataFrame(columns=["Student", "Room", "Time", "Date"])
            df = pd.read_csv("detention.txt", names=["Student", "Room", "Time", "Date"])
            df['Date'] = df['Date'].astype(str)
            return df
        except:
            return pd.DataFrame(columns=["Student", "Room", "Time", "Date"])
    return pd.DataFrame(columns=["Student", "Room", "Time", "Date"])

# Initialize data
students = load_students()
# Adjusted for timezone if needed - ensure school_time is set correctly
school_time = datetime.now() - timedelta(hours=4)
today_str = school_time.strftime("%Y-%m-%d")

# --- SIDEBAR NAVIGATION ---
st.sidebar.image("https://via.placeholder.com/150?text=CCSS+LOGO", width=150) # Placeholder for your logo
st.sidebar.markdown("---")
mode = st.sidebar.radio("Navigation", ["Student Check-in", "Teacher Attendance"])

if mode == "Student Check-in":
    st.title("--- CCSS STUDENT PORTAL ---")
    st.write(f"**Current Session Date:** {today_str} | **Clock:** {school_time.strftime('%I:%M %p')}")

    val = st.text_input("Scan ID or Enter Full Name:").strip().lower()

    if val:
        matched_key = val if val in students else None
        if not matched_key:
            matches = get_close_matches(val, students.keys(), n=1, cutoff=0.6)
            if matches: matched_key = matches[0]

        if matched_key:
            homeroom = students[matched_key]
            display_name = matched_key.title()
            
            # Late Check (8:15 AM)
            is_late = school_time.hour > 8 or (school_time.hour == 8 and school_time.minute > 15)
            
            history_df = load_detention_data()
            previous_lates = len(history_df[history_df['Student'] == display_name])
            
            if is_late:
                current_strike = previous_lates + 1
                
                if current_strike >= 3:
                    st.markdown(f"""
                        <div class="strike-card">
                            <h1 style="margin:0;">🚨 STRIKE {current_strike}</h1>
                            <h3 style="color: black !important;">DETENTION EARNED</h3>
                            <p>Student: <b>{display_name}</b> (Room {homeroom})</p>
                            <p style="color: #D32F2F;"><b>PLEASE REPORT TO THE OFFICE IMMEDIATELY</b></p>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning(f"### Strike {current_strike} of 3")
                    st.write(f"Notice: {display_name}, you are late for Room {homeroom}. Please be on time tomorrow.")

                with open("detention.txt", "a") as d_file:
                    d_file.write(f"{display_name},{homeroom},{school_time.strftime('%I:%M %p')},{today_str}\n")
            
            else:
                st.success(f"### CHECK-IN SUCCESSFUL")
                st.balloons()
                st.write(f"Excellent timing, **{display_name}**! Enjoy your day in Room {homeroom}.")
        else:
            st.error("Name not recognized. Please scan again or see the Front Desk.")

elif mode == "Teacher Attendance":
    st.title("👩‍🏫 Academic Administration")
    
    pw = st.text_input("Administrator Credentials", type="password")
    if pw == "ccss2026":
        st.divider()
        
        df_all_history = load_detention_data()
        unique_dates = sorted(df_all_history['Date'].unique().tolist(), reverse=True)
        if today_str not in unique_dates:
            unique_dates.insert(0, today_str)
            
        view_date = st.selectbox("📅 Select Attendance Record:", unique_dates)

        # Metrics Section
        total_enrolled = len(students)
        checked_in_on_date = len(df_all_history[df_all_history['Date'] == view_date]['Student'].unique())
        missing_count = total_enrolled - checked_in_on_date

        col1, col2, col3 = st.columns(3)
        col1.metric("Enrolled", total_enrolled)
        col2.metric("Late/Checked In", checked_in_on_date)
        col3.metric("Unaccounted", missing_count)

        st.divider()
        
        # Records Table
        st.subheader(f"Late Records: {view_date}")
        date_lates = df_all_history[df_all_history['Date'] == view_date]
        
        if not date_lates.empty:
            st.dataframe(date_lates[["Student", "Room", "Time"]], use_container_width=True)
            csv = date_lates.to_csv(index=False).encode('utf-8')
            st.download_button(f"📥 Export {view_date} CSV", data=csv, file_name=f"CCSS_Late_List_{view_date}.csv")
        else:
            st.info(f"No lateness records for {view_date}.")

        # Student History Search
        st.divider()
        with st.expander("🔍 Search Individual Disciplinary History"):
            search_name = st.text_input("Search Student Name:").strip().title()
            if search_name:
                personal_history = df_all_history[df_all_history['Student'] == search_name]
                if not personal_history.empty:
                    st.write(f"**Total Infractions:** {len(personal_history)}")
                    st.table(personal_history[["Date", "Time", "Room"]])
                else:
                    st.write("No disciplinary records found for this student.")
            
    elif pw != "":
        st.error("Access Denied: Incorrect Password")
