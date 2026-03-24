import streamlit as st
import os
from datetime import datetime, timedelta
import pandas as pd
from difflib import get_close_matches

# --- APP CONFIG ---
st.set_page_config(page_title="CCSS Late Tracker", page_icon="📝")

# 1. Load students into a dictionary (Cached for speed)
@st.cache_data
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

students = load_students()

# --- WEB UI INTERFACE ---
st.title("--- CCSS LATE TRACKER 2026 ---")

# Calculate local time (UTC - 4 for Saint Lucia)
school_time = datetime.now() - timedelta(hours=4)
time_str = school_time.strftime("%I:%M %p")
date_str = school_time.strftime("%Y-%m-%d")

st.write(f"**Current School Time:** {time_str}")

# Student Input Box
val = st.text_input("Scan/Enter Student Name:").strip().lower()

if val:
    # Try exact match first, then fuzzy match
    matched_key = None
    if val in students:
        matched_key = val
    else:
        matches = get_close_matches(val, students.keys(), n=1, cutoff=0.6)
        if matches:
            matched_key = matches[0]

    if matched_key:
        homeroom = students[matched_key]
        display_name = matched_key.title()

        # LATE CHECK: After 8:15 AM
        is_late = school_time.hour > 8 or (school_time.hour == 8 and school_time.minute > 15)

        if is_late:
            st.error(f"### Result: LATE")
            st.write(f"**Student:** {display_name} | **Room:** {homeroom} | **Time:** {time_str}")

            # Append to detention file (Internal storage)
            with open("detention.txt", "a") as d_file:
                d_file.write(f"{display_name},{homeroom},{time_str},{date_str}\n")
            st.warning(">>> Added to Detention List.")
        else:
            st.success(f"### Result: ON TIME")
            st.write(f"**Student:** {display_name} | **Room:** {homeroom} | **Time:** {time_str}")
    else:
        st.info(f"Student '{val}' not found. Check spelling or add to student.txt")

# --- ADMIN SECTION ---
st.divider()
with st.expander("Admin: View Detention List"):
    if os.path.exists("detention.txt"):
        # Load the text file into a table for easier reading
        df = pd.read_csv("detention.txt", names=["Student", "Room", "Time", "Date"])
        st.dataframe(df, use_container_width=True)

        # Button to download as CSV for Excel
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Report for Admin", data=csv, file_name=f"detention_{date_str}.csv", mime="text/csv")
    else:
        st.write("No one is on the detention list yet!")
