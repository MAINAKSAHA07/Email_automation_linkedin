import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database.mongo_operations import MongoDB

# Initialize database connection
db = MongoDB()

# Page config
st.set_page_config(
    page_title="Recruiter Outreach Dashboard",
    page_icon="📧",
    layout="wide"
)

# Sidebar
st.sidebar.title("Settings")
job_title = st.sidebar.text_input("Job Title", "Data Engineer")
location = st.sidebar.text_input("Location", "United States")
max_results = st.sidebar.slider("Max Results", 10, 500, 100)

# Main content
st.title("Recruiter Outreach Dashboard")

# Stats overview
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_recruiters = len(db.get_pending_recruiters())
    st.metric("Total Recruiters", total_recruiters)

with col2:
    emails_found = len(db.get_pending_recruiters(status='email_found'))
    st.metric("Emails Found", emails_found)

with col3:
    emails_sent = len(db.get_pending_recruiters(status='email_sent'))
    st.metric("Emails Sent", emails_sent)

with col4:
    success_rate = (emails_sent / total_recruiters * 100) if total_recruiters > 0 else 0
    st.metric("Success Rate", f"{success_rate:.1f}%")

# Recent activity
st.subheader("Recent Activity")
recent_outreach = db.get_recent_outreach(limit=10)
if recent_outreach:
    df = pd.DataFrame(recent_outreach)
    st.dataframe(df)
else:
    st.info("No recent outreach activity")

# Manual controls
st.subheader("Manual Controls")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Start Scraping"):
        # Trigger scraping task
        st.success("Scraping started!")

with col2:
    if st.button("Find Emails"):
        # Trigger email finding task
        st.success("Email finding started!")

with col3:
    if st.button("Send Emails"):
        # Trigger email sending task
        st.success("Email sending started!")

# Charts
st.subheader("Analytics")

# Daily activity chart
daily_activity = db.get_daily_activity()
if daily_activity:
    df = pd.DataFrame(daily_activity)
    st.line_chart(df.set_index('date'))

# Status distribution
status_dist = db.get_status_distribution()
if status_dist:
    df = pd.DataFrame(status_dist)
    st.bar_chart(df.set_index('status'))

# Company distribution
company_dist = db.get_company_distribution()
if company_dist:
    df = pd.DataFrame(company_dist)
    st.bar_chart(df.set_index('company'))

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit") 