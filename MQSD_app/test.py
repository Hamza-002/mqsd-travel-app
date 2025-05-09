from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://hamza_manger:1bSHx7XhuzlWPx40@cluster0.bvo9dhg.mongodb.net/mqsd_trips?retryWrites=true&w=majority"
client = MongoClient(uri, server_api=ServerApi('1'))

try:
    client.admin.command('ping')
    print("✅ Success! Connected to MongoDB Atlas.")
except Exception as e:
    print("❌ Error:", e)
# 1bSHx7XhuzlWPx40