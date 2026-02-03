# app.py - Flask Web Application for Email Analyzer
# ==================================================
# Web interface for the Gmail Email Analyzer

"""
Flask Web Application for Gmail Email Analysis

This web app provides:
- Google OAuth 2.0 authentication via web flow
- Email fetching and analysis
- Beautiful web interface to view results
- Session management for multiple users
"""

import os
import json
import secrets
from flask import Flask, render_template, redirect, url_for, session, request, jsonify
from flask_session import Session
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from gmail_reader import fetch_emails, fetch_emails_by_days
# Use generalized patterns that work for ANY store/card/membership
from patterns_generalized import analyze_text
from analyzer import (
    extract_membership_name,
    extract_credit_card_name,
    extract_company_name,
    analyze_emails
)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32))

# Server-side session configuration (fixes cookie size limit issue)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './flask_session'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Initialize server-side sessions
Session(app)

# Gmail API scope - read-only access to emails
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# OAuth 2.0 credentials file
CLIENT_SECRETS_FILE = 'credentials.json'

# Get base URL from environment (for production) or use localhost
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:8080')

# For development, allow HTTP (change to False in production with HTTPS)
if BASE_URL.startswith('http://localhost'):
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


def get_flow():
    """Create OAuth 2.0 flow for web application."""
    redirect_uri = f"{BASE_URL}/oauth/callback"
    
    # Try to load credentials from file first, then from environment variable
    if os.path.exists(CLIENT_SECRETS_FILE):
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
    elif os.environ.get('GOOGLE_CREDENTIALS'):
        # Load credentials from environment variable (for Render deployment)
        credentials_info = json.loads(os.environ.get('GOOGLE_CREDENTIALS'))
        flow = Flow.from_client_config(
            credentials_info,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
    else:
        raise FileNotFoundError("credentials.json not found and GOOGLE_CREDENTIALS env var not set")
    
    return flow


def credentials_to_dict(credentials):
    """Convert credentials object to dictionary for session storage."""
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }


def get_gmail_service():
    """Get authenticated Gmail service from session credentials."""
    if 'credentials' not in session:
        return None
    
    credentials = Credentials(**session['credentials'])
    
    # Refresh token if expired
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        session['credentials'] = credentials_to_dict(credentials)
    
    return build('gmail', 'v1', credentials=credentials)


@app.route('/')
def index():
    """Home page - show login or dashboard."""
    if 'credentials' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/login')
def login():
    """Initiate OAuth 2.0 login flow."""
    flow = get_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    session['state'] = state
    return redirect(authorization_url)


@app.route('/oauth/callback')
def oauth_callback():
    """Handle OAuth 2.0 callback."""
    flow = get_flow()
    flow.fetch_token(authorization_response=request.url)
    
    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    
    # Get user email
    service = build('gmail', 'v1', credentials=credentials)
    profile = service.users().getProfile(userId='me').execute()
    session['user_email'] = profile.get('emailAddress', 'Unknown')
    
    return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    """Clear session and logout."""
    session.clear()
    return redirect(url_for('index'))


@app.route('/dashboard')
def dashboard():
    """Main dashboard - show analysis options."""
    if 'credentials' not in session:
        return redirect(url_for('login'))
    
    user_email = session.get('user_email', 'Unknown')
    return render_template('dashboard.html', user_email=user_email)


@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze emails based on user parameters."""
    if 'credentials' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    service = get_gmail_service()
    if not service:
        return jsonify({'error': 'Failed to get Gmail service'}), 500
    
    # Get parameters from request
    num_emails = request.form.get('num_emails', 50, type=int)
    days = request.form.get('days', None, type=int)
    strict_mode = request.form.get('strict_mode', 'false') == 'true'
    
    try:
        # Fetch emails
        if days:
            emails = fetch_emails_by_days(service, days=days, max_results=num_emails)
        else:
            emails = fetch_emails(service, max_results=num_emails)
        
        if not emails:
            return jsonify({'error': 'No emails found'}), 404
        
        # Analyze emails with OCR enabled
        results = analyze_emails(emails, strict_mode=strict_mode, enable_ocr=True)
        
        # Process results for web display
        processed_results = process_results_for_web(results)
        
        # Store in session for viewing
        session['analysis_results'] = processed_results
        session.modified = True  # Ensure session is saved
        
        print(f"✓ Analysis complete. Stored {len(processed_results)} result categories")
        print(f"   Session keys after storage: {list(session.keys())}")
        
        return jsonify({
            'success': True,
            'redirect': url_for('results')
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def extract_membership_dates(subject, body, date):
    """Extract start_date and expiry_date from membership email."""
    import re
    from datetime import datetime, timedelta
    
    text = f"{subject} {body}"
    
    # Try to find explicit dates in the email
    # Pattern: "valid from X to Y", "expires on X", "renewable on X", etc.
    date_patterns = [
        r'(?:valid from|starts?(?:\s+on)?)[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
        r'(?:expires?|expiry|ends?)[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
        r'(?:renewable on|renews? on)[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
    ]
    
    start_date = None
    expiry_date = None
    
    # Try to parse the email date as start date
    try:
        # Parse email date format: "Wed, 21 Jan 2026 11:25:22 +0530"
        parsed_date = datetime.strptime(date.split(',')[1].strip().split(' +')[0], '%d %b %Y %H:%M:%S')
        start_date = parsed_date.strftime('%B %d, %Y')
        # Calculate expiry as 1 year from start
        expiry_parsed = parsed_date + timedelta(days=365)
        expiry_date = expiry_parsed.strftime('%B %d, %Y')
    except:
        # If parsing fails, use a default
        start_date = date.split(',')[1].strip().split(' ')[0:3]
        start_date = ' '.join(start_date) if len(start_date) >= 3 else date
    
    return start_date, expiry_date


def process_results_for_web(results):
    """Process analysis results for web display - grouped by unique memberships/offers/coupons/giftcards."""
    
    # Group memberships by unique names
    memberships_dict = {}
    for email in results['membership']:
        membership_name = extract_membership_name(email['subject'], email.get('body', ''))
        if membership_name not in memberships_dict:
            start_date, expiry_date = extract_membership_dates(
                email['subject'], 
                email.get('body', ''), 
                email['date']
            )
            memberships_dict[membership_name] = {
                'from': email['sender'],
                'start_date': start_date,
                'expiry_date': expiry_date,
                'status': 'Active',
                'is_shopping_domain': email.get('is_shopping_domain', False)
            }
    
    # Group offers by unique card names
    offers_dict = {}
    for email in results['offer']:
        card_name = extract_credit_card_name(email['subject'], email.get('body', ''))
        if card_name not in offers_dict:
            offers_dict[card_name] = {
                'from': email['sender'],
                'date': email['date'],
                'status': 'Active',
                'is_shopping_domain': email.get('is_shopping_domain', False)
            }
    
    # Show ALL gift cards (each has unique card number, PIN, value)
    giftcards_list = []
    for idx, email in enumerate(results.get('giftcard', [])):
        # Priority: footer_store_name > image_stores > extract_company_name
        store_name = email.get('footer_store_name')
        if not store_name:
            image_stores = email.get('image_stores', [])
            store_name = image_stores[0] if image_stores else None
        if not store_name:
            store_name = extract_company_name(email['sender'], email['subject'], email.get('body', ''))
        
        giftcard_details = email.get('giftcard_details', {})
        
        giftcards_list.append({
            'id': idx,
            'store_name': store_name,
            'subject': email['subject'],
            'from': email['sender'],
            'date': email['date'],
            'card_number': giftcard_details.get('card_number'),
            'pin': giftcard_details.get('pin'),
            'value': giftcard_details.get('value'),
            'is_shopping_domain': email.get('is_shopping_domain', False)
        })
    
    # Show ALL coupons (each has different promo codes, discounts, expiry dates)
    coupons_list = []
    for idx, email in enumerate(results['coupon']):
        # Priority: footer_store_name > image_stores > extract_company_name
        store_name = email.get('footer_store_name')
        if not store_name:
            image_stores = email.get('image_stores', [])
            store_name = image_stores[0] if image_stores else None
        if not store_name:
            store_name = extract_company_name(email['sender'], email['subject'], email.get('body', ''))
        
        # Extract offer details from footer_offers
        footer_offers = email.get('footer_offers', {})
        promo_codes = footer_offers.get('promo_codes', [])
        discounts = footer_offers.get('discounts', [])
        discount_details = footer_offers.get('discount_details', [])
        expiry_date = footer_offers.get('expiry_date')
        
        coupons_list.append({
            'id': idx,
            'store_name': store_name,
            'subject': email['subject'],
            'from': email['sender'],
            'date': email['date'],
            'promo_codes': promo_codes,
            'discounts': discounts,
            'discount_details': discount_details,
            'expiry_date': expiry_date,
            'is_shopping_domain': email.get('is_shopping_domain', False)
        })
    
    processed = {
        'summary': {
            'total': sum(len(v) for k, v in results.items() if k != 'excluded'),
            'membership': len(memberships_dict),
            'offer': len(offers_dict),
            'giftcard': len(giftcards_list),
            'coupon': len(coupons_list),
            'normal': len(results['normal']),
            'excluded': len(results.get('excluded', []))
        },
        'membership': memberships_dict,
        'offer': offers_dict,
        'giftcard': giftcards_list,
        'coupon': coupons_list,
        'normal': results['normal'][:10]  # Keep original format for normal emails
    }
    
    return processed


@app.route('/results')
def results():
    """Display analysis results."""
    if 'credentials' not in session:
        print("❌ Results: No credentials in session")
        return redirect(url_for('login'))
    
    if 'analysis_results' not in session:
        print("❌ Results: No analysis_results in session")
        print(f"   Session keys: {list(session.keys())}")
        return redirect(url_for('dashboard'))
    
    results = session['analysis_results']
    user_email = session.get('user_email', 'Unknown')
    
    print(f"✓ Displaying results for {user_email}")
    return render_template('results.html', results=results, user_email=user_email)


@app.route('/api/results')
def api_results():
    """API endpoint to get analysis results as JSON."""
    if 'credentials' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if 'analysis_results' not in session:
        return jsonify({'error': 'No results available'}), 404
    
    return jsonify(session['analysis_results'])


# Error handlers
@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', error='Page not found'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', error='Server error'), 500


if __name__ == '__main__':
    # Check if credentials.json exists or GOOGLE_CREDENTIALS env var is set
    if not os.path.exists(CLIENT_SECRETS_FILE) and not os.environ.get('GOOGLE_CREDENTIALS'):
        print("❌ Error: credentials.json not found and GOOGLE_CREDENTIALS env var not set!")
        print("\nTo use this web app, you need to:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create/select a project")
        print("3. Enable Gmail API")
        print("4. Go to APIs & Services → Credentials")
        print("5. Click 'Create Credentials' → 'OAuth client ID'")
        print("6. Select Application type: 'Web application'")
        print("7. Add authorized redirect URI (local or production)")
        print("   - Local: http://localhost:8080/oauth/callback")
        print("   - Production: https://your-app.onrender.com/oauth/callback")
        print("8. Download credentials.json OR set GOOGLE_CREDENTIALS env var")
        exit(1)
    
    # Get port from environment (for production) or use 8080
    port = int(os.environ.get('PORT', 8080))
    
    print("=" * 60)
    print("📧 EMAIL ANALYZER WEB APP")
    print("=" * 60)
    print(f"\n🌐 Starting web server on port {port}...")
    print(f"   Base URL: {BASE_URL}")
    print("\n⚠️  Make sure your Google OAuth credentials are set up for web application!")
    print(f"   Add this redirect URI: {BASE_URL}/oauth/callback")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=port)
