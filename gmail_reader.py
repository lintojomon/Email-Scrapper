# gmail_reader.py - Gmail Email Fetching Module
# ==============================================
# Fetches emails from Gmail using Gmail API

"""
Gmail Reader - Fetch and parse emails from Gmail inbox

This module handles:
- Fetching messages from inbox (configurable: last N emails or last N days)
- Extracting subject from headers
- Decoding email body from base64
- Handling multipart emails (text/html and text/plain)
- Cleaning HTML using BeautifulSoup
"""

import base64
from bs4 import BeautifulSoup
from typing import Optional, List, Dict


def fetch_emails(service, max_results: int = 50, query: str = "") -> List[Dict]:
    """
    Fetch emails from Gmail inbox.
    
    Args:
        service: Authenticated Gmail API service object
        max_results: Maximum number of emails to fetch (default: 50)
        query: Gmail search query (e.g., 'newer_than:30d' for last 30 days)
    
    Returns:
        List of email dictionaries with id, subject, body, date, sender
    """
    emails = []
    
    # Build query - always include INBOX
    search_query = "in:inbox"
    if query:
        search_query = f"{search_query} {query}"
    
    print(f"📧 Fetching emails (max: {max_results})...")
    if query:
        print(f"   Query: {query}")
    
    try:
        # Step 1: Get list of message IDs
        results = service.users().messages().list(
            userId='me',
            maxResults=max_results,
            q=search_query
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            print("   No emails found.")
            return emails
        
        print(f"   Found {len(messages)} emails. Fetching details...")
        
        # Step 2: Fetch full details for each message
        for i, msg in enumerate(messages, 1):
            email_data = get_email_details(service, msg['id'])
            if email_data:
                emails.append(email_data)
            
            # Progress indicator
            if i % 10 == 0:
                print(f"   Processed {i}/{len(messages)} emails...")
        
        print(f"✓ Successfully fetched {len(emails)} emails")
        
    except Exception as e:
        print(f"❌ Error fetching emails: {e}")
    
    return emails


def get_email_details(service, msg_id: str) -> Optional[Dict]:
    """
    Get full details of a single email.
    
    Args:
        service: Authenticated Gmail API service object
        msg_id: Gmail message ID
    
    Returns:
        Dictionary with email details or None if error
    """
    try:
        # Fetch full message
        message = service.users().messages().get(
            userId='me',
            id=msg_id,
            format='full'
        ).execute()
        
        # Extract headers
        headers = message.get('payload', {}).get('headers', [])
        
        subject = ""
        sender = ""
        date = ""
        
        for header in headers:
            name = header.get('name', '').lower()
            if name == 'subject':
                subject = header.get('value', '')
            elif name == 'from':
                sender = header.get('value', '')
            elif name == 'date':
                date = header.get('value', '')
        
        # Extract body
        body = extract_body(message.get('payload', {}))
        
        return {
            'id': msg_id,
            'subject': subject,
            'sender': sender,
            'date': date,
            'body': body,
            'snippet': message.get('snippet', '')
        }
        
    except Exception as e:
        print(f"   ⚠ Error fetching message {msg_id}: {e}")
        return None


def extract_body(payload: Dict) -> str:
    """
    Extract email body from payload, handling multipart messages.
    
    Args:
        payload: Gmail message payload
    
    Returns:
        Cleaned plain text body
    """
    body_html = ""
    body_text = ""
    
    # Check if message has parts (multipart)
    parts = payload.get('parts', [])
    
    if parts:
        # Multipart message - extract text/html and text/plain
        for part in parts:
            mime_type = part.get('mimeType', '')
            
            if mime_type == 'text/plain':
                data = part.get('body', {}).get('data', '')
                if data:
                    body_text = decode_base64(data)
            
            elif mime_type == 'text/html':
                data = part.get('body', {}).get('data', '')
                if data:
                    body_html = decode_base64(data)
            
            # Handle nested multipart
            elif 'multipart' in mime_type:
                nested_parts = part.get('parts', [])
                for nested_part in nested_parts:
                    nested_mime = nested_part.get('mimeType', '')
                    nested_data = nested_part.get('body', {}).get('data', '')
                    
                    if nested_data:
                        if nested_mime == 'text/plain':
                            body_text = decode_base64(nested_data)
                        elif nested_mime == 'text/html':
                            body_html = decode_base64(nested_data)
    else:
        # Single part message
        data = payload.get('body', {}).get('data', '')
        mime_type = payload.get('mimeType', '')
        
        if data:
            decoded = decode_base64(data)
            if mime_type == 'text/html':
                body_html = decoded
            else:
                body_text = decoded
    
    # Prefer HTML (after cleaning) over plain text for better content
    if body_html:
        return clean_html(body_html)
    elif body_text:
        return body_text.strip()
    
    return ""


def decode_base64(data: str) -> str:
    """
    Decode base64 URL-safe encoded data.
    
    Args:
        data: Base64 URL-safe encoded string
    
    Returns:
        Decoded UTF-8 string
    """
    try:
        # Gmail uses URL-safe base64 encoding
        decoded_bytes = base64.urlsafe_b64decode(data)
        return decoded_bytes.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"   ⚠ Base64 decode error: {e}")
        return ""


def clean_html(html_content: str) -> str:
    """
    Clean HTML content and extract readable text using BeautifulSoup.
    
    Args:
        html_content: Raw HTML string
    
    Returns:
        Clean plain text
    """
    try:
        # Parse HTML
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Remove script and style elements
        for element in soup(['script', 'style', 'head', 'meta', 'link']):
            element.decompose()
        
        # Get text
        text = soup.get_text(separator=' ')
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
        
    except Exception as e:
        print(f"   ⚠ HTML cleaning error: {e}")
        # Fallback: return raw content with tags stripped
        return html_content


# Utility functions for filtering

def fetch_emails_by_days(service, days: int = 30, max_results: int = 100) -> List[Dict]:
    """
    Fetch emails from the last N days.
    
    Args:
        service: Authenticated Gmail API service object
        days: Number of days to look back
        max_results: Maximum number of emails to fetch
    
    Returns:
        List of email dictionaries
    """
    query = f"newer_than:{days}d"
    return fetch_emails(service, max_results=max_results, query=query)


def fetch_emails_from_sender(service, sender: str, max_results: int = 50) -> List[Dict]:
    """
    Fetch emails from a specific sender.
    
    Args:
        service: Authenticated Gmail API service object
        sender: Email address or name to search for
        max_results: Maximum number of emails to fetch
    
    Returns:
        List of email dictionaries
    """
    query = f"from:{sender}"
    return fetch_emails(service, max_results=max_results, query=query)


# For testing this module directly
if __name__ == "__main__":
    from auth import get_gmail_service
    
    print("=" * 50)
    print("Gmail Reader Test")
    print("=" * 50)
    
    try:
        # Authenticate
        service = get_gmail_service()
        
        # Fetch last 5 emails for testing
        emails = fetch_emails(service, max_results=5)
        
        print("\n" + "=" * 50)
        print("FETCHED EMAILS:")
        print("=" * 50)
        
        for i, email in enumerate(emails, 1):
            print(f"\n--- Email {i} ---")
            print(f"Subject: {email['subject']}")
            print(f"From: {email['sender']}")
            print(f"Date: {email['date']}")
            print(f"Body preview: {email['body'][:200]}..." if len(email['body']) > 200 else f"Body: {email['body']}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
