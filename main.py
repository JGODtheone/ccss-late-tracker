import streamlit as st
import hydralit_components as hc
import os
from datetime import datetime, timedelta
import pandas as pd
from difflib import get_close_matches
from streamlit_extras.metric_cards import style_metric_cards
# Added this import for the home page cards
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

school_time = datetime.now() - timedelta(hours=4)
today_str = school_time.strftime("%Y-%m-%d")

# --- HYDRALIT NAVIGATION BAR ---
menu_data = [
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
    home_name='Home',
    sticky_nav=True,
    sticky_mode='pinned',
)

# --- PAGE CONTENT ---
if mode == 'Home':
    # Professional Header
    st.markdown("<h1 style='text-align: center; color: #D32F2F; margin-bottom: 0;'>CASTRIES COMPREHENSIVE</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #555555; margin-top: 0;'>Secondary School Portal</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-style: italic;'>\"A Place of Excellence and Opportunity\"</p>", unsafe_allow_html=True)
    
    st.divider()

    # Layout for a fuller home page
    col1, col2, col3 = st.columns(3)

    with col1:
        with stylable_container(
            key="student_info",
            css_styles="{ border: 1px solid #ddd; border-radius: 10px; padding: 20px; text-align: center; }"
        ):
            st.markdown("### 👤 Students")
            st.write("Ensure you check in before **8:15 AM** to avoid receiving a strike.")
            st.write("**3 Strikes = Detention**")

    with col2:
        with stylable_container(
            key="sys_status",
            css_styles="{ border: 1px solid #D32F2F; border-radius: 10px; padding: 20px; text-align: center; background-color: #FFF5F5; }"
        ):
            st.markdown("### ⏱️ Terminal Clock")
            st.subheader(school_time.strftime('%I:%M %p'))
            st.write(f"Date: {today_str}")

    with col3:
        with stylable_container(
            key="admin_info",
            css_styles="{ border: 1px solid #ddd; border-radius: 10px; padding: 20px; text-align: center; }"
        ):
            st.markdown("### 👩‍🏫 Administration")
            st.write("Teachers can monitor attendance and download daily late reports.")
            st.caption("Secure Login Required")

    st.divider()
    st.markdown("<p style='text-align: center; color: gray;'>© 2026 Castries Comprehensive Secondary School | Digital Attendance Terminal</p>", unsafe_allow_html=True)

elif mode == "Student Check-in":
    st.markdown("<h1>--- STUDENT CHECK-IN ---</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #333333;'><b>Current Time:</b> {school_time.strftime('%I:%M %p')}</p>", unsafe_allow_html=True)

    val = st.text_input("Scan ID or Enter Name:").strip().lower()

    if val:
        matched_key = val if val in students else None
        if not matched_key:
            matches = get_close_matches(val, students.keys(), n=1, cutoff=0.6)
            if matches: matched_key = matches[0]

        if matched_key:
            homeroom = students[matched_key]
            display_name = matched_key.title()
            is_late = school_time.hour > 8 or (school_time.hour == 8 and school_time.minute > 15)
            
            previous_lates = len(history_df[history_df['Student'] == display_name])
            
            if is_late:
                current_strike = previous_lates + 1
                if current_strike >= 3:
                    st.markdown(f"""
                        <div style="border: 3px solid #D32F2F; background-color: #FFF5F5; padding: 20px; border-radius: 10px; text-align: center;">
                            <h2 style="color: #D32F2F;">🚨 STRIKE {current_strike}!</h2>
                            <h4 style="color: #000000;">DETENTION EARNED - REPORT TO OFFICE</h4>
                            <p style="color: #333333;">Student: {display_name} | Room: {homeroom}</p>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning(f"Strike {current_strike} of 3 recorded for {display_name}. Please be punctual tomorrow.")

                with open("detention.txt", "a") as d_file:
                    d_file.write(f"{display_name},{homeroom},{school_time.strftime('%I:%M %p')},{today_str}\n")
            else:
                st.success(f"Check-in Successful: {display_name} (On Time)")
                st.balloons()
        else:
            st.error("Credential not recognized. Please see an administrator.")

elif mode == "Teacher Attendance":
    st.markdown("<h1>👩‍🏫 ADMINISTRATION PANEL</h1>", unsafe_allow_html=True)
    pw = st.text_input("Enter Admin Password", type="password")
    
    if pw == "ccss2026":
        unique_dates = sorted(history_df['Date'].unique().tolist(), reverse=True)
        if today_str not in unique_dates: unique_dates.insert(0, today_str)
            
        view_date = st.selectbox("Select Date to View:", unique_dates)
        
        # Metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("Enrolled Students", len(students))
        c2.metric("Late Records Today", len(history_df[history_df['Date'] == view_date]))
        c3.metric("System Status", "Online")
        style_metric_cards(background_color="#FFFFFF", border_left_color="#D32F2F")

        st.divider()
        date_lates = history_df[history_df['Date'] == view_date]
        st.dataframe(date_lates, use_container_width=True)
