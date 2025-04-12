import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.mongo_operations import MongoDB
from crawler.linkedin_scraper import LinkedInScraper
from email_finder.hunter_api import HunterAPI
from email_sender.send_email import EmailSender

# Initialize components
db = MongoDB()
scraper = None  # Initialize scraper only when needed
hunter = HunterAPI()
email_sender = EmailSender()

# Page config
st.set_page_config(
    page_title="Recruiter Outreach Dashboard",
    page_icon="📊",
    layout="wide"
)

# Sidebar
st.sidebar.title("Settings")
job_title = st.sidebar.text_input("Job Title", "Data analyst")
location = st.sidebar.text_input("Location", "United states america")
max_results = st.sidebar.slider("Max Results", 10, 100, 50)

# Main content
st.title("Recruiter Outreach Dashboard")

# Metrics
col1, col2, col3, col4 = st.columns(4)
total_recruiters = db.recruiters.count_documents({})
emails_found = db.emails.count_documents({})
emails_sent = db.outreach.count_documents({})
success_rate = (emails_sent / total_recruiters * 100) if total_recruiters > 0 else 0

col1.metric("Total Recruiters", total_recruiters)
col2.metric("Emails Found", emails_found)
col3.metric("Emails Sent", emails_sent)
col4.metric("Success Rate", f"{success_rate:.1f}%")

# Recent Activity
st.subheader("Recent Activity")
recent_outreach = db.get_recent_outreach(limit=10)
if recent_outreach:
    df_recent = pd.DataFrame(recent_outreach)
    st.dataframe(df_recent[['recruiter_name', 'company', 'status', 'created_at']])
else:
    st.info("No recent outreach activity")

# Manual Controls
st.subheader("Manual Controls")
col1, col2, col3 = st.columns(3)

if col1.button("Scrape Recruiters"):
    with st.spinner("Scraping recruiters from LinkedIn..."):
        try:
            # Initialize scraper if not already initialized
            if scraper is None:
                scraper = LinkedInScraper()
            
            # Search for recruiters
            recruiters = scraper.search_recruiters(job_title, location, max_results)
            
            # Store recruiters in database
            for recruiter in recruiters:
                db.insert_recruiter(recruiter)
            
            st.success(f"Successfully scraped {len(recruiters)} recruiters!")
            
            # Close the scraper
            scraper.close()
            
        except Exception as e:
            st.error(f"Error scraping recruiters: {str(e)}")
            if scraper:
                scraper.close()

if col2.button("Find Emails"):
    with st.spinner("Finding emails for recruiters..."):
        try:
            # Get recruiters without emails
            recruiters = db.get_pending_recruiters()
            found_count = 0
            
            for recruiter in recruiters:
                # Extract domain from company name
                domain = recruiter['company'].lower().replace(' ', '') + '.com'
                
                # Split name into first and last
                name_parts = recruiter['name'].split()
                first_name = name_parts[0]
                last_name = name_parts[-1] if len(name_parts) > 1 else ''
                
                # Find email
                email_data = hunter.find_email(first_name, last_name, domain)
                
                if email_data:
                    # Store email
                    email_id = db.insert_email({
                        'recruiter_id': str(recruiter['_id']),
                        'email': email_data['email'],
                        'score': email_data['score'],
                        'status': email_data['status']
                    })
                    
                    # Update recruiter status
                    db.update_recruiter_status(str(recruiter['_id']), 'email_found')
                    found_count += 1
            
            st.success(f"Found {found_count} email addresses!")
            
        except Exception as e:
            st.error(f"Error finding emails: {str(e)}")

if col3.button("Send Emails"):
    with st.spinner("Sending outreach emails..."):
        try:
            # Get recruiters with verified emails
            recruiters = db.get_pending_recruiters(status='email_found')
            sent_count = 0
            
            for recruiter in recruiters:
                # Send email
                result = email_sender.send_email(
                    to_email=recruiter['email'],
                    template_name='initial',
                    template_data={
                        'name': recruiter['name'],
                        'company': recruiter['company'],
                        'field': job_title,
                        'your_name': 'Mainak Saha'  # Replace with your name
                    }
                )
                
                if result['status'] == 'success':
                    # Log outreach
                    db.log_outreach({
                        'recruiter_id': str(recruiter['_id']),
                        'email_id': str(recruiter['email_id']),
                        'template': 'initial',
                        'status': 'sent',
                        'created_at': datetime.utcnow()
                    })
                    
                    # Update recruiter status
                    db.update_recruiter_status(str(recruiter['_id']), 'email_sent')
                    sent_count += 1
            
            st.success(f"Successfully sent {sent_count} emails!")
            
        except Exception as e:
            st.error(f"Error sending emails: {str(e)}")

# Analytics
st.subheader("Analytics")

# Daily Activity
daily_activity = db.get_daily_activity()
if daily_activity:
    df_daily = pd.DataFrame(daily_activity)
    fig_daily = px.line(df_daily, x='date', y='count', title='Daily Activity')
    st.plotly_chart(fig_daily, use_container_width=True)

# Status Distribution
status_dist = db.get_status_distribution()
if status_dist:
    df_status = pd.DataFrame(status_dist)
    fig_status = px.pie(df_status, values='count', names='status', title='Status Distribution')
    st.plotly_chart(fig_status, use_container_width=True)

# Company Distribution
company_dist = db.get_company_distribution()
if company_dist:
    df_company = pd.DataFrame(company_dist)
    fig_company = px.bar(df_company, x='company', y='count', title='Top Companies')
    st.plotly_chart(fig_company, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("Built with Streamlit") 