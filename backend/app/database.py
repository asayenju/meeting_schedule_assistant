import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
# Load .env from backend/ directory (parent of app/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, '.env')
load_dotenv(ENV_PATH)

# MongoDB connection
MONGODB_URI = os.getenv('MONGODB_URI')
if not MONGODB_URI:
    raise ValueError("MONGODB_URI not found in .env file. Please set it in backend/.env")

DATABASE_NAME = os.getenv('DATABASE_NAME', 'meeting_schedule_assistant')

# Global client
_client: AsyncIOMotorClient = None
_database = None

async def connect_to_mongo():
    """Create database connection."""
    global _client, _database
    _client = AsyncIOMotorClient(MONGODB_URI)
    _database = _client[DATABASE_NAME]
    await create_indexes()
    return _database

async def close_mongo_connection():
    """Close database connection."""
    global _client
    if _client:
        _client.close()

async def create_indexes():
    """Create database indexes on startup."""
    db = get_database()
    
    # Users collection indexes
    users_collection = db['users']
    await users_collection.create_index('google_id', unique=True)
    
    # Auth tokens collection indexes
    auth_tokens_collection = db['auth_tokens']
    await auth_tokens_collection.create_index('user_id')
    
    # Negotiation states collection indexes
    negotiation_states_collection = db['negotiation_states']
    await negotiation_states_collection.create_index('user_id')
    await negotiation_states_collection.create_index('thread_id', unique=True)

def get_database():
    """Get database instance."""
    if _database is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return _database

def get_users_collection():
    """Get users collection."""
    return get_database()['users']

def get_auth_tokens_collection():
    """Get auth_tokens collection."""
    return get_database()['auth_tokens']

def get_negotiation_states_collection():
    """Get negotiation_states collection."""
    return get_database()['negotiation_states']