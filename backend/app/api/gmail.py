import base64
from email.mime.text import MIMEText
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.service.google_service import get_gmail_service
from datetime import datetime


router = APIRouter(prefix="/gmail", tags=["Gmail"])

class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str

@router.get("/incoming")
async def get_incoming_emails(
    google_id: str = Query(..., description="Google user ID"), max_results: int = Query(10, description="Maximum number of results (default: 10, max: 50)")):
    """Get incoming emails (limited to 10 by default)"""
    try:
        service = await get_gmail_service(google_id)  # Add google_id parameter
        
        max_results = min(max_results, 50)
        
        # Get unread incoming messages
        results = service.users().messages().list(
            userId='me',
            q='is:unread in:inbox',
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        email_list = []
        
        for msg in messages[:max_results]:
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            
            headers = message['payload']['headers']
            email_list.append({
                'id': msg['id'],
                'subject': next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject'),
                'from': next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown'),
                'date': next((h['value'] for h in headers if h['name'] == 'Date'), ''),
                'snippet': message.get('snippet', '')
            })
        
        return JSONResponse(content={"emails": email_list, "count": len(email_list)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send")
async def send_email(
    email: EmailRequest, 
    google_id: str = Query(..., description="Google user ID")
):
    """Send an email"""
    try:
        service = await get_gmail_service(google_id)
        
        message = MIMEText(email.body)
        message['to'] = email.to
        message['subject'] = email.subject
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        send_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        return JSONResponse(content={
            "status": "success",
            "message_id": send_message.get('id')
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/unread")
async def get_recent_unread_emails(
    google_id: str = Query(..., description="Google user ID"),
    max_results: int = Query(10, description="Maximum number of unread emails to fetch"),
    mark_as_read: bool = Query(False, description="Mark unread emails as read after fetching")
):
    try:
        service = await get_gmail_service(google_id)
        max_results = min(max_results, 30)

        response = service.users().messages().list(
            userId='me',
            q='is:unread label:inbox',
            maxResults=max_results
        ).execute()

        messages = response.get('messages', [])
        if not messages:
            return JSONResponse(content={"emails": [], "count": 0, "message": "No unread emails found."})

        email_list = []
        for msg in messages:
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()

            headers = {h['name']: h['value'] for h in message['payload']['headers']}
            email_list.append({
                'id': msg['id'],
                'subject': headers.get('Subject', 'No Subject'),
                'from': headers.get('From', 'Unknown'),
                'date': headers.get('Date', ''),
                'snippet': message.get('snippet', '')
            })

            if mark_as_read:
                service.users().messages().modify(
                    userId='me',
                    id=msg['id'],
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()

        return JSONResponse(content={"emails": email_list, "count": len(email_list)})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch unread emails: {str(e)}")

@router.post("/watch/setup")
async def setup_watch(
    google_id: str = Query(..., description="Google user ID"),
    topic_name: str = Query(..., description="Google Cloud Pub/Sub topic name")
):
    """Set up Gmail watch for push notifications."""
    try:
        from service.google_service import setup_gmail_watch
        response = await setup_gmail_watch(google_id, topic_name)
        return JSONResponse(content={
            "status": "success",
            "expiration": response.get('expiration'),
            "historyId": response.get('historyId'),
            "message": f"Watch set up successfully. Expires at: {response.get('expiration')}"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
