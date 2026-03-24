import streamlit as st
import os
from datetime import datetime, timedelta
import pandas as pd
from difflib import get_close_matches

# --- APP CONFIG ---
st.set_page_config(page_title="CCSS School Portal", page_icon="🏫")

# --- DATABASE LOADERS ---
def load_students():
    students = {}
    try:
        with open("student.txt", "r") as f:
            for line in f:
                if "," in line:
                    name, room = line.strip().split(",")
                    students[name.lower().strip()] = room.strip()
    except FileNotFoundError:
        st.error("Error: student.txt not found!")
    return students

def load_detention_data():
    if os.path.exists("detention.txt"):
        return pd.read_csv("detention.txt", names=["Student", "Room", "Time", "Date"])
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
        # Match student
        matched_key = val if val in students else None
        if not matched_key:
            matches = get_close_matches(val, students.keys(), n=1, cutoff=0.6)
            if matches: matched_key = matches[0]

        if matched_key:
            homeroom = students[matched_key]
            display_name = matched_key.title()
            
            # 1. LATE CHECK & STRIKE SYSTEM
            is_late = school_time.hour > 8 or (school_time.hour == 8 and school_time.minute > 15)
            
            # Count historical lates
            history_df = load_detention_data()
            previous_lates = len(history_df[history_df['Student'] == display_name])
            
            if is_late:
                current_strike = previous_lates + 1
                st.error(f"### Result: LATE")
                
                if current_strike >= 3:
                    st.header(f"🚨 STRIKE {current_strike}!")
                    st.subheader("DETENTION EARNED - REPORT TO OFFICE")
                else:
                    st.warning(f"Strike {current_strike} of 3. Streak Reset to 0.")

                # Save record
                with open("detention.txt", "a") as d_file:
                    d_file.write(f"{display_name},{homeroom},{school_time.strftime('%I:%M %p')},{today_str}\n")
            
            else:
                st.success(f"### Result: ON TIME")
                st.balloons()
                st.write(f"Points Gained! Keep the streak alive, {display_name}!")
                
            # Note: In a real cloud app, you'd save "Points" to a CSV here. 
            # For now, it shows their status.
        else:
            st.info("Name not found. Check spelling!")

elif mode == "Teacher Attendance":
    st.title("👩‍🏫 Teacher Admin Panel")
    
    # Simple password protection
    pw = st.text_input("Enter Admin Password", type="password")
    if pw == "ccss2026":
        st.divider()
        
        # 2. ATTENDANCE SUMMARY
        df = load_detention_data()
        
        col1, col2 = st.columns(2)
        col1.metric("Total Lates Today", len(df[df['Date'] == today_str]))
        
        st.subheader("Current Detention List")
        st.dataframe(df, use_container_width=True)
        
        # 3. ABSENTEE CHECK
        st.subheader("Who is missing?")
        checked_in_names = df[df['Date'] == today_str]['Student'].str.lower().tolist()
        absent = [name.title() for name in students.keys() if name not in checked_in_names]
        
        if absent:
            st.warning(f"{len(absent)} students have not checked in yet.")
            st.write(", ".join(absent))
            
        # Download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Full Report", data=csv, file_name=f"school_report_{today_str}.csv")
