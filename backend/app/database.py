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
    try:
        # For MongoDB Atlas, the connection string should already include TLS parameters
        # Only add connection timeout options, don't override TLS settings from URI
        _client = AsyncIOMotorClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=10000,  # 10 second timeout
            connectTimeoutMS=20000,  # 20 second connection timeout
            socketTimeoutMS=20000,  # 20 second socket timeout
        )
        # Test the connection with a ping
        await _client.admin.command('ping')
        _database = _client[DATABASE_NAME]
        await create_indexes()
        return _database
    except Exception as e:
        error_msg = str(e)
        if "SSL" in error_msg or "TLS" in error_msg:
            raise ConnectionError(
                f"MongoDB SSL/TLS connection failed: {error_msg}\n"
                f"Please check:\n"
                f"1. Your MONGODB_URI includes proper TLS parameters (tls=true or ssl=true)\n"
                f"2. Your network/firewall allows connections to MongoDB Atlas\n"
                f"3. Your IP address is whitelisted in MongoDB Atlas Network Access\n"
                f"4. Your MongoDB credentials are correct"
            )
        raise ConnectionError(f"Failed to connect to MongoDB: {error_msg}. Please check your MONGODB_URI and network connection.")

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
    await users_collection.create_index('pending_requests.message_id')  # Index for pending requests

    # Auth tokens collection indexes
    auth_tokens_collection = db['auth_tokens']
    await auth_tokens_collection.create_index('user_id')
    
    # Negotiation states collection indexes (commented out for now)
    # negotiation_states_collection = db['negotiation_states']
    # await negotiation_states_collection.create_index('user_id')
    # await negotiation_states_collection.create_index('thread_id', unique=True)

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

# def get_negotiation_states_collection():
#     """Get negotiation_states collection."""
#     return get_database()['negotiation_states']
