import streamlit as st
import os
from datetime import datetime, timedelta
import pandas as pd
from difflib import get_close_matches

# --- STREAMLIT EXTRAS IMPORTS ---
from streamlit_extras.stylable_container import stylable_container
from streamlit_extras.metric_cards import style_metric_cards

# --- APP CONFIG ---
st.set_page_config(page_title="CCSS School Portal", page_icon="🏫", layout="wide")

# --- CSS LOADER ---
def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

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
school_time = datetime.now() - timedelta(hours=4)
today_str = school_time.strftime("%Y-%m-%d")

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("## 🏫 CCSS Admin")
    mode = st.radio("Select Mode", ["Student Check-in", "Teacher Attendance"])
    st.divider()
    st.info("Academic Year: 2025-2026")

if mode == "Student Check-in":
    st.title("--- CCSS STUDENT PORTAL ---")
    
    # Use a stylable container for the clock section
    with stylable_container(
        key="clock_box",
        css_styles="""{ border: 1px solid #D32F2F; border-radius: 0.5rem; padding: 10px; background-color: #fcfcfc; }"""
    ):
        st.write(f"**Current Date:** {today_str} | **Clock:** {school_time.strftime('%I:%M %p')}")

    val = st.text_input("Scan/Enter Your Name:").strip().lower()

    if val:
        matched_key = val if val in students else None
        if not matched_key:
            matches = get_close_matches(val, students.keys(), n=1, cutoff=0.6)
            if matches: 
                matched_key = matches[0]

        if matched_key:
            homeroom = students[matched_key]
            display_name = matched_key.title()
            
            is_late = school_time.hour > 8 or (school_time.hour == 8 and school_time.minute > 15)
            history_df = load_detention_data()
            previous_lates = len(history_df[history_df['Student'] == display_name])
            
            if is_late:
                current_strike = previous_lates + 1
                
                if current_strike >= 3:
                    # Academic Red Alert Card using stylable container
                    with stylable_container(
                        key="strike_alert",
                        css_styles="""
                            {
                                border: 3px solid #D32F2F;
                                background-color: #FFF5F5;
                                padding: 20px;
                                border-radius: 15px;
                                text-align: center;
                            }
                        """
                    ):
                        st.error(f"🚨 STRIKE {current_strike}!")
                        st.subheader("DETENTION EARNED - REPORT TO OFFICE")
                        st.write(f"**Student:** {display_name} | **Room:** {homeroom}")
                else:
                    st.warning(f"Strike {current_strike} of 3. Please be earlier tomorrow!")

                with open("detention.txt", "a") as d_file:
                    d_file.write(f"{display_name},{homeroom},{school_time.strftime('%I:%M %p')},{today_str}\n")
            
            else:
                st.success("### Result: ON TIME")
                st.balloons()
                st.write(f"Good job **{display_name}**! You are on time.")
        else:
            st.error("Name not found. Check spelling or see a teacher.")

elif mode == "Teacher Attendance":
    st.title("👩‍🏫 Teacher Admin Panel")
    
    pw = st.text_input("Enter Admin Password", type="password")
    if pw == "ccss2026":
        st.divider()
        
        df_all_history = load_detention_data()
        unique_dates = sorted(df_all_history['Date'].unique().tolist(), reverse=True)
        if today_str not in unique_dates:
            unique_dates.insert(0, today_str)
            
        view_date = st.selectbox("📅 Select Date:", unique_dates)

        # 1. CALCULATE HEADCOUNT
        total_enrolled = len(students)
        checked_in_on_date = len(df_all_history[df_all_history['Date'] == view_date]['Student'].unique())
        missing_count = total_enrolled - checked_in_on_date

        st.subheader(f"Stats for {view_date}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Enrolled", total_enrolled)
        c2.metric("Checked In", checked_in_on_date)
        c3.metric("Missing", missing_count)
        
        # This is a Streamlit Extra! It makes the metrics look like cards.
        style_metric_cards(background_color="#FFFFFF", border_left_color="#D32F2F", border_size_px=2)

        st.divider()
        
        # 2. SHOW LIST
        date_lates = df_all_history[df_all_history['Date'] == view_date]
        if not date_lates.empty:
            st.dataframe(date_lates[["Student", "Room", "Time"]], use_container_width=True)
            csv = date_lates.to_csv(index=False).encode('utf-8')
            st.download_button(f"📥 Download {view_date} Report", data=csv, file_name=f"late_list_{view_date}.csv")
        else:
            st.info(f"No records found for {view_date}.")

        # 3. STUDENT HISTORY SEARCH
        st.divider()
        with st.expander("🔍 Search Individual Student History"):
            search_name = st.text_input("Enter Name:").strip().title()
            if search_name:
                personal_history = df_all_history[df_all_history['Student'] == search_name]
                if not personal_history.empty:
                    st.write(f"**Total Late Times:** {len(personal_history)}")
                    st.table(personal_history[["Date", "Time", "Room"]])
                else:
                    st.write("No records found.")
            
    elif pw != "":
        st.error("Incorrect Password")
