#!/usr/bin/env python3
"""Debug footer store name extraction"""

from gmail_reader import fetch_emails
from auth import get_gmail_service
from analyzer import extract_company_name
from footer_extractor import get_enhanced_email_data, extract_store_name_from_footer

# Get emails
service = get_gmail_service()
emails = fetch_emails(service, max_results=50, query='newer_than:30d')
print(f'Found {len(emails)} emails\n')

# Check each email for footer store extraction
for email in emails:
    sender = email.get('sender', '')
    subject = email.get('subject', '')
    body = email.get('body', '')
    
    # Get footer data
    footer_data = get_enhanced_email_data(body, sender, subject)
    footer_store = footer_data.get('store_name')
    
    # Get domain extraction
    domain_store = extract_company_name(sender, subject, body)
    
    # Only show emails where footer extraction failed but should work
    if '@innovinlabs.com' in sender.lower():
        print(f'📧 Email from: {sender[:70]}')
        print(f'   Subject: {subject[:70]}')
        print(f'   Domain Store: {domain_store}')
        print(f'   Footer Store: {footer_store}')
        print(f'   Body length: {len(body)} chars')
        # Show last 500 chars of body (footer area)
        if body and len(body) > 0:
            footer_snippet = body[-500:] if len(body) > 500 else body
            print(f'   Footer snippet (last 300 chars):')
            print(f'   {footer_snippet[-300:]}')
        print('-' * 80)
        print()
