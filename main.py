import streamlit as st
import hydralit_components as hc
import os
from datetime import datetime, timedelta
import pandas as pd
from difflib import get_close_matches
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.stylable_container import stylable_container 

# --- APP CONFIG ---
st.set_page_config(page_title="CCSS School Portal", page_icon="🏫", layout="wide")

# --- CSS LOADER ---
def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

# --- HYDRALIT LOADER & DATA LOADING ---
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

    students = load_students()
    history_df = load_detention_data()

# Time Adjustment for Saint Lucia (UTC-4)
school_time = datetime.now() - timedelta(hours=4)
today_str = school_time.strftime("%Y-%m-%d")

# --- HYDRALIT NAVIGATION BAR ---
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

# --- GLOBAL BRANDING FUNCTION ---
def school_header():
    col_logo, col_text = st.columns([1, 5])
    with col_logo:
        # This will look for image_bea7a3.jpg in your GitHub folder
        if os.path.exists("image_bea7a3.jpg"):
            st.image("image_bea7a3.jpg", width=100)
        else:
            st.markdown("🏫") # Fallback emoji
    with col_text:
        st.markdown("<h1 style='color: #D32F2F; margin-bottom: 0;'>CASTRIES COMPREHENSIVE</h1>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #555555; margin-top: 0;'>Secondary School Digital Portal</h4>", unsafe_allow_html=True)
    st.divider()

# --- PAGE CONTENT ---
if mode == 'Home':
    school_header()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        with stylable_container(key="s_info", css_styles="{border: 1px solid #ddd; border-radius: 10px; padding: 20px; text-align: center;}"):
            st.markdown("<h3 style='color: #333;'>👤 Student Check-in</h3>", unsafe_allow_html=True)
            st.write("Register your arrival before 8:15 AM to avoid strikes.")

    with col2:
        with stylable_container(key="sys_status", css_styles="{border: 1px solid #D32F2F; border-radius: 10px; padding: 20px; text-align: center; background-color: #FFF5F5;}"):
            st.markdown("<h3 style='color: #333333; margin-bottom: 0;'>⏱️ Terminal Clock</h3>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='color: #D32F2F; margin-top: 0;'>{school_time.strftime('%I:%M %p')}</h2>", unsafe_allow_html=True)
            st.markdown(f"<p style='color: #555555;'>{school_time.strftime('%A, %b %d')}</p>", unsafe_allow_html=True)
            
    with col3:
        with stylable_container(key="a_info", css_styles="{border: 1px solid #ddd; border-radius: 10px; padding: 20px; text-align: center;}"):
            st.markdown("<h3 style='color: #333;'>👩‍🏫 Staff Portal</h3>", unsafe_allow_html=True)
            st.write("Administrative access for attendance tracking and reports.")

elif mode == "Student Check-in":
    school_header()
    
    st.markdown("<h2 style='text-align: center; color: #333;'>Student Attendance</h2>", unsafe_allow_html=True)
    
    is_late = school_time.hour > 8 or (school_time.hour == 8 and school_time.minute > 15)
    
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        with stylable_container(key="checkin", css_styles="{border: 1px solid #ddd; border-radius: 15px; padding: 30px; background-color: #f9f9f9;}"):
            # UPDATED: No mention of scanning or cards
            val = st.text_input("Enter Full Name:", placeholder="Type your name here...").strip().lower()

            if val:
                matched_key = val if val in students else None
                if not matched_key:
                    matches = get_close_matches(val, students.keys(), n=1, cutoff=0.6)
                    if matches: matched_key = matches[0]

                if matched_key:
                    homeroom = students[matched_key]
                    display_name = matched_key.title()
                    student_history = history_df[history_df['Student'] == display_name]
                    previous_lates = len(student_history)
                    
                    if is_late:
                        current_strike = previous_lates + 1
                        st.error(f"LATE RECORDED: {display_name}")
                        if current_strike >= 3:
                            st.markdown(f"<h1 style='color: #D32F2F; text-align: center;'>🚨 STRIKE {current_strike}</h1>", unsafe_allow_html=True)
                            st.warning("DETENTION EARNED - Please report to the office.")
                        else:
                            st.warning(f"Strike {current_strike} recorded. Please arrive earlier tomorrow.")
                        
                        with open("detention.txt", "a") as d_file:
                            d_file.write(f"{display_name},{homeroom},{school_time.strftime('%I:%M %p')},{today_str}\n")
                    else:
                        st.success(f"WELCOME {display_name}! You are on time.")
                        st.balloons()
                else:
                    st.error("Name not found. Please ensure you are entering your full name correctly.")

elif mode == "Teacher Attendance":
    school_header()
    pw = st.text_input("Enter Admin Password", type="password")
    if pw == "ccss2026":
        unique_dates = sorted(history_df['Date'].unique().tolist(), reverse=True)
        if today_str not in unique_dates: unique_dates.insert(0, today_str)
        view_date = st.selectbox("Select Date:", unique_dates)
        
        c1, c2, c3 = st.columns(3)
        date_lates = history_df[history_df['Date'] == view_date]
        c1.metric("Lates Today", len(date_lates))
        c2.metric("Total Records", len(history_df))
        c3.metric("System Status", "Live")
        style_metric_cards(background_color="#FFFFFF", border_left_color="#D32F2F")

        st.divider()
        st.dataframe(date_lates, use_container_width=True)
