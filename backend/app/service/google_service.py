import os
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from app.database import get_auth_tokens_collection
from app.service.encryption import encrypt_token, decrypt_token

os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'credentials.json')

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/userinfo.email',  # Add this
    'https://www.googleapis.com/auth/userinfo.profile',  # Add this
]

async def get_credentials_for_user(google_id: str) -> Credentials:
    """Load credentials for a specific user from MongoDB."""
    auth_tokens_collection = get_auth_tokens_collection()
    token_doc = await auth_tokens_collection.find_one({"user_id": google_id})
    
    if not token_doc:
        return None
    
    # Decrypt refresh token
    refresh_token = decrypt_token(token_doc['encrypted_refresh_token'])
    
    # Load client_id and client_secret from credentials.json
    import json
    with open(CREDENTIALS_PATH, 'r') as f:
        creds_data = json.load(f)
        client_id = creds_data['installed']['client_id']  # or 'web'['client_id'] depending on your file
        client_secret = creds_data['installed']['client_secret']  # or 'web'['client_secret']
    
    # Create credentials object
    creds = Credentials(
        token=token_doc.get('access_token'),
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,  # From credentials.json
        client_secret=client_secret,  # From credentials.json
        scopes=SCOPES
    )
    
    # Check if token needs refresh
    if creds.expired and creds.refresh_token:
        await refresh_user_token(google_id, creds)
        # Reload from database after refresh
        token_doc = await auth_tokens_collection.find_one({"user_id": google_id})
        creds.token = token_doc['access_token']
    
    return creds

async def refresh_user_token(google_id: str, creds: Credentials):
    """Refresh access token and update in database."""
    creds.refresh(Request())
    
    auth_tokens_collection = get_auth_tokens_collection()
    encrypted_refresh = encrypt_token(creds.refresh_token)
    
    await auth_tokens_collection.update_one(
        {"user_id": google_id},
        {
            "$set": {
                "access_token": creds.token,
                "access_token_expiry": creds.expiry if creds.expiry else datetime.utcnow() + timedelta(hours=1),
                "encrypted_refresh_token": encrypted_refresh,
                "updated_at": datetime.utcnow()
            }
        }
    )

async def save_credentials_for_user(google_id: str, creds: Credentials, watch_history_id: str = None):
    """Save credentials to MongoDB for a user."""
    auth_tokens_collection = get_auth_tokens_collection()
    encrypted_refresh = encrypt_token(creds.refresh_token)
    
    token_doc = {
        "user_id": google_id,
        "encrypted_refresh_token": encrypted_refresh,
        "access_token": creds.token,
        "access_token_expiry": creds.expiry if creds.expiry else datetime.utcnow() + timedelta(hours=1),
        "watch_history_id": watch_history_id,
        "updated_at": datetime.utcnow()
    }
    
    await auth_tokens_collection.update_one(
        {"user_id": google_id},
        {"$set": token_doc},
        upsert=True
    )

async def authenticate_user():
    """Authenticate user and return google_id, email, and credentials."""
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    creds = flow.run_local_server(port=0, prompt='consent',   access_type='offline')  
    
    # Validate credentials have a token
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise ValueError("Failed to obtain valid credentials")
    
    # Get user info to extract google_id
    try:
        service = build('oauth2', 'v2', credentials=creds)
        user_info = service.userinfo().get().execute()
        google_id = user_info.get('id')
        email = user_info.get('email')
    except Exception as e:
        raise ValueError(f"Failed to get user info: {str(e)}. Credentials may be invalid.")
    
    # Get Gmail watch historyId if available
    try:
        gmail_service = build('gmail', 'v1', credentials=creds)
        profile = gmail_service.users().getProfile(userId='me').execute()
        watch_history_id = profile.get('historyId')
    except Exception as e:
        watch_history_id = None  # Gmail might not be available
    
    # Save credentials
    await save_credentials_for_user(google_id, creds, watch_history_id)
    
    return google_id, email, creds  # Return all three values

async def get_calendar_service(google_id: str):
    """Get Calendar service for a user."""
    creds = await get_credentials_for_user(google_id)
    if not creds:
        raise ValueError(f"No credentials found for user {google_id}")
    return build('calendar', 'v3', credentials=creds)

async def get_gmail_service(google_id: str):
    """Get Gmail service for a user."""
    creds = await get_credentials_for_user(google_id)
    if not creds:
        raise ValueError(f"No credentials found for user {google_id}")
    return build('gmail', 'v1', credentials=creds)

async def update_watch_history_id(google_id: str, history_id: str):
    """Update watch_history_id in database."""
    auth_tokens_collection = get_auth_tokens_collection()
    await auth_tokens_collection.update_one(
        {"user_id": google_id},
        {"$set": {"watch_history_id": history_id, "updated_at": datetime.utcnow()}}
    )

async def setup_gmail_watch(google_id: str, topic_name: str) -> dict:
    """
    Set up Gmail watch for push notifications.
    
    Args:
        google_id: User's Google ID
        topic_name: Google Cloud Pub/Sub topic name 
                   (e.g., "projects/your-project/topics/gmail-notifications")
    
    Returns:
        Watch response with expiration and historyId
    """
    service = await get_gmail_service(google_id)
    
    # Get current historyId from database
    auth_tokens_collection = get_auth_tokens_collection()
    token_doc = await auth_tokens_collection.find_one({"user_id": google_id})
    start_history_id = token_doc.get('watch_history_id') if token_doc else None
    
    watch_request = {
        "topicName": topic_name,
        "labelIds": ["INBOX"]  # Only watch inbox
    }
    
    # Include start historyId if available
    if start_history_id:
        watch_request["labelFilterAction"] = "include"
    
    response = service.users().watch(userId='me', body=watch_request).execute()
    
    # Update historyId in database
    if response.get('historyId'):
        await update_watch_history_id(google_id, response['historyId'])
    
    return response