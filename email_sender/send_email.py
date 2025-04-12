import os
import time
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

class EmailSender:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.gmail_user = os.getenv('GMAIL_USER')
        self.gmail_password = os.getenv('GMAIL_APP_PASSWORD')  # Use App Password for Gmail
        self.templates = {
            'initial': """
            Hi {name},

            I came across your profile while looking into {company} opportunities. 
            I'm passionate about {field} roles and believe my background fits your hiring goals.

            Would love to connect!

            Best regards,
            {your_name}
            """,
            'follow_up': """
            Hi {name},

            I hope this email finds you well. I wanted to follow up on my previous message about {field} opportunities at {company}.

            I'm particularly interested in [specific role/team] and would love to learn more about your hiring process.

            Looking forward to your response!

            Best regards,
            {your_name}
            """
        }

    def send_email(self, to_email: str, template_name: str, template_data: Dict) -> Dict:
        """Send an email using Gmail SMTP"""
        try:
            # Get template
            template = self.templates.get(template_name)
            if not template:
                raise ValueError(f"Template {template_name} not found")

            # Format template with data
            formatted_content = template.format(**template_data)

            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.gmail_user
            msg['To'] = to_email
            msg['Subject'] = f"Regarding {template_data.get('field', '')} Opportunities at {template_data.get('company', '')}"

            # Add body
            msg.attach(MIMEText(formatted_content, 'plain'))

            # Add random delay to mimic human behavior
            time.sleep(random.uniform(5, 10))

            # Connect to SMTP server and send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.gmail_user, self.gmail_password)
                server.send_message(msg)
            
            return {
                'status': 'success',
                'email': to_email,
                'template': template_name
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'email': to_email,
                'template': template_name
            }

    def send_bulk_emails(self, emails: List[Dict], template_name: str, template_data: Dict) -> List[Dict]:
        """Send emails to multiple recipients"""
        results = []
        for email_data in emails:
            # Add recipient-specific data to template data
            recipient_data = {**template_data, **email_data}
            
            # Send email
            result = self.send_email(
                to_email=email_data['email'],
                template_name=template_name,
                template_data=recipient_data
            )
            
            results.append(result)
            
            # Add delay between emails
            time.sleep(random.uniform(30, 60))
            
        return results 