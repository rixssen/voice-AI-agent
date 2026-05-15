import streamlit as st
import requests
import datetime

# The URL where your FastAPI backend is running
BASE_URL = "http://127.0.0.1:4444"

st.set_page_config(page_title="Home Repair Dashboard", layout="wide")

st.title("🔧 Home Repair Service Manager")
st.write("Use this dashboard to test your Voice Agent's backend.")

# Sidebar for Navigation
menu = st.sidebar.selectbox("Menu", ["Book a Repair", "View Schedule"])

# --- TAB 1: BOOK A REPAIR ---
if menu == "Book a Repair":
    st.header("📝 Create New Visit Slot")
    
    with st.form("repair_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Client Name")
            tech = st.selectbox("Technician Type", ["Plumber", "Electrician", "AC Technician", "Carpenter"])
        with col2:
            date = st.date_input("Visit Date", datetime.date.today())
            time = st.time_input("Visit Time", datetime.time(10, 0))
        
        issue = st.text_area("Issue Description (e.g. Leaking sink)")
        
        submit = st.form_submit_button("Book Technician")
        
        if submit:
            # Combine date and time for the API
            visit_dt = datetime.datetime.combine(date, time).isoformat()
            
            payload = {
                "client_name": name,
                "issue_description": issue,
                "technician_type": tech,
                "visit_time": visit_dt
            }
            
            try:
                response = requests.post(f"{BASE_URL}/book_repair/", json=payload)
                if response.status_code == 200:
                    st.success(f"✅ Successfully booked {tech} for {name}!")
                else:
                    st.error(f"❌ Error: {response.text}")
            except Exception as e:
                st.error(f"Could not connect to backend. Is it running? {e}")

# --- TAB 2: VIEW SCHEDULE & CANCEL ---
elif menu == "View Schedule":
    st.header("📅 Technician Schedule")
    
    check_date = st.date_input("Select Date to View", datetime.date.today())
    
    # Fetch the data
    try:
        response = requests.get(f"{BASE_URL}/view_schedule/", params={"date": check_date})
        if response.status_code == 200:
            data = response.json()
            if data:
                # Display each booking with a Cancel button next to it
                for booking in data:
                    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                    with col1:
                        st.write(f"**Client:** {booking['client_name']}")
                    with col2:
                        st.write(f"**Tech:** {booking['technician_type']}")
                    with col3:
                        st.write(f"**Issue:** {booking['issue_description']}")
                    with col4:
                        # The Cancel Button
                        if st.button("Cancel", key=booking['id']):
                            cancel_payload = {
                                "client_name": booking['client_name'],
                                "date": check_date.isoformat()
                            }
                            # Calling your /cancel_repair/ endpoint
                            res = requests.post(f"{BASE_URL}/cancel_repair/", params=cancel_payload)
                            if res.status_code == 200:
                                st.success("Cancelled!")
                                st.rerun() # Refresh the list
                            else:
                                st.error("Failed to cancel.")
            else:
                st.info("No repairs scheduled for this date.")
        else:
            st.error("Failed to fetch schedule.")
    except Exception as e:
        st.error(f"Connection Error: {e}")