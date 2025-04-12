import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Get MongoDB URI from environment
uri = os.getenv("MONGODB_URI")
print(f"Connecting to MongoDB with URI: {uri}")

try:
    # Create a new client and connect to the server
    client = MongoClient(uri)
    
    # Send a ping to confirm a successful connection
    client.admin.command('ping')
    print("Successfully connected to MongoDB!")
    
    # Create or get the recruiter_bot database
    db = client.recruiter_bot
    
    # Create collections if they don't exist
    collections = ['recruiters', 'emails', 'outreach']
    for collection in collections:
        if collection not in db.list_collection_names():
            db.create_collection(collection)
            print(f"Created collection: {collection}")
        else:
            print(f"Collection already exists: {collection}")
    
    # List all databases
    print("\nAvailable databases:")
    for db_name in client.list_database_names():
        print(f"- {db_name}")
    
    # Close the connection
    client.close()
    
except Exception as e:
    print(f"Error connecting to MongoDB: {e}") 