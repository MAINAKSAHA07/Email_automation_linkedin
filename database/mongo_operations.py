from typing import List, Dict, Optional
from datetime import datetime
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

class MongoDB:
    def __init__(self):
        self.client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
        self.db = self.client.recruiter_bot
        self.recruiters = self.db.recruiters
        self.emails = self.db.emails
        self.outreach = self.db.outreach

    async def insert_recruiter(self, recruiter_data: Dict) -> str:
        """Insert a new recruiter into the database"""
        result = await self.recruiters.insert_one(recruiter_data)
        return str(result.inserted_id)

    async def find_recruiter(self, query: Dict) -> Optional[Dict]:
        """Find a recruiter by query"""
        return await self.recruiters.find_one(query)

    async def update_recruiter_status(self, recruiter_id: str, status: str) -> bool:
        """Update recruiter status"""
        result = await self.recruiters.update_one(
            {"_id": recruiter_id},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    async def insert_email(self, email_data: Dict) -> str:
        """Insert a new email into the database"""
        result = await self.emails.insert_one(email_data)
        return str(result.inserted_id)

    async def log_outreach(self, outreach_data: Dict) -> str:
        """Log an outreach attempt"""
        result = await self.outreach.insert_one(outreach_data)
        return str(result.inserted_id)

    async def get_pending_recruiters(self, limit: int = 100) -> List[Dict]:
        """Get recruiters pending outreach"""
        cursor = self.recruiters.find({"status": "pending"}).limit(limit)
        return await cursor.to_list(length=limit)

    async def close(self):
        """Close the database connection"""
        self.client.close() 