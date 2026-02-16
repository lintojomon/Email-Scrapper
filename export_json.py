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
    Enhanced to find renewal/expiry dates from store membership emails.
    
    Args:
        body: Email body content
    
    Returns:
        Tuple of (start_date, expiry_date) strings
    """
    start_date = ""
    expiry_date = ""
    
    # Pattern for various date formats (including ordinal suffixes like "15th", "1st", "2nd")
    # Also match dates without year (like "April 15th")
    date_pattern = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{4}[/\-]\d{1,2}[/\-]\d{1,2}'
    
    # Start date patterns - more comprehensive
    start_patterns = [
        rf'(?:Start\s*Date|Membership\s*Start(?:ed)?|Valid\s*from|Starts?\s*on|Effective\s*Date|Begin(?:s|ning)?\s*Date|Activated\s*on|Member\s*since)\s*[:\s]+({date_pattern})',
        rf'(?:Started|Activated|Enrolled)\s*(?:on)?\s*[:\s]*({date_pattern})',
        rf'(?:Your\s+membership\s+(?:started|begins?)|Membership\s+active\s+from)\s*[:\s]*({date_pattern})',
    ]
    
    # Expiry/renewal date patterns - enhanced
    expiry_patterns = [
        rf'(?:Expiry\s*Date|Expiration\s*Date|Expires?\s*on|Valid\s*(?:until|through|till)|End\s*Date|Renewal\s*Date|Next\s*Renewal|Renew(?:al|s)?\s*(?:on|date)?)\s*[:\s]*({date_pattern})',
        rf'(?:Expires?|Renews?|Auto[-\s]?renew(?:s|al)?)\s*[:\s]*({date_pattern})',
        rf'(?:Your\s+membership\s+(?:expires?|renews?)|Membership\s+(?:expires?|valid)\s+(?:until|through|till)?)\s*[:\s]*({date_pattern})',
        rf'(?:Annual\s+fee\s+due|Payment\s+due)\s*[:\s]*({date_pattern})',
        # Catch "Renewal coming April 15th" or "Renews April 15th"
        rf'(?:Renewal\s+coming|Renews?\s+on|Due\s+on)\s+({date_pattern})',
        rf'(?:Membership\s+)?(?:expires?|renews?|valid\s+until)\s+({date_pattern})',
        # Catch promotional offer expiry dates like "thru Feb 28th" or "through March 15th"
        rf'(?:thru|through|until|till)\s+({date_pattern})',
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
            # If date doesn't have a year, add current/next year
            if re.match(r'^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2}(?:st|nd|rd|th)?$', expiry_date, re.IGNORECASE):
                from datetime import datetime
                current_year = datetime.now().year
                expiry_date = f"{expiry_date}, {current_year}"
            break
    
    # If no dates found, look for duration mentions (e.g., "annual", "1 year")
    if not expiry_date and start_date:
        duration_match = re.search(r'(?:annual|yearly|1\s*year|12\s*month)', body, re.IGNORECASE)
        if duration_match:
            # Calculate expiry as 1 year from start
            try:
                from datetime import datetime, timedelta
                if '/' in start_date or '-' in start_date:
                    # Parse MM/DD/YYYY or similar
                    parts = re.split(r'[/\-]', start_date)
                    if len(parts) == 3:
                        if len(parts[2]) == 4:  # YYYY
                            start_dt = datetime(int(parts[2]), int(parts[0]), int(parts[1]))
                        else:  # YY
                            start_dt = datetime(2000 + int(parts[2]), int(parts[0]), int(parts[1]))
                        expiry_dt = start_dt + timedelta(days=365)
                        expiry_date = expiry_dt.strftime("%B %d, %Y")
            except:
                pass
    
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
    
    # Validity patterns - enhanced to catch more date formats
    validity_patterns = [
        # Only match actual dates, not random "valid" text
        r'(?:Valid(?:ity)?|Expires?|Expiry)\s*[:\s]+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',
        r'(?:Valid(?:ity)?|Expires?|Expiry)\s*[:\s]+(\d{1,2}/\d{1,2}/\d{2,4})',
        r'(?:Valid\s*(?:from|until|through|till))\s*[:\s]+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',
        r'(?:Offer\s*ends?|Expires?\s*on|End(?:s|ing)\s*(?:on|date)?)\s*[:\s]*([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',
        # Time-based phrases - only specific ones
        r'(?:ends?\s+)((?:today|tonight|tomorrow|this\s+(?:week(?:end)?|month)|(?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day))',
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
                "total_giftcard": len(results.get('giftcard', [])),
                "total_coupon": len(results.get('coupon', []))
            },
            "membership": {},
            "offer": {},
            "giftcard": {},
            "coupon": {}
        }
    }
    
    data = output[user_email]
    
    # Process Memberships
    for email in results.get('membership', []):
        sender = email.get('sender', '')
        subject = email.get('subject', '')
        body = email.get('body', '')
        
        # Extract membership name (may be generic like "Membership")
        membership_name = membership_extractor(subject, body)
        
        # Try to extract store name from footer or subject for better identification
        footer_store = email.get('footer_store_name')
        
        # If membership name is generic, try to get store name
        if membership_name in ['Membership', 'Member', 'Subscriber']:
            # Priority: footer > domain
            if footer_store:
                membership_name = f"{footer_store} Membership"
            elif '@' in sender:
                # Try domain extraction
                domain_store = company_extractor(sender, subject, body)
                if domain_store and domain_store != "Unknown Store":
                    membership_name = f"{domain_store} Membership"
        
        # Extract description from subject and body
        description_parts = []
        
        # Check for discount/offer in subject or body
        discount_patterns = [
            r'(\d+%\s+off[^.]*)',
            r'(\$\d+\s+off[^.]*)',
            r'(discount[^.]*)',
            r'(gift for you)',
            r'(anniversary[^.]*)',
            r'(birthday[^.]*)',
        ]
        
        for pattern in discount_patterns:
            match = re.search(pattern, subject + " " + body[:500], re.IGNORECASE)
            if match:
                desc = match.group(1).strip()
                if len(desc) < 100:  # Avoid too long descriptions
                    description_parts.append(desc)
                    break
        
        # Extract dates from email body (expiry/validity)
        start_date, expiry_date = extract_membership_dates(body)
        
        # Also check footer for expiry date
        footer_offers = email.get('footer_offers', {})
        if not expiry_date and footer_offers.get('expiry_date'):
            expiry_date = footer_offers['expiry_date']
        
        # If no start date found in body, use email date as fallback
        if not start_date:
            start_date = email.get('date', '')
        
        # Extract membership benefits
        membership_benefits = email.get('membership_benefits', [])
        
        data["membership"][membership_name] = {
            "from": sender,
            "subject": subject,
            "description": ' | '.join(description_parts) if description_parts else subject[:100],
            "start_date": start_date,
            "expiry_date": expiry_date if expiry_date else "No expiry",
            "status": "Active",
            "benefits": membership_benefits
        }
    
    # Process Gift Cards
    for email in results.get('giftcard', []):
        sender = email.get('sender', '')
        subject = email.get('subject', '')
        body = email.get('body', '')
        
        # Extract store name
        footer_store = email.get('footer_store_name')
        if footer_store:
            store_name = footer_store
        else:
            store_name = company_extractor(sender, subject, body)
            if store_name == "Unknown Store":
                store_name = "Gift Card"
        
        # Get gift card details
        giftcard_details = email.get('giftcard_details', {})
        
        # Create unique key with timestamp to handle multiple gift cards from same store
        timestamp = email.get('date', '')
        card_key = f"{store_name} - {timestamp[:16]}" if timestamp else store_name
        
        data["giftcard"][card_key] = {
            "from": sender,
            "subject": subject,
            "date": timestamp,
            "card_number": giftcard_details.get('card_number', 'N/A'),
            "pin": giftcard_details.get('pin', 'N/A'),
            "value": giftcard_details.get('value', 'N/A'),
            "redemption_url": giftcard_details.get('redemption_url', 'N/A'),
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
        # Priority for store name: Domain > Footer > Images
        # This matches the smart extraction flow in analyzer.py
        sender = email.get('sender', '')
        subject = email.get('subject', '')
        body = email.get('body', '')
        footer_store = email.get('footer_store_name')
        image_stores = email.get('image_stores', [])
        
        # 1. Try domain extraction first (skip test emails)
        store_name = None
        if '@innovinlabs.com' not in sender.lower():
            domain_store = company_extractor(sender, subject, body)
            if domain_store and domain_store != "Unknown Store":
                store_name = domain_store
        
        # 2. If no domain store, try footer
        if not store_name and footer_store:
            store_name = footer_store
        
        # 3. If no footer store, try images (OCR)
        if not store_name and image_stores:
            store_name = image_stores[0]
        
        # 4. Fallback to "Unknown Store"
        if not store_name:
            store_name = "Unknown Store"
        
        coupon_desc = extract_coupon_description(subject)
        
        # MERGE footer and image data - prioritize footer, supplement with OCR
        footer_offers = email.get('footer_offers', {})
        image_offers = email.get('image_offers', [])
        
        # Collect all offers (footer + image offers)
        all_offers = []
        
        # Primary offer from footer
        footer_discount = None
        if footer_offers.get('discount_details'):
            footer_discount = ', '.join(footer_offers['discount_details'])
        elif footer_offers.get('discounts'):
            footer_discount = ', '.join(footer_offers['discounts'])
        
        footer_promo = ', '.join(footer_offers['promo_codes']) if footer_offers.get('promo_codes') else None
        footer_expiry = footer_offers.get('expiry_date')
        footer_validity_terms = footer_offers.get('validity_terms', [])
        footer_points = footer_offers.get('points_rewards', [])
        
        # If we have footer data, add as first offer
        if footer_discount or footer_promo or footer_expiry or footer_validity_terms or footer_points:
            all_offers.append({
                'discount_details': footer_discount if footer_discount else None,
                'coupon_code': footer_promo if footer_promo else None,
                'expiry_date': footer_expiry if footer_expiry else None,
                'validity_terms': footer_validity_terms if footer_validity_terms else [],
                'points_rewards': footer_points if footer_points else [],
                'source': 'footer'
            })
        
        # Add image offers if they provide additional/missing information
        for img_offer in image_offers:
            discount = img_offer.get('discount')
            promo = img_offer.get('promo_code')
            expiry = img_offer.get('expiry_date')
            
            # Only add if it provides new/different information
            if discount or promo or expiry:
                # Check if this is a duplicate of existing offer
                is_duplicate = False
                for existing in all_offers:
                    # Consider it duplicate if discount matches
                    if existing['discount_details'] == discount:
                        is_duplicate = True
                        # But update if image has additional info
                        if promo and not existing['coupon_code']:
                            existing['coupon_code'] = promo
                        if expiry and not existing['expiry_date']:
                            existing['expiry_date'] = expiry
                        break
                
                if not is_duplicate:
                    all_offers.append({
                        'discount_details': discount if discount else None,
                        'coupon_code': promo if promo else None,
                        'expiry_date': expiry if expiry else None,
                        'validity_terms': [],  # OCR doesn't capture validity terms
                        'points_rewards': [],  # OCR doesn't capture points
                        'source': 'ocr'
                    })
        
        # Fallback: extract from body if no offers found
        if not all_offers:
            coupon_code_fallback, validity_fallback = extract_coupon_details(body)
            
            # Check subject for expiry info
            validity = validity_fallback
            if not validity:
                if re.search(r'(?:ends?\s+(?:today|tonight|tomorrow|this\s+week|friday|sunday|monday))', subject, re.IGNORECASE):
                    validity_match = re.search(r'(?:ends?\s+)((?:today|tonight|tomorrow|this\s+week(?:end)?|(?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day))', subject, re.IGNORECASE)
                    if validity_match:
                        validity = f"Ends {validity_match.group(1)}"
            
            all_offers.append({
                'discount_details': None,
                'coupon_code': coupon_code_fallback,
                'expiry_date': validity,
                'validity_terms': [],  # Fallback doesn't capture validity terms
                'points_rewards': [],  # Fallback doesn't capture points
                'source': 'body'
            })
        
        if store_name not in data["coupon"]:
            data["coupon"][store_name] = []
        
        # Add all offers for this store (supports multiple offers per email)
        for offer in all_offers:
            data["coupon"][store_name].append({
                "coupon": coupon_desc,
                "discount_details": offer['discount_details'] if offer['discount_details'] else None,
                "coupon_code": offer['coupon_code'] if offer['coupon_code'] else None,
                "validity": offer['expiry_date'] if offer['expiry_date'] else None,
                "expiry_date": offer['expiry_date'] if offer['expiry_date'] else None,
                "validity_terms": offer.get('validity_terms', []),
                "points_rewards": offer.get('points_rewards', []),
                "source": offer['source']  # Track where data came from: footer/ocr/body
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
        .coupon-terms, .coupon-rewards {
            color: #555;
            font-weight: 600;
            margin-top: 10px;
            margin-bottom: 5px;
        }
        .terms-list, .rewards-list {
            list-style: none;
            padding-left: 0;
            margin: 5px 0;
        }
        .terms-list li, .rewards-list li {
            padding: 5px 0;
            padding-left: 20px;
            position: relative;
            color: #666;
            font-size: 0.9em;
        }
        .terms-list li:before {
            content: '•';
            position: absolute;
            left: 5px;
            color: #4776E6;
        }
        .rewards-list li:before {
            content: '★';
            position: absolute;
            left: 5px;
            color: #FFD700;
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
                discount_details = coupon.get('discount_details', '')
                validity_terms = coupon.get('validity_terms', [])
                points_rewards = coupon.get('points_rewards', [])
                
                html_content += f'''
                            <div class="coupon-item">
                                <div class="coupon-name">🎟️ {coupon['coupon']}</div>
'''
                # Show discount details if available
                if discount_details:
                    html_content += f'''
                                <div class="coupon-code">💰 <strong>{discount_details}</strong></div>
'''
                
                html_content += f'''
                                <div class="coupon-code">🔑 Code: <strong>{coupon_code}</strong></div>
                                <div class="coupon-validity">⏰ Valid: {validity}</div>
'''
                # Show validity terms if available
                if validity_terms:
                    html_content += '''
                                <div class="coupon-terms">📋 Terms:</div>
                                <ul class="terms-list">
'''
                    for term in validity_terms:
                        html_content += f'''
                                    <li>{term}</li>
'''
                    html_content += '''
                                </ul>
'''
                
                # Show points/rewards if available
                if points_rewards:
                    html_content += '''
                                <div class="coupon-rewards">🎁 Rewards:</div>
                                <ul class="rewards-list">
'''
                    for reward in points_rewards:
                        html_content += f'''
                                    <li>{reward}</li>
'''
                    html_content += '''
                                </ul>
'''
                
                html_content += '''
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
