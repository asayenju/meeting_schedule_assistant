from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from typing import Optional
import json
import base64
import asyncio
from app.service.google_service import get_gmail_service, update_watch_history_id
from app.database import get_auth_tokens_collection, get_users_collection
import httpx

router = APIRouter(prefix="/gmail", tags=["Gmail Webhook"])

@router.post("/webhook")
async def gmail_webhook(
    request: Request,
    x_goog_channel_id: Optional[str] = Header(None),
    x_goog_channel_token: Optional[str] = Header(None),
    x_goog_resource_id: Optional[str] = Header(None),
    x_goog_resource_state: Optional[str] = Header(None)
):
    """
    Webhook endpoint to receive Gmail push notifications.
    Handles both sync notifications and email change notifications.
    """
    try:
        # Handle sync notification (initial setup)
        if x_goog_resource_state == "sync":
            return JSONResponse(content={"status": "sync_received"})
        
        # Try to parse the request body (for Pub/Sub messages)
        try:
            body = await request.json()
            message_data = body.get('message', {})
            
            # Check if this is a Pub/Sub message (has 'data' field)
            if 'data' in message_data:
                # Decode the data if it's base64 encoded
                decoded_data = base64.b64decode(message_data['data']).decode('utf-8')
                notification_data = json.loads(decoded_data)
                email_address = notification_data.get('emailAddress')

                # Get user document from MongoDB
                users_collection = get_users_collection()
                user_doc = await users_collection.find_one({"email": email_address})
                
                if user_doc:
                    google_id = user_doc['google_id']
                    print(f"Processing email changes for user: {email_address} (google_id: {google_id})")
                    await process_email_changes(google_id)
                else:
                    print(f"User not found for email: {email_address}")
                
                return JSONResponse(content={"status": "success"})
        except json.JSONDecodeError:
            # Not a JSON body, might be direct Gmail watch notification
            pass
        except Exception as e:
            print(f"Error processing webhook: {str(e)}")
            # Continue to check for direct Gmail watch format
        
        # Handle direct Gmail watch notification (with headers)
        if x_goog_resource_state == "exists":
            # This handles direct Gmail watch notifications (not via Pub/Sub)
            # For now, we'll rely on Pub/Sub messages above
            pass
        
        return JSONResponse(content={"status": "success"})
    
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
async def process_email_changes(google_id: str):
    """Process email changes since last historyId."""
    try:
        # Get Gmail service and current historyId
        service = await get_gmail_service(google_id)
        auth_tokens_collection = get_auth_tokens_collection()
        token_doc = await auth_tokens_collection.find_one({"user_id": google_id})
        
        if not token_doc or not token_doc.get('watch_history_id'):
            return
        
        start_history_id = token_doc['watch_history_id']
        
        # Get history of changes
        history = service.users().history().list(
            userId='me',
            startHistoryId=start_history_id
        ).execute()
        
        # Process each history record
        for history_record in history.get('history', []):
            # Check for new messages
            if 'messagesAdded' in history_record:
                for message_added in history_record['messagesAdded']:
                    message_id = message_added['message']['id']
                    await process_new_email(google_id, message_id, service)
        
        # Update historyId
        if history.get('historyId'):
            await update_watch_history_id(google_id, history['historyId'])
    
    except Exception as e:
        print(f"Error processing email changes: {str(e)}")
        raise

async def process_new_email(google_id: str, message_id: str, service):
    """Process a new email and call AI API."""
    try:
        # Get full message
        message = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()
        
        # Extract email details
        headers = message['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
        from_email = next((h['value'] for h in headers if h['name'] == 'From'), '')
        thread_id = message.get('threadId')
        snippet = message.get('snippet', '')
        
        # Get email body
        body_text = extract_email_body(message['payload'])
        
        print(f"New email received: From: {from_email}, Subject: {subject}, Thread: {thread_id}")
        
        # Call AI API in background (non-blocking)
        asyncio.create_task(call_ai_api(google_id, from_email, subject, body_text, snippet))
    
    except Exception as e:
        print(f"Error processing email {message_id}: {str(e)}")

async def call_ai_api(google_id: str, from_email: str, subject: str, body_text: str, snippet: str):
    """Call AI API to process email (non-blocking)."""
    try:
        ai_url = "http://localhost:8001/get-response"
        ai_prompt = f"""You received a new email:

From: {from_email}
Subject: {subject}
Body: {body_text}
Snippet: {snippet}

Please analyze this email and take appropriate action."""
        
        ai_data = {
            "input": ai_prompt,
            "google_id": google_id  # Pass google_id to AI API
        }
        
        # Use httpx for async requests
        async with httpx.AsyncClient(timeout=120.0) as client:
            ai_response = await client.post(ai_url, json=ai_data)
            
            if ai_response.status_code == 200:
                ai_result = ai_response.json()
                print(f"AI processed email: {ai_result.get('response', 'No response')}")
            else:
                print(f"AI API error: {ai_response.status_code}, {ai_response.text}")
    
    except Exception as ai_error:
        print(f"Error calling AI API: {str(ai_error)}")

def extract_email_body(payload: dict) -> str:
    """Extract text body from email payload."""
    body = ""
    
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data')
                if data:
                    body += base64.urlsafe_b64decode(data).decode('utf-8')
    elif payload.get('mimeType') == 'text/plain':
        data = payload['body'].get('data')
        if data:
            body = base64.urlsafe_b64decode(data).decode('utf-8')
    
    return body

def detect_meeting_request(subject: str, body: str) -> bool:
    """Simple detection of meeting requests."""
    meeting_keywords = [
        'meeting', 'schedule', 'calendar', 'appointment',
        'call', 'conference', 'zoom', 'teams', 'google meet',
        'when are you available', 'can we meet'
    ]
    
    text = (subject + ' ' + body).lower()
    return any(keyword in text for keyword in meeting_keywords)

