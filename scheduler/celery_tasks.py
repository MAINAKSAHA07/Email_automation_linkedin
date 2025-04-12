import os
import time
from celery import Celery
from datetime import datetime, timedelta
from dotenv import load_dotenv

from crawler.linkedin_scraper import LinkedInScraper
from email_finder.hunter_api import HunterAPI
from email_sender.send_email import EmailSender
from database.mongo_operations import MongoDB

load_dotenv()

# Initialize Celery with Redis configuration
celery_app = Celery('recruiter_bot',
                    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
                    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
                    broker_transport_options={
                        'visibility_timeout': 43200,  # 12 hours
                        'fanout_prefix': True,
                        'fanout_patterns': True
                    })

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    worker_max_tasks_per_child=100,
    worker_prefetch_multiplier=1
)

# Initialize components
db = MongoDB()
hunter = HunterAPI()
email_sender = EmailSender()

@celery_app.task
def scrape_recruiters(job_title: str, location: str, max_results: int = 100):
    """Task to scrape recruiters from LinkedIn"""
    try:
        scraper = LinkedInScraper()
        recruiters = scraper.search_recruiters(job_title, location, max_results)
        
        # Store recruiters in database
        for recruiter in recruiters:
            db.insert_recruiter(recruiter)
            
        scraper.close()
        return {'status': 'success', 'count': len(recruiters)}
        
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

@celery_app.task
def find_emails():
    """Task to find emails for pending recruiters"""
    try:
        recruiters = db.get_pending_recruiters()
        results = []
        
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
                
                results.append({
                    'recruiter_id': str(recruiter['_id']),
                    'email_id': email_id,
                    'status': 'success'
                })
            else:
                results.append({
                    'recruiter_id': str(recruiter['_id']),
                    'status': 'no_email_found'
                })
                
        return {'status': 'success', 'results': results}
        
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

@celery_app.task
def send_outreach_emails():
    """Task to send outreach emails"""
    try:
        # Get recruiters with verified emails
        recruiters = db.get_pending_recruiters(status='email_found')
        results = []
        
        for recruiter in recruiters:
            # Send email
            result = email_sender.send_email(
                to_email=recruiter['email'],
                template_name='initial',
                template_data={
                    'name': recruiter['name'],
                    'company': recruiter['company'],
                    'field': 'Data Engineering',  # This should be configurable
                    'your_name': 'Your Name'  # This should be configurable
                }
            )
            
            # Log outreach
            db.log_outreach({
                'recruiter_id': str(recruiter['_id']),
                'email_id': str(recruiter['email_id']),
                'template': 'initial',
                'status': result['status'],
                'timestamp': datetime.utcnow()
            })
            
            # Update recruiter status
            db.update_recruiter_status(str(recruiter['_id']), 'email_sent')
            
            results.append(result)
            
        return {'status': 'success', 'results': results}
        
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

# Schedule tasks
celery_app.conf.beat_schedule = {
    'scrape-recruiters': {
        'task': 'scheduler.celery_tasks.scrape_recruiters',
        'schedule': timedelta(days=1),
        'args': ('Data Engineer', 'United States', 100)
    },
    'find-emails': {
        'task': 'scheduler.celery_tasks.find_emails',
        'schedule': timedelta(hours=6)
    },
    'send-outreach-emails': {
        'task': 'scheduler.celery_tasks.send_outreach_emails',
        'schedule': timedelta(hours=12)
    }
} 