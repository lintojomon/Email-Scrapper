# auth.py - Google OAuth Authentication Module
# ============================================
# SECURITY NOTE: 
# - Only OAuth tokens are stored (token.json)
# - NO Gmail passwords are stored
# - Uses Gmail API (not scraping)
# - Works within Google security policies

"""
Google OAuth 2.0 Authentication for Gmail API

This module handles:
- OAuth 2.0 authentication flow using InstalledAppFlow
- Token persistence (save/load token.json)
- Automatic token refresh when expired
- Returns authenticated Gmail service object
"""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API scope - read-only access to emails
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# File paths for credentials and token
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'


def get_gmail_service():
    """
    Authenticate user and return Gmail API service object.
    
    Flow:
    1. Check if token.json exists (previously authenticated)
    2. If token exists, load and refresh if expired
    3. If no token, run OAuth flow (opens browser)
    4. Save token for future use
    5. Return authenticated Gmail service
    
    Returns:
        googleapiclient.discovery.Resource: Authenticated Gmail API service
    
    Raises:
        FileNotFoundError: If credentials.json is missing
    """
    creds = None
    
    # Step 1: Check if token.json exists (user previously authenticated)
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        print("✓ Loaded existing token from token.json")
    
    # Step 2: If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Token expired but refresh token available - refresh it
            print("⟳ Token expired, refreshing...")
            creds.refresh(Request())
            print("✓ Token refreshed successfully")
        else:
            # No valid token - run full OAuth flow
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"'{CREDENTIALS_FILE}' not found!\n"
                    "Please download it from Google Cloud Console:\n"
                    "1. Go to https://console.cloud.google.com/\n"
                    "2. Create/select a project\n"
                    "3. Enable Gmail API (APIs & Services → Library → Gmail API)\n"
                    "4. Go to APIs & Services → Credentials\n"
                    "5. Click 'Create Credentials' → 'OAuth client ID'\n"
                    "6. Select Application type: 'Desktop app' (NOT Web application)\n"
                    "7. Give it a name (e.g., 'Email Scraper')\n"
                    "8. Click Create and download the JSON\n"
                    "9. Save the downloaded file as 'credentials.json' in this folder"
                )
            
            print("🔐 Starting OAuth authentication flow...")
            print("   A browser window will open for Google sign-in.")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            # Run local server for OAuth callback
            creds = flow.run_local_server(port=0)
            print("✓ Authentication successful!")
        
        # Step 3: Save credentials for future runs
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            print(f"✓ Token saved to {TOKEN_FILE}")
    
    # Step 4: Build and return Gmail service
    service = build('gmail', 'v1', credentials=creds)
    print("✓ Gmail service initialized")
    
    return service


def revoke_token():
    """
    Revoke the current OAuth token and delete token.json.
    Useful for switching accounts or troubleshooting.
    """
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
        print(f"✓ Removed {TOKEN_FILE}")
        print("  You will need to re-authenticate on next run.")
    else:
        print(f"  No {TOKEN_FILE} found to remove.")


# For testing this module directly
if __name__ == "__main__":
    print("=" * 50)
    print("Gmail OAuth Authentication Test")
    print("=" * 50)
    
    try:
        service = get_gmail_service()
        
        # Quick test: Get user's email address
        profile = service.users().getProfile(userId='me').execute()
        print(f"\n✓ Authenticated as: {profile['emailAddress']}")
        print(f"  Total messages: {profile['messagesTotal']}")
        print(f"  Total threads: {profile['threadsTotal']}")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
