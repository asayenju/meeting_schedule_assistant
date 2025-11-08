import base64
from email.mime.text import MIMEText
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.service.google_service import get_gmail_service

router = APIRouter(prefix="/gmail", tags=["Gmail"])

class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str

@router.get("/incoming")
async def get_incoming_emails(google_id: str = Query(..., description="Google user ID"), max_results: int = 10):
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
async def send_email(email: EmailRequest, google_id: str = Query(..., description="Google user ID")):
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