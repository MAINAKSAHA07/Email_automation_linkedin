from typing import List, Dict, Optional
from datetime import datetime
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

class MongoDB:
    def __init__(self):
        self.client = MongoClient(os.getenv("MONGODB_URI"))
        self.db = self.client.recruiter_bot
        self.recruiters = self.db.recruiters
        self.emails = self.db.emails
        self.outreach = self.db.outreach

    def insert_recruiter(self, recruiter_data: Dict) -> str:
        """Insert a new recruiter into the database"""
        result = self.recruiters.insert_one(recruiter_data)
        return str(result.inserted_id)

    def find_recruiter(self, query: Dict) -> Optional[Dict]:
        """Find a recruiter by query"""
        return self.recruiters.find_one(query)

    def update_recruiter_status(self, recruiter_id: str, status: str) -> bool:
        """Update recruiter status"""
        result = self.recruiters.update_one(
            {"_id": recruiter_id},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    def insert_email(self, email_data: Dict) -> str:
        """Insert a new email into the database"""
        result = self.emails.insert_one(email_data)
        return str(result.inserted_id)

    def log_outreach(self, outreach_data: Dict) -> str:
        """Log an outreach attempt"""
        result = self.outreach.insert_one(outreach_data)
        return str(result.inserted_id)

    def get_pending_recruiters(self, status: str = None, limit: int = 100) -> List[Dict]:
        """Get recruiters pending outreach"""
        query = {"status": status} if status else {"status": "pending"}
        cursor = self.recruiters.find(query).limit(limit)
        return list(cursor)

    def get_recent_outreach(self, limit: int = 10) -> List[Dict]:
        """Get recent outreach attempts"""
        cursor = self.outreach.find().sort("created_at", -1).limit(limit)
        return list(cursor)

    def get_daily_activity(self) -> List[Dict]:
        """Get daily activity statistics"""
        pipeline = [
            {
                "$group": {
                    "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}},
            {"$project": {"date": "$_id", "count": 1, "_id": 0}}
        ]
        return list(self.outreach.aggregate(pipeline))

    def get_status_distribution(self) -> List[Dict]:
        """Get distribution of recruiter statuses"""
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            {"$project": {"status": "$_id", "count": 1, "_id": 0}}
        ]
        return list(self.recruiters.aggregate(pipeline))

    def get_company_distribution(self) -> List[Dict]:
        """Get distribution of companies"""
        pipeline = [
            {"$group": {"_id": "$company", "count": {"$sum": 1}}},
            {"$project": {"company": "$_id", "count": 1, "_id": 0}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        return list(self.recruiters.aggregate(pipeline))

    def close(self):
        """Close the database connection"""
        self.client.close() 