import streamlit as st
import os
from datetime import datetime, timedelta
import pandas as pd
from difflib import get_close_matches

# --- APP CONFIG ---
st.set_page_config(page_title="CCSS School Portal", page_icon="🏫")

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
            return pd.read_csv("detention.txt", names=["Student", "Room", "Time", "Date"])
        except:
            return pd.DataFrame(columns=["Student", "Room", "Time", "Date"])
    return pd.DataFrame(columns=["Student", "Room", "Time", "Date"])

# Initialize data
students = load_students()
school_time = datetime.now() - timedelta(hours=4)
today_str = school_time.strftime("%Y-%m-%d")

# --- SIDEBAR NAVIGATION ---
mode = st.sidebar.radio("Select Mode", ["Student Check-in", "Teacher Attendance"])

if mode == "Student Check-in":
    st.title("--- CCSS STUDENT PORTAL ---")
    st.write(f"**Current Time:** {school_time.strftime('%I:%M %p')}")

    val = st.text_input("Scan/Enter Your Name:").strip().lower()

    if val:
        # Match student (Exact then Fuzzy)
        matched_key = val if val in students else None
        if not matched_key:
            matches = get_close_matches(val, students.keys(), n=1, cutoff=0.6)
            if matches: matched_key = matches[0]

        if matched_key:
            homeroom = students[matched_key]
            display_name = matched_key.title()
            
            # 1. LATE CHECK & STRIKE SYSTEM
            is_late = school_time.hour > 8 or (school_time.hour == 8 and school_time.minute > 15)
            
            # Count historical lates for this student
            history_df = load_detention_data()
            previous_lates = len(history_df[history_df['Student'] == display_name])
            
            if is_late:
                current_strike = previous_lates + 1
                st.error(f"### Result: LATE")
                
                if current_strike >= 3:
                    st.header(f"🚨 STRIKE {current_strike}!")
                    st.subheader("DETENTION EARNED - REPORT TO OFFICE")
                else:
                    st.warning(f"Strike {current_strike} of 3. Please be earlier tomorrow!")

                # Save record to detention.txt
                with open("detention.txt", "a") as d_file:
                    d_file.write(f"{display_name},{homeroom},{school_time.strftime('%I:%M %p')},{today_str}\n")
            
            else:
                st.success(f"### Result: ON TIME")
                st.balloons()
                st.write(f"Good job {display_name}! You are on time.")
        else:
            st.info("Name not found. Check spelling or see a teacher.")

elif mode == "Teacher Attendance":
    st.title("👩‍🏫 Teacher Admin Panel")
    
    pw = st.text_input("Enter Admin Password", type="password")
    if pw == "ccss2026":
        st.divider()
        
        # Load data
        df_all_history = load_detention_data()
        
        # 1. CALCULATE HEADCOUNT (Numbers only, no names)
        total_enrolled = len(students)
        # Note: In this simple version, we assume students only show up in detention.txt if they checked in
        # To be more accurate, you'd need a separate 'attendance.txt'
        checked_in_today = len(df_all_history[df_all_history['Date'] == today_str]['Student'].unique())
        missing_count = total_enrolled - checked_in_today

        # 2. DISPLAY METRICS
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Enrolled", total_enrolled)
        c2.metric("Checked In", checked_in_today)
        c3.metric("Missing Students", missing_count)

        st.divider()
        
        # 3. SHOW ONLY LATE RECORDS FOR TODAY
        st.subheader("Today's Late List")
        today_lates = df_all_history[df_all_history['Date'] == today_str]
        
        if not today_lates.empty:
            st.dataframe(today_lates[["Student", "Room", "Time"]], use_container_width=True)
            
            # Download
            csv = today_lates.to_csv(index=False).encode('utf-8')
            st.download_button("Download Today's Report", data=csv, file_name=f"late_list_{today_str}.csv")
        else:
            st.info("No late students recorded so far today.")
            
    elif pw != "":
        st.error("Incorrect Password")
