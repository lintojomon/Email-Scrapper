# export_json.py - Export email analysis to structured JSON
# =========================================================

"""
Export email analysis results to a structured JSON format.

Structure:
{
    "user_email": {
        "membership": {
            "Walmart+": { details... },
            "Amazon Prime": { details... }
        },
        "offer": {
            "Delta SkyMiles Card": { details... }
        },
        "coupon": {
            "Walmart": [
                { "coupon": "15% Off", details... }
            ]
        }
    }
}
"""

import json
import re
from typing import Dict, List, Any, Tuple
from datetime import datetime


def extract_membership_dates(body: str) -> Tuple[str, str]:
    """
    Extract start date and expiry date from membership email body.
    
    Args:
        body: Email body content
    
    Returns:
        Tuple of (start_date, expiry_date) strings
    """
    start_date = ""
    expiry_date = ""
    
    # Common date patterns
    # "Start Date: January 20, 2026"
    # "Expiry Date: January 19, 2027"
    # "Valid from: 01/20/2026"
    # "Expires: 01/19/2027"
    # "Membership Start: Jan 20, 2026"
    # "Renewal Date: January 19, 2027"
    
    # Pattern for various date formats
    date_pattern = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{4}[/\-]\d{1,2}[/\-]\d{1,2}'
    
    # Start date patterns
    start_patterns = [
        rf'(?:Start\s*Date|Membership\s*Start|Valid\s*from|Starts?\s*on|Effective\s*Date|Begin(?:s|ning)?\s*Date)\s*[:\s]+({date_pattern})',
        rf'(?:Started|Activated)\s*(?:on)?\s*[:\s]+({date_pattern})',
    ]
    
    # Expiry date patterns
    expiry_patterns = [
        rf'(?:Expiry\s*Date|Expiration\s*Date|Expires?\s*on|Valid\s*(?:until|through|till)|End\s*Date|Renewal\s*Date|Next\s*Renewal)\s*[:\s]+({date_pattern})',
        rf'(?:Expires?|Renews?)\s*[:\s]+({date_pattern})',
    ]
    
    # Search for start date
    for pattern in start_patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            start_date = match.group(1).strip()
            break
    
    # Search for expiry date
    for pattern in expiry_patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            expiry_date = match.group(1).strip()
            break
    
    return start_date, expiry_date


def extract_coupon_description(subject: str) -> str:
    """
    Extract the coupon/offer description from email subject.
    
    Args:
        subject: Email subject line
    
    Returns:
        Coupon description string
    """
    # Remove emojis and clean up
    subject = re.sub(r'[🎉🛒💰🔥✨💸🏷️]', '', subject).strip()
    
    # Try to extract the offer part
    patterns = [
        r'(Save \$?\d+[%]?.*?)(?:\s*[—–-]\s*|$)',
        r'((?:\d+%|₹\d+|\$\d+)\s*(?:Off|Discount|Cashback).*?)(?:\s*[—–-]\s*|$)',
        r'(Enjoy \d+%.*?)(?:\s*[—–-]\s*|$)',
        r'(Get \d+%.*?)(?:\s*[—–-]\s*|$)',
        r'(Free Shipping.*?)(?:\s*[—–-]\s*|$)',
        r'(Buy \d+ Get \d+.*?)(?:\s*[—–-]\s*|$)',
        r'(Flat \d+%.*?)(?:\s*[—–-]\s*|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, subject, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    # If no pattern matches, return cleaned subject
    # Remove common prefixes
    subject = re.sub(r'^(Welcome!?\s*|Hey!?\s*|Hi!?\s*)', '', subject, flags=re.IGNORECASE)
    return subject.strip()


def extract_coupon_details(body: str) -> Tuple[str, str]:
    """
    Extract coupon code and validity from email body.
    
    Args:
        body: Email body content
    
    Returns:
        Tuple of (coupon_code, validity) strings
    """
    coupon_code = ""
    validity = ""
    
    # Coupon code patterns
    code_patterns = [
        r'(?:Coupon\s*Code|Promo\s*Code|Code|Use\s*Code|Discount\s*Code|Offer\s*Code)\s*[:\s]+([A-Z0-9]{4,20})',
        r'(?:Code|Coupon)\s*[:\s]*["\']?([A-Z0-9]{4,20})["\']?',
        r'(?:Apply|Enter|Use)\s+(?:code\s+)?["\']?([A-Z0-9]{4,20})["\']?',
    ]
    
    # Validity patterns
    validity_patterns = [
        r'(?:Valid(?:ity)?|Expires?|Valid\s*(?:until|through|till)|Offer\s*(?:valid|ends)|Expiry)\s*[:\s]+(.+?)(?:\n|$)',
        r'(?:Valid\s*(?:from|until|through|till))\s*[:\s]+(.+?)(?:\n|$)',
        r'(?:Offer\s*ends?|Expires?\s*on)\s*[:\s]+(.+?)(?:\n|$)',
    ]
    
    # Search for coupon code
    for pattern in code_patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            coupon_code = match.group(1).strip()
            break
    
    # Search for validity
    for pattern in validity_patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            validity = match.group(1).strip()
            # Clean up validity string
            validity = re.sub(r'\s+', ' ', validity)
            if len(validity) > 50:  # Truncate if too long
                validity = validity[:50] + "..."
            break
    
    return coupon_code, validity


def create_structured_json(results: Dict[str, List[Dict]], 
                           user_email: str,
                           membership_extractor,
                           card_extractor,
                           company_extractor) -> Dict:
    """
    Create a structured JSON from analysis results.
    
    Args:
        results: Dictionary with categorized emails
        user_email: The email ID from which emails were fetched
        membership_extractor: Function to extract membership name
        card_extractor: Function to extract credit card name
        company_extractor: Function to extract company/store name
    
    Returns:
        Structured dictionary for JSON export
    """
    output = {
        user_email: {
            "fetched_at": datetime.now().isoformat(),
            "summary": {
                "total_membership": len(results.get('membership', [])),
                "total_offer": len(results.get('offer', [])),
                "total_coupon": len(results.get('coupon', []))
            },
            "membership": {},
            "offer": {},
            "coupon": {}
        }
    }
    
    data = output[user_email]
    
    # Process Memberships
    for email in results.get('membership', []):
        membership_name = membership_extractor(email.get('subject', ''), email.get('body', ''))
        # Extract dates from email body
        body = email.get('body', '')
        start_date, expiry_date = extract_membership_dates(body)
        
        # If no start date found in body, use email date as fallback
        if not start_date:
            start_date = email.get('date', '')
        
        data["membership"][membership_name] = {
            "from": email.get('sender', ''),
            "start_date": start_date,
            "expiry_date": expiry_date,
            "status": "Active"
        }
    
    # Process Offers (Credit Cards)
    for email in results.get('offer', []):
        card_name = card_extractor(email.get('subject', ''), email.get('body', ''))
        data["offer"][card_name] = {
            "from": email.get('sender', ''),
            "date": email.get('date', ''),
            "status": "Active"
        }
    
    # Process Coupons (grouped by store)
    for email in results.get('coupon', []):
        store_name = company_extractor(email.get('sender', ''), email.get('subject', ''), email.get('body', ''))
        coupon_desc = extract_coupon_description(email.get('subject', ''))
        
        # Extract coupon code and validity from body
        body = email.get('body', '')
        coupon_code, validity = extract_coupon_details(body)
        
        if store_name not in data["coupon"]:
            data["coupon"][store_name] = []
        
        data["coupon"][store_name].append({
            "coupon": coupon_desc,
            "coupon_code": coupon_code,
            "validity": validity
        })
    
    return output


def export_to_json(results: Dict[str, List[Dict]], 
                   user_email: str,
                   membership_extractor,
                   card_extractor,
                   company_extractor,
                   output_file: str = "email_analysis.json") -> str:
    """
    Export analysis results to a JSON file.
    
    Args:
        results: Dictionary with categorized emails
        user_email: The email ID from which emails were fetched
        membership_extractor: Function to extract membership name
        card_extractor: Function to extract credit card name
        company_extractor: Function to extract company/store name
        output_file: Output JSON filename
    
    Returns:
        Path to the created JSON file
    """
    structured_data = create_structured_json(
        results, user_email, 
        membership_extractor, card_extractor, company_extractor
    )
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(structured_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ JSON exported to: {output_file}")
    return output_file


def generate_html_viewer(json_file: str = "email_analysis.json", 
                         output_file: str = "email_viewer.html") -> str:
    """
    Generate an HTML viewer with interactive dropdowns.
    
    Args:
        json_file: Input JSON file
        output_file: Output HTML filename
    
    Returns:
        Path to the created HTML file
    """
    # Read the JSON data
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Analysis Viewer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .header .email-id {
            background: rgba(255,255,255,0.2);
            padding: 10px 20px;
            border-radius: 20px;
            display: inline-block;
        }
        .summary {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        .summary-card {
            background: white;
            padding: 20px 30px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            min-width: 150px;
        }
        .summary-card .count {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }
        .summary-card .label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
        }
        .categories {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }
        .category-card {
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .category-header {
            padding: 20px;
            color: white;
            font-size: 1.3em;
            font-weight: bold;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .category-header .icon {
            font-size: 1.5em;
        }
        .category-header .arrow {
            transition: transform 0.3s;
        }
        .category-header.expanded .arrow {
            transform: rotate(180deg);
        }
        .membership-header { background: linear-gradient(135deg, #11998e, #38ef7d); }
        .offer-header { background: linear-gradient(135deg, #ee0979, #ff6a00); }
        .coupon-header { background: linear-gradient(135deg, #4776E6, #8E54E9); }
        
        .category-content {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }
        .category-content.expanded {
            max-height: 2000px;
        }
        .item {
            padding: 15px 20px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
            transition: background 0.2s;
        }
        .item:hover {
            background: #f8f9fa;
        }
        .item:last-child {
            border-bottom: none;
        }
        .item-name {
            font-weight: 600;
            color: #333;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .item-name .badge {
            background: #667eea;
            color: white;
            padding: 3px 10px;
            border-radius: 10px;
            font-size: 0.8em;
        }
        .item-details {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
            margin-top: 0;
        }
        .item-details.expanded {
            max-height: 500px;
            margin-top: 10px;
        }
        .detail-row {
            padding: 8px 0;
            color: #666;
            font-size: 0.9em;
            border-top: 1px dashed #eee;
        }
        .detail-row:first-child {
            border-top: none;
        }
        .detail-label {
            font-weight: 600;
            color: #888;
            display: inline-block;
            width: 80px;
        }
        .store-item {
            background: #f8f9fa;
            margin: 10px;
            border-radius: 10px;
            overflow: hidden;
        }
        .store-header {
            padding: 15px;
            background: #e9ecef;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .store-header:hover {
            background: #dee2e6;
        }
        .coupon-list {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }
        .coupon-list.expanded {
            max-height: 1000px;
        }
        .coupon-item {
            padding: 12px 15px;
            border-bottom: 1px solid #dee2e6;
            background: white;
        }
        .coupon-item:last-child {
            border-bottom: none;
        }
        .coupon-name {
            color: #4776E6;
            font-weight: 600;
            margin-bottom: 5px;
        }
        .coupon-date {
            color: #888;
            font-size: 0.85em;
        }
        .no-items {
            padding: 20px;
            text-align: center;
            color: #888;
        }
    </style>
</head>
<body>
    <div class="container">
'''
    
    # Get the user email (first key)
    user_email = list(data.keys())[0]
    user_data = data[user_email]
    
    html_content += f'''
        <div class="header">
            <h1>📧 Email Analysis</h1>
            <div class="email-id">📬 {user_email}</div>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <div class="count">{user_data['summary']['total_membership']}</div>
                <div class="label">Memberships</div>
            </div>
            <div class="summary-card">
                <div class="count">{user_data['summary']['total_offer']}</div>
                <div class="label">Credit Cards</div>
            </div>
            <div class="summary-card">
                <div class="count">{user_data['summary']['total_coupon']}</div>
                <div class="label">Coupons</div>
            </div>
        </div>
        
        <div class="categories">
'''
    
    # Membership Section
    html_content += '''
            <div class="category-card">
                <div class="category-header membership-header" onclick="toggleCategory(this)">
                    <span><span class="icon">🔔</span> Memberships</span>
                    <span class="arrow">▼</span>
                </div>
                <div class="category-content">
'''
    
    if user_data['membership']:
        for name, details in user_data['membership'].items():
            expiry = details.get('expiry_date', '') or 'Not specified'
            html_content += f'''
                    <div class="item" onclick="toggleDetails(this)">
                        <div class="item-name">
                            <span>{name}</span>
                            <span class="badge">Active</span>
                        </div>
                        <div class="item-details">
                            <div class="detail-row"><span class="detail-label">Start Date:</span> {details.get('start_date', '')}</div>
                            <div class="detail-row"><span class="detail-label">Expiry Date:</span> {expiry}</div>
                            <div class="detail-row"><span class="detail-label">From:</span> {details['from']}</div>
                        </div>
                    </div>
'''
    else:
        html_content += '<div class="no-items">No memberships found</div>'
    
    html_content += '''
                </div>
            </div>
'''
    
    # Offer Section
    html_content += '''
            <div class="category-card">
                <div class="category-header offer-header" onclick="toggleCategory(this)">
                    <span><span class="icon">💳</span> Credit Card Offers</span>
                    <span class="arrow">▼</span>
                </div>
                <div class="category-content">
'''
    
    if user_data['offer']:
        for name, details in user_data['offer'].items():
            html_content += f'''
                    <div class="item" onclick="toggleDetails(this)">
                        <div class="item-name">
                            <span>{name}</span>
                            <span class="badge">Active</span>
                        </div>
                        <div class="item-details">
                            <div class="detail-row"><span class="detail-label">From:</span> {details['from']}</div>
                            <div class="detail-row"><span class="detail-label">Date:</span> {details['date']}</div>
                        </div>
                    </div>
'''
    else:
        html_content += '<div class="no-items">No credit card offers found</div>'
    
    html_content += '''
                </div>
            </div>
'''
    
    # Coupon Section
    html_content += '''
            <div class="category-card">
                <div class="category-header coupon-header" onclick="toggleCategory(this)">
                    <span><span class="icon">🏷️</span> Coupons</span>
                    <span class="arrow">▼</span>
                </div>
                <div class="category-content">
'''
    
    if user_data['coupon']:
        for store, coupons in user_data['coupon'].items():
            html_content += f'''
                    <div class="store-item">
                        <div class="store-header" onclick="toggleStore(this)">
                            <span>🏪 {store}</span>
                            <span>({len(coupons)} coupon{'s' if len(coupons) > 1 else ''}) ▼</span>
                        </div>
                        <div class="coupon-list">
'''
            for coupon in coupons:
                coupon_code = coupon.get('coupon_code', '') or 'N/A'
                validity = coupon.get('validity', '') or 'N/A'
                html_content += f'''
                            <div class="coupon-item">
                                <div class="coupon-name">🎟️ {coupon['coupon']}</div>
                                <div class="coupon-code">🔑 Code: <strong>{coupon_code}</strong></div>
                                <div class="coupon-validity">⏰ Valid: {validity}</div>
                            </div>
'''
            html_content += '''
                        </div>
                    </div>
'''
    else:
        html_content += '<div class="no-items">No coupons found</div>'
    
    html_content += '''
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function toggleCategory(header) {
            header.classList.toggle('expanded');
            const content = header.nextElementSibling;
            content.classList.toggle('expanded');
        }
        
        function toggleDetails(item) {
            event.stopPropagation();
            const details = item.querySelector('.item-details');
            details.classList.toggle('expanded');
        }
        
        function toggleStore(header) {
            event.stopPropagation();
            const couponList = header.nextElementSibling;
            couponList.classList.toggle('expanded');
        }
        
        // Auto-expand all categories on load
        document.addEventListener('DOMContentLoaded', function() {
            document.querySelectorAll('.category-header').forEach(header => {
                header.classList.add('expanded');
                header.nextElementSibling.classList.add('expanded');
            });
        });
    </script>
</body>
</html>
'''
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ HTML viewer exported to: {output_file}")
    return output_file


if __name__ == "__main__":
    print("This module provides JSON export functionality.")
    print("Use: from export_json import export_to_json, generate_html_viewer")
