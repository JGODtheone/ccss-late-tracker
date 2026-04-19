import streamlit as st
import hydralit_components as hc
import os
from datetime import datetime, timedelta
import pandas as pd
from difflib import get_close_matches
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.stylable_container import stylable_container 

# --- APP CONFIG ---
# Removed the custom image file to revert to the default Streamlit logo
st.set_page_config(
    page_title="CCSS School Portal", 
    layout="wide"
)

# --- CUSTOM CSS FOR METRICS & TEXT ---
# This ensures the administration metrics are visible against the dark background
st.markdown("""
    <style>
    [data-testid="stMetricValue"] {
        color: white !important;
    }
    [data-testid="stMetricLabel"] {
        color: rgba(255, 255, 255, 0.8) !important;
    }
    div[data-testid="metric-container"] {
        background-color: #1E1E1E;
        border: 1px solid #D32F2F;
        padding: 15px;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- CSS LOADER ---
def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

# --- DATA LOADING ---
with hc.HyLoader('Accessing CCSS Secure Database...', loader_name='standard'):
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
        except Exception:
            pass
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

    students = load_students()
    history_df = load_detention_data()

# Time Adjustment for Saint Lucia (UTC-4)
school_time = datetime.now() - timedelta(hours=4)
today_str = school_time.strftime("%Y-%m-%d")

# --- NAVIGATION BAR ---
menu_data = [
    {'icon': "bi bi-house", 'label': "Home"},
    {'icon': "bi bi-person-check", 'label': "Student Check-in"},
    {'icon': "bi bi-shield-lock", 'label': "Teacher Attendance"},
]

over_theme = {
    'txc_inactive': '#FFFFFF', 
    'menu_background': '#D32F2F', 
    'txc_active': '#D32F2F', 
    'option_active': '#FFFFFF'
}

mode = hc.nav_bar(
    menu_definition=menu_data,
    override_theme=over_theme,
    home_name=None, 
    sticky_nav=True,
    sticky_mode='pinned',
)

# --- PAGE CONTENT ---
if mode == 'Home':
    st.markdown("<h1 style='text-align: center; color: #D32F2F; margin-bottom: 0;'>CASTRIES COMPREHENSIVE</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #555555; margin-top: 0;'>Secondary School Portal</h3>", unsafe_allow_html=True)
    st.divider()

    col1, col2, col3 = st.columns(3)
    with col2:
        with stylable_container(key="sys_status", css_styles="{border: 1px solid #D32F2F; border-radius: 10px; padding: 20px; text-align: center; background-color: #FFF5F5;}"):
            st.markdown(f"<h2 style='color: #D32F2F; margin-top: 0;'>{school_time.strftime('%I:%M %p')}</h2>", unsafe_allow_html=True)
            st.write(school_time.strftime('%A, %B %d'))

elif mode == "Student Check-in":
    st.markdown("<h2 style='text-align: center;'>STUDENT CHECK-IN</h2>", unsafe_allow_html=True)
    is_late = school_time.hour > 8 or (school_time.hour == 8 and school_time.minute > 15)
    
    # Red status box for late arrivals
    if is_late:
        st.error(f"Current Status: LATE ({school_time.strftime('%I:%M %p')})")
    else:
        st.success(f"Current Status: ON TIME ({school_time.strftime('%I:%M %p')})")

    # Simplified input as requested
    val = st.text_input("Enter Name:", placeholder="Click here...").strip().lower()

    if val:
        matches = get_close_matches(val, students.keys(), n=1, cutoff=0.6)
        if matches:
            matched_key = matches[0]
            display_name = matched_key.title()
            homeroom = students[matched_key]
            
            if is_late:
                with open("detention.txt", "a") as d_file:
                    d_file.write(f"{display_name},{homeroom},{school_time.strftime('%I:%M %p')},{today_str}\n")
                st.warning(f"⚠️ {display_name} recorded as LATE.")
            else:
                st.balloons()
                st.success(f"✅ Welcome {display_name}!")
        else:
            st.error("User not found.")

elif mode == "Teacher Attendance":
    st.markdown("<h2 style='color: #D32F2F;'>ADMINISTRATION PANEL</h2>", unsafe_allow_html=True)
    pw = st.text_input("Enter Admin Password", type="password")
    
    if pw == "ccss2026":
        unique_dates = sorted(history_df['Date'].unique().tolist(), reverse=True)
        if today_str not in unique_dates: unique_dates.insert(0, today_str)
        view_date = st.selectbox("Select Date to View:", unique_dates)
        
        # Administration metrics
        date_lates = history_df[history_df['Date'] == view_date]
        c1, c2, c3 = st.columns(3)
        c1.metric("Students Logged Late", len(date_lates))
        c2.metric("Total System Strikes", len(history_df))
        c3.metric("Portal Status", "ONLINE", delta="Stable")
        
        style_metric_cards(background_color="#121212", border_left_color="#D32F2F", border_color="#1E1E1E")

        st.divider()
        st.subheader(f"Records for {view_date}")
        st.dataframe(date_lates, use_container_width=True)
    elif pw != "":
        st.error("Incorrect Password.")
