import streamlit as st
import hydralit_components as hc
import os
from datetime import datetime, timedelta
import pandas as pd
from difflib import get_close_matches
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.stylable_container import stylable_container 

# --- APP CONFIG ---
# This line sets your school logo as the icon in the browser tab
st.set_page_config(
    page_title="CCSS School Portal", 
    page_icon="image_bea7a3.jpg", 
    layout="wide"
)

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

# --- PAGE CONTENT ---
if mode == 'Home':
    st.markdown("<h1 style='text-align: center; color: #D32F2F; margin-bottom: 0;'>CASTRIES COMPREHENSIVE</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #555555; margin-top: 0;'>Secondary School Portal</h3>", unsafe_allow_html=True)
    
    st.divider()

    # --- LATE BELL PROGRESS BAR ---
    target_time = school_time.replace(hour=8, minute=15, second=0, microsecond=0)
    if school_time < target_time:
        time_left = target_time - school_time
        total_seconds = 8 * 3600 + 15 * 60 
        current_seconds = school_time.hour * 3600 + school_time.minute * 60
        progress = min(current_seconds / total_seconds, 1.0)
        
        st.write(f"⏳ **Time until Late Bell:** {str(time_left).split('.')[0]} remaining")
        st.progress(progress)
    else:
        st.error("🚨 Late Bell has rung. All arrivals are now recorded as strikes.")

    col1, col2, col3 = st.columns(3)

    with col1:
        with stylable_container(key="s_info", css_styles="{border: 1px solid #ddd; border-radius: 10px; padding: 20px; text-align: center;}"):
            st.markdown("<h3 style='color: #333;'>👤 Students</h3>", unsafe_allow_html=True)
            st.write("Ensure you check in before **8:15 AM**.")
            st.markdown("**3 Strikes = Detention**")

    with col2:
        with stylable_container(key="sys_status", css_styles="{border: 1px solid #D32F2F; border-radius: 10px; padding: 20px; text-align: center; background-color: #FFF5F5;}"):
            st.markdown("<h3 style='color: #333333; margin-bottom: 0;'>⏱️ Terminal Clock</h3>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='color: #D32F2F; margin-top: 0;'>{school_time.strftime('%I:%M %p')}</h2>", unsafe_allow_html=True)
            st.markdown(f"<p style='color: #555555;'>{school_time.strftime('%A, %B %d')}</p>", unsafe_allow_html=True)
            
    with col3:
        with stylable_container(key="a_info", css_styles="{border: 1px solid #ddd; border-radius: 10px; padding: 20px; text-align: center;}"):
            st.markdown("<h3 style='color: #333;'>👩‍🏫 Staff</h3>", unsafe_allow_html=True)
            st.write("Manage daily reports and student records securely.")
            st.caption("Authorization Required")

elif mode == "Student Check-in":
    st.markdown("<h2 style='text-align: center;'>STUDENT CHECK-IN</h2>", unsafe_allow_html=True)
    
    # Status Indicator
    is_late = school_time.hour > 8 or (school_time.hour == 8 and school_time.minute > 15)
    if is_late:
        st.error(f"Current Status: LATE ({school_time.strftime('%I:%M %p')})")
    else:
        st.success(f"Current Status: ON TIME ({school_time.strftime('%I:%M %p')})")

    # FIXED LINE: Removed all mention of Scan ID/Card
    val = st.text_input("Enter Name:", placeholder="Click here...").strip().lower()

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
                if current_strike >= 3:
                    st.markdown(f"""
                        <div style="border: 4px solid #D32F2F; background-color: #fce8e6; padding: 30px; border-radius: 15px; text-align: center;">
                            <h1 style="color: #D32F2F; font-size: 50px;">🚨 STRIKE {current_strike}</h1>
                            <h2 style="color: #000;">{display_name}</h2>
                            <h3 style="color: #333;">DETENTION ISSUED</h3>
                            <p>Report to Room {homeroom} for further instructions.</p>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning(f"⚠️ {display_name}: Strike {current_strike} of 3. Please arrive by 8:15 AM tomorrow.")

                with open("detention.txt", "a") as d_file:
                    d_file.write(f"{display_name},{homeroom},{school_time.strftime('%I:%M %p')},{today_str}\n")
            else:
                st.balloons()
                st.success(f"✅ Welcome {display_name}! You are on time. Enjoy your day!")
        else:
            st.error("User not found. Please try again or see the office.")

elif mode == "Teacher Attendance":
    st.markdown("<h2 style='color: #D32F2F;'>ADMINISTRATION PANEL</h2>", unsafe_allow_html=True)
    pw = st.text_input("Enter Admin Password", type="password")
    
    if pw == "ccss2026":
        unique_dates = sorted(history_df['Date'].unique().tolist(), reverse=True)
        if today_str not in unique_dates: unique_dates.insert(0, today_str)
            
        view_date = st.selectbox("Select Date to View:", unique_dates)
        
        c1, c2, c3 = st.columns(3)
        date_lates = history_df[history_df['Date'] == view_date]
        
        c1.metric("Students Logged Late", len(date_lates))
        c2.metric("Total System Strikes", len(history_df))
        c3.metric("Portal Status", "ONLINE", delta="Stable")
        style_metric_cards(background_color="#FFFFFF", border_left_color="#D32F2F")

        st.divider()
        
        col_a, col_b = st.columns([4, 1])
        with col_a:
            st.subheader(f"Records for {view_date}")
        with col_b:
            csv = date_lates.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export CSV", data=csv, file_name=f"lates_{view_date}.csv", mime='text/csv')
            
        st.dataframe(date_lates, use_container_width=True)
    elif pw != "":
        st.error("Incorrect Password.")
