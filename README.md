# Recruiter Outreach Automation Bot

An automated system for scraping recruiter information, finding valid emails, and sending personalized outreach emails.

## 🚀 Features

- Scrapes recruiter profiles from LinkedIn and other platforms
- Finds and validates email addresses
- Sends personalized emails automatically
- Monitors activities through a dashboard
- Handles captchas and anti-bot measures
- Implements rate limiting and human-like behavior

## 🛠️ Tech Stack

- **Scraping**: Selenium, BeautifulSoup, Playwright
- **Email Discovery**: Hunter.io API, Snov.io API
- **Database**: MongoDB
- **Email Sending**: SendGrid API
- **Task Scheduling**: Celery + Redis
- **Backend**: FastAPI
- **Frontend**: Streamlit
- **Proxy Handling**: ScraperAPI

## 📦 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/recruiter-outreach-bot.git
cd recruiter-outreach-bot
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file with the following variables:
```
MONGODB_URI=your_mongodb_uri
HUNTER_API_KEY=your_hunter_api_key
SENDGRID_API_KEY=your_sendgrid_api_key
LINKEDIN_EMAIL=your_linkedin_email
LINKEDIN_PASSWORD=your_linkedin_password
```

5. Start Redis server:
```bash
redis-server
```

6. Start Celery worker:
```bash
celery -A scheduler.celery_app worker --loglevel=info
```

7. Run the FastAPI server:
```bash
uvicorn main:app --reload
```

8. Run the Streamlit dashboard:
```bash
streamlit run dashboard/app.py
```

## 📁 Project Structure

```
recruiter_outreach_bot/
├── crawler/           # Scraping modules
├── email_finder/      # Email discovery and validation
├── email_sender/      # Email sending functionality
├── scheduler/         # Task scheduling with Celery
├── dashboard/         # Streamlit dashboard
├── database/          # Database operations
└── utils/            # Utility functions
```

## 🔒 Security Notes

- Never commit your `.env` file
- Use environment variables for sensitive data
- Implement rate limiting to avoid API bans
- Follow LinkedIn's terms of service
- Respect GDPR and privacy regulations

## 📝 License

MIT License - See LICENSE file for details 