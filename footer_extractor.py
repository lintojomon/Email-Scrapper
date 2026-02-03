# footer_extractor.py - Email Footer Content Extraction
# =====================================================
# Extracts store names, promo codes, and offers from email footers

"""
Footer Extractor - Parse promotional content from email footers

Email footers often contain:
- Store/company names
- Promo codes (e.g., "Use code SAVE20")
- Offer terms and conditions
- Contact information
- Website URLs
"""

import re
from typing import Dict, List, Optional


def extract_footer_content(body: str, last_n_chars: int = 2000) -> Dict:
    """
    Extract promotional content from email footer.
    
    Args:
        body: Email body text
        last_n_chars: Number of characters from end to analyze (default: 2000)
    
    Returns:
        Dictionary with extracted footer content
    """
    # Get footer section (last N characters)
    footer = body[-last_n_chars:] if len(body) > last_n_chars else body
    
    result = {
        'store_name': None,
        'promo_codes': [],
        'website': None,
        'contact_email': None,
        'company_address': None
    }
    
    # Extract promo codes from footer
    # More specific patterns that require alphanumeric mix to avoid generic words
    promo_patterns = [
        # Must contain both letters and numbers (most common promo format)
        r'(?:use|enter|apply|with)\s+(?:code|promo)[\s:]+([A-Z]+\d+[A-Z0-9]*|[0-9]+[A-Z]+[A-Z0-9]*)\b',
        # Code with specific context words, requiring alphanumeric
        r'(?:discount|promo|coupon)\s+code[\s:]+([A-Z]+\d+[A-Z0-9]*|[0-9]+[A-Z]+[A-Z0-9]*)\b',
        # Standalone format: "CODE: SAVE20" but only if alphanumeric mix
        r'\b(?:code|promo)[\s:]+([A-Z]+\d+[A-Z0-9]{2,}|[0-9]+[A-Z]+[A-Z0-9]{2,})\b',
    ]
    
    false_positives = ['CODE', 'PROMO', 'THIS', 'THAT', 'YOUR', 'HERE', 
                      'ONLY', 'SAVE', 'CODES', 'BELOW', 'FIELD', 'TEXT',
                      'SHOP', 'LINK', 'EMAIL', 'MAIL', 'FROM', 'NAME', 'CHECKOUT',
                      'ONLINE', 'OFFER', 'GIFT', 'FREE', 'NOW', 'TODAY', 'WHEN',
                      'PHONE', 'NUMBER', 'SCAN', 'ENTER', 'WITH', 'HAVE', 'APPLY']
    
    for pattern in promo_patterns:
        matches = re.findall(pattern, footer, re.IGNORECASE)
        for match in matches:
            if match and len(match) >= 4:
                # Check if code has both letters and numbers
                has_letter = any(c.isalpha() for c in match)
                has_digit = any(c.isdigit() for c in match)
                
                # Only accept if it's alphanumeric mix or not in false positives
                if (has_letter and has_digit) and match.upper() not in false_positives:
                    result['promo_codes'].append(match.upper())
    
    # Remove duplicates
    result['promo_codes'] = list(set(result['promo_codes']))
    
    # Extract website URL
    url_pattern = r'https?://(?:www\.)?([a-zA-Z0-9-]+\.(?:com|net|org|co|shop|us|io))'
    url_matches = re.findall(url_pattern, footer, re.IGNORECASE)
    if url_matches:
        # Get unique URLs and take the last one (usually main site link)
        unique_urls = list(set(url_matches))
        # Prefer non-www, main domain URLs
        for url in reversed(unique_urls):
            if 'jcrew' in url.lower() or 'factory' in url.lower():
                result['website'] = url
                break
        if not result['website'] and unique_urls:
            result['website'] = unique_urls[-1]
    
    # Extract contact email
    email_pattern = r'\b([a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
    email_matches = re.findall(email_pattern, footer)
    if email_matches:
        # Filter out unsubscribe/list emails, prefer customer service emails
        for email in email_matches:
            if not any(skip in email.lower() for skip in ['unsubscribe', 'list-', 'bounce', 'return']):
                result['contact_email'] = email
                break
    
    # Extract company name from common footer patterns
    # Order matters - more specific patterns first
    company_patterns = [
        # COPYRIGHT patterns (highest priority - most reliable)
        # Matches: "© 2025 Nike, Inc." or "© 2025 Amazon.com, Inc." or "©2025 Walmart"
        r'©\s*\d{4}\s+([A-Z][A-Za-z0-9\.]+(?:\s+[A-Z][A-Za-z]+)*?)(?:,?\s+(?:Inc\.|LLC|Ltd\.|Corp\.|Corporation|Co\.))?(?:\s+All\s+Rights|\.|$)',
        # Matches: "Copyright 2025 Nike, Inc."
        r'Copyright\s+(?:©\s*)?\d{4}\s+([A-Z][A-Za-z0-9\.]+(?:\s+[A-Z][A-Za-z]+)*?)(?:,?\s+(?:Inc\.|LLC|Ltd\.|Corp\.|Corporation))?',
        # EMAIL SENT BY patterns (NEW - high priority for "sent by: Company, Inc.")
        r'This email (?:was sent by|is from)[:\s]+([A-Z][\w\s\.&]+?)(?:,\s*(?:Inc\.|LLC|Ltd\.|Corp\.))?(?:[,\.]|\s+\d)',
        # CUSTOMER SERVICE patterns
        r'([\w\s\.&]+)\s+Customer\s+(?:Relations|Service|Support|Care)',
        # REGISTERED TRADEMARK patterns (high priority)
        # Pattern 1: "Company Name® is a registered trademark" - must start after period/spaces or line start
        r'(?:\.|\s{2,})\s*([A-Z][\w\s\+\.&]{3,40}?)®\s+is\s+a\s+(?:registered\s+)?trademark',
        # Pattern 2: Generic trademark statement  
        r'(?:^|\.\s+)([A-Z][\w\s\+\.&®]{3,40}?)\s+is\s+a\s+(?:registered\s+)?trademark',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+reserves\s+the\s+right',
        # DIVISION patterns
        r'\(a division of\s+([A-Z][\w\s&\.]+?)(?:\s+Corp\.?|\s+Inc\.)?\)',
        r'a division of\s+([A-Z][\w\s&\.]+?)(?:\s+Corp\.?|\s+Inc\.?)?[,\.]',
        # GENERIC entity patterns with comma (e.g., "Sprouts Farmers Market, Inc.")
        r'([A-Z][\w\s\.&]+?)(?:,\s*(?:Inc\.|LLC|Ltd\.|Corp\.|Corporation))(?:[,\s]|$)',
        # GENERIC entity patterns without comma (lowest priority)
        r'([\w\s\.&]+)\s+(?:Inc\.|LLC|Ltd\.|Corp\.|Corporation)',
        # URL pattern (very low priority - extract from email domain)
        r'(?:unsubscribe|contact|visit)\s+(?:at\s+)?https?://(?:www\.)?([a-zA-Z0-9-]+)\.(?:com|net)',
    ]
    
    for pattern in company_patterns:
        match = re.search(pattern, footer, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            # Clean up company name - remove "Online" suffix if present
            company = re.sub(r'\s+Online$', '', company, flags=re.IGNORECASE)
            # Clean up trailing "Co" (from "Best Buy Co., Inc." -> "Best Buy")
            company = re.sub(r'\s+Co\.?$', '', company, flags=re.IGNORECASE)
            
            # Skip if it looks like a personal name (Firstname M. Lastname or Firstname Lastname pattern)
            # Personal names typically have 2-3 words with the middle one being a single letter with period
            name_pattern = r'^[A-Z][a-z]+\s+[A-Z]\.\s+[A-Z][a-z]+$|^[A-Z][a-z]+\s+[A-Z][a-z]+$'
            if re.match(name_pattern, company):
                continue  # Skip this match and try next pattern
            
            # Clean up company name
            if len(company) > 3 and len(company) < 50:
                result['store_name'] = company
                break
    
    # Extract company address (US format)
    address_pattern = r'\b(\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct|Circle|Cir|Crescent)[^,]*,\s*[A-Z]{2}[,\s]+\d{5}(?:-\d{4})?)'
    address_match = re.search(address_pattern, footer, re.IGNORECASE)
    if address_match:
        result['company_address'] = address_match.group(1).strip()
    
    return result


def extract_store_name_from_body(body: str) -> Optional[str]:
    """
    Extract store/company name from email body text using multiple patterns.
    Works for any store, not specific to any brand.
    
    Args:
        body: Email body text
    
    Returns:
        Store name string or None
    """
    # Priority 1: Look for store name at the beginning of email body
    # Many promotional emails start with the store name
    first_800 = body[:800]
    
    # First check for "Factory", "Outlet", "Plus" variants which are more specific
    # Includes single-letter brands like "J.Crew Factory"
    variant_pattern = r'\b([A-Z]\.?\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(Factory|Outlet|Plus|Express|Direct)\b'
    variant_match = re.search(variant_pattern, first_800)
    if variant_match:
        name = variant_match.group(0).strip()
        # Clean up spacing around dots (J. Crew -> J.Crew)
        name = re.sub(r'([A-Z])\.\s+', r'\1.', name)
        return name
    
    # NEW: Look for greeting patterns: "Hi, TIM! You're at <Store>" or "Hi from <Store>"
    greeting_patterns = [
        r"Hi[,!]\s+[A-Z]+[!,]\s+You['']re\s+(?:at\s+)?([A-Z][a-z]+(?:['']\s*[A-Za-z]+)?)",
        r'Hi\s+from\s+([A-Z][a-z]+(?:['']\s*[A-Za-z]+)?)',
        r'Welcome\s+(?:to\s+)?([A-Z][a-z]+(?:['']\s*[A-Za-z]+)?)',
    ]
    
    for pattern in greeting_patterns:
        match = re.search(pattern, first_800)
        if match:
            name = match.group(1).strip()
            # Skip generic/personal words
            skip_words = ['you', 'your', 'tim', 'john', 'jane', 'welcome', 'hello', 'hi']
            if name.lower() not in skip_words and len(name) >= 3:
                return name
    
    # Pattern: Look for capitalized brand names with optional single letters
    # Examples: "Target members", "Amazon Prime", "Costco customers", "Walmart+ members"
    brand_patterns = [
        # Matches: "Best Buy Rewards members", "Amazon Prime customers" (2-word brand + program + keyword)
        r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:Rewards?|Prime|Plus\+?|Club\+?|Passport)\s+(?:members?|customers?)',
        # Matches: "Target members", "Walmart+ members", "Costco customers" (1-word brand + keyword)
        r'\b([A-Z][a-z]+(?:\+)?)\s+(?:members?|customers?)\b',
        # Matches: "Sephora Beauty Insider", "Ulta Rewards" (brand + program word)
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:Insider|Perks|Benefits)\b',
        # Matches: "Target Customer", "Walmart Support"
        r'\b([A-Z][a-z]+(?:\+)?)\s+(?:Customer|Support|Service)\b',
    ]
    
    for pattern in brand_patterns:
        match = re.search(pattern, first_800)
        if match:
            name = match.group(1).strip()
            # Clean up spacing around dots (J. Crew -> J.Crew)
            name = re.sub(r'([A-Z])\.\s+', r'\1.', name)
            # Validate it's a reasonable store name (1-4 words, 3-40 chars)
            word_count = len(name.split())
            if 1 <= word_count <= 4 and 3 <= len(name) <= 40:
                # Skip generic words that aren't store names
                skip_words = ['the', 'your', 'our', 'welcome', 'thank', 'hello', 'rewards', 
                             'reward', 'buy', 'prime', 'plus', 'club', 'customer', 'xtra', 'gear', 
                             'order', 'shop', 'store', 'offer']
                if name.lower() not in skip_words and not any(name.lower().endswith(sw) for sw in skip_words):
                    return name
    
    # Priority 2: Extract from email addresses in body (e.g., store@mail.store.com)
    email_pattern = r'\b([a-zA-Z0-9._-]+)@(?:mail|email|news|promo)\.([a-zA-Z0-9.-]+)\b'
    email_matches = re.findall(email_pattern, body)
    for prefix, domain in email_matches:
        skip_prefixes = ['noreply', 'no-reply', 'info', 'support', 'hello', 'contact', 'newsletter', 'eteam', 'team', 'emarketing', 'marketing']
        if prefix and prefix.lower() not in skip_prefixes:
            # Clean up the prefix to make it readable
            name = prefix.replace('_', ' ').replace('-', ' ')
            
            # Handle compound names like "jcrewfactory" -> "J.Crew Factory"
            if 'factory' in name.lower():
                name = name.lower().replace('factory', '').strip() + ' Factory'
            elif 'outlet' in name.lower():
                name = name.lower().replace('outlet', '').strip() + ' Outlet'
            
            # Capitalize properly
            name = name.title()
            
            # Special handling for common patterns
            if 'jcrew' in name.lower().replace(' ', ''):
                name = name.replace('Jcrew', 'J.Crew')
            
            # Skip single-word generic names
            if len(name.split()) ==  1 and name.lower() in ['team', 'email', 'mail', 'news', 'shop']:
                continue
            
            if len(name) >= 3:
                return name
    
    # Priority 3: Look for domain names in URLs (e.g., store.com, storeoutlet.com)
    url_pattern = r'https?://(?:www\.)?([a-zA-Z0-9-]+)\.com'
    url_matches = re.findall(url_pattern, body)
    
    # Collect all domains and prioritize certain patterns
    for domain in url_matches:
        if domain.lower() in ['google', 'facebook', 'twitter', 'instagram', 'youtube', 
                              'unsubscribe', 'privacy', 'terms', 'cdn', 'images']:
            continue
        
        # Clean up domain name
        name = domain.replace('-', ' ')
        
        # Handle compound names
        if 'factory' in name.lower():
            name = name.lower().replace('factory', '').strip() + ' Factory'
        elif 'outlet' in name.lower():
            name = name.lower().replace('outlet', '').strip() + ' Outlet'
        
        # Capitalize properly - handle multi-word brands like "bestbuy" -> "Best Buy"
        # Common multi-word patterns
        multi_word_brands = {
            'bestbuy': 'Best Buy',
            'homedepot': 'Home Depot',
            'wholefoods': 'Whole Foods',
            'dollartree': 'Dollar Tree',
            'fiveguys': 'Five Guys',
            'panera bread': 'Panera Bread',
        }
        
        name_lower = name.lower().replace(' ', '')
        if name_lower in multi_word_brands:
            name = multi_word_brands[name_lower]
        else:
            # Default title case
            name = name.title()
        
        # Special handling for common patterns
        if 'jcrew' in name.lower().replace(' ', ''):
            name = name.replace('Jcrew', 'J.Crew')
        
        if len(name) >= 3:
            return name
    
    return None


def extract_store_name_from_footer(body: str, sender: str = "") -> Optional[str]:
    """
    Extract store/company name from email body/footer or sender.
    Tries body patterns first, then footer, then sender as fallback.
    
    Args:
        body: Email body text
        sender: Email sender string
    
    Returns:
        Store name string or None
    """
    # Priority 0: Extract from body text patterns (BEST)
    body_store_name = extract_store_name_from_body(body)
    if body_store_name:
        return body_store_name
    
    # Priority 1: Store name from footer patterns
    footer_data = extract_footer_content(body)
    if footer_data['store_name']:
        return footer_data['store_name']
    
    # Priority 2: Extract from contact email domain
    if footer_data['contact_email']:
        try:
            full_domain = footer_data['contact_email'].split('@')[1]
            domain = full_domain.split('.')[0]
            
            # Clean up and format domain name
            name = domain.replace('_', ' ').replace('-', ' ')
            
            # Handle compound names
            if 'factory' in name.lower():
                name = name.lower().replace('factory', '').strip() + ' Factory'
            elif 'outlet' in name.lower():
                name = name.lower().replace('outlet', '').strip() + ' Outlet'
            
            # Capitalize properly
            name = name.title()
            
            # Special handling for common patterns
            if 'jcrew' in name.lower().replace(' ', ''):
                name = name.replace('Jcrew', 'J.Crew')
            
            if domain and domain.lower() not in ['mail', 'email', 'noreply', 'info', 'newsletter']:
                return name
        except:
            pass
    
    # Priority 3: Extract from website domain
    if footer_data['website']:
        # Convert domain to readable name (e.g., "store.com" -> "Store")
        domain = footer_data['website'].replace('.com', '').replace('.net', '').replace('.org', '')
        
        # Clean up and format
        name = domain.replace('-', ' ').replace('_', ' ')
        
        # Handle compound names
        if 'factory' in name.lower():
            name = name.lower().replace('factory', '').strip() + ' Factory'
        elif 'outlet' in name.lower():
            name = name.lower().replace('outlet', '').strip() + ' Outlet'
        
        # Capitalize properly
        name = name.title()
        
        # Special handling for common patterns
        if 'jcrew' in name.lower().replace(' ', ''):
            name = name.replace('Jcrew', 'J.Crew')
        
        return name
    
    # Priority 4: Extract from sender email (FALLBACK - often personal email)
    if sender and '@' in sender:
        try:
            domain = sender.split('@')[1].split('>')[0].split('.')[0]
            
            # Skip common personal email domains
            if domain.lower() in ['gmail', 'yahoo', 'hotmail', 'outlook', 'mail', 'email', 'noreply', 'aol', 'icloud']:
                return None
            
            # Clean up and format
            name = domain.replace('-', ' ').replace('_', ' ')
            
            # Handle compound names
            if 'factory' in name.lower():
                name = name.lower().replace('factory', '').strip() + ' Factory'
            elif 'outlet' in name.lower():
                name = name.lower().replace('outlet', '').strip() + ' Outlet'
            
            # Capitalize properly
            name = name.title()
            
            # Special handling for common patterns
            if 'jcrew' in name.lower().replace(' ', ''):
                name = name.replace('Jcrew', 'J.Crew')
            
            return name
        except:
            pass
    
    return None


def extract_promo_codes_from_body(body: str) -> List[str]:
    """
    Extract all promo codes from entire email body (not just footer).
    Only extracts codes with both letters AND numbers to avoid false positives.
    
    Args:
        body: Email body text
    
    Returns:
        List of promo code strings
    """
    promo_codes = []
    
    # Patterns for promo codes - must contain both letters and numbers
    patterns = [
        # Must contain both letters and numbers (most common promo format)
        r'(?:use|enter|apply|with)\s+(?:code|promo)[\s:]+([A-Z]+\d+[A-Z0-9]*|[0-9]+[A-Z]+[A-Z0-9]*)\b',
        # Code with specific context words, requiring alphanumeric
        r'(?:discount|promo|coupon)\s+code[\s:]+([A-Z]+\d+[A-Z0-9]*|[0-9]+[A-Z]+[A-Z0-9]*)\b',
        # Standalone format: "CODE: SAVE20" but only if alphanumeric mix
        r'\b(?:code|promo)[\s:]+([A-Z]+\d+[A-Z0-9]{2,}|[0-9]+[A-Z]+[A-Z0-9]{2,})\b',
        # "save X% with code ABC123"
        r'(?:save|get)\s+(?:\d+%?\s+)?(?:with|using)\s+code\s+([A-Z]+\d+[A-Z0-9]*|[0-9]+[A-Z]+[A-Z0-9]*)\b',
    ]
    
    false_positives = ['CODE', 'PROMO', 'THIS', 'THAT', 'YOUR', 'HERE', 
                      'ONLY', 'SAVE', 'CODES', 'BELOW', 'FIELD', 'TEXT',
                      'SHOP', 'LINK', 'EMAIL', 'MAIL', 'FROM', 'NAME', 'CHECKOUT',
                      'ONLINE', 'OFFER', 'GIFT', 'FREE', 'NOW', 'TODAY', 'WHEN',
                      'PHONE', 'NUMBER', 'SCAN', 'ENTER', 'WITH', 'HAVE', 'APPLY']
    
    for pattern in patterns:
        matches = re.findall(pattern, body, re.IGNORECASE)
        for match in matches:
            if match and len(match) >= 4:
                # Check if code has both letters and numbers
                has_letter = any(c.isalpha() for c in match)
                has_digit = any(c.isdigit() for c in match)
                
                # Only accept if it's alphanumeric mix and not in false positives
                if (has_letter and has_digit) and match.upper() not in false_positives:
                    promo_codes.append(match.upper())
    
    # Remove duplicates
    return list(set(promo_codes))


def extract_offers_from_body(body: str) -> Dict:
    """
    Extract all promotional offers from email body with detailed conditions.
    
    Args:
        body: Email body text
    
    Returns:
        Dictionary with offers data including detailed discount descriptions
    """
    offers = {
        'discounts': [],
        'discount_details': [],  # New: Detailed discount descriptions
        'promo_codes': [],
        'free_shipping': False,
        'expiry_date': None
    }
    
    # Extract detailed dollar discounts with conditions and items
    # Pattern: "$15 off your order over $75" or "25% off with orders $125+" or "$10 off Nike shoes"
    detailed_dollar_patterns = [
        # With item/category: "$15 off Nike/Puma items"
        r'\$(\d+(?:\.\d{2})?)\s+off\s+([A-Z][A-Za-z/\s&]+?)(?:\s+(?:items?|products?|gear|shoes|apparel|clothing|collection))?\s*(?:\n|$|\.)',
        # With minimum spend
        r'\$(\d+(?:\.\d{2})?)\s+off\s+(?:your\s+)?(?:order|purchase)s?\s+(?:of|over|when you spend)\s+\$(\d+)',
        r'(?:save|get|enjoy|take)\s+\$(\d+(?:\.\d{2})?)\s+off\s+(?:orders?|purchases?)\s+(?:of|over)\s+\$(\d+)',
        r'\$(\d+(?:\.\d{2})?)\s+off\s+\$(\d+)\+',
        r'(?:save|get)\s+\$(\d+)\s+(?:with|on)\s+\$(\d+)',  # "Get $15 with $75"
    ]
    
    for pattern in detailed_dollar_patterns:
        matches = re.finditer(pattern, body, re.IGNORECASE)
        for match in matches:
            if len(match.groups()) == 2 and not match.group(2).isdigit():
                # Item/category discount: "$15 off Nike"
                amount = match.group(1)
                item = match.group(2).strip()
                # Clean up item name
                item = re.sub(r'\s+', ' ', item)
                detail = f"${amount} OFF {item}"
                if detail not in offers['discount_details']:
                    offers['discount_details'].append(detail)
                    offers['discounts'].append(f"${amount}")
            else:
                # Minimum spend discount
                amount = match.group(1)
                minimum = match.group(2) if len(match.groups()) >= 2 else None
                if minimum:
                    detail = f"${amount} OFF YOUR ORDER OVER ${minimum}"
                    if detail not in offers['discount_details']:
                        offers['discount_details'].append(detail)
                        offers['discounts'].append(f"${amount}")
    
    # Extract percentage discounts with items/categories or minimum spend
    detailed_percent_patterns = [
        # With specific brands/items: "30% off Nike/Puma" or "25% off select Nike shoes"
        r'(\d{1,2})%\s+off\s+(?:select\s+)?([A-Z][A-Za-z/\s&,]{2,30}?)(?:\s+(?:items?|products?|gear|shoes|apparel|clothing|collection|styles?))?\s*(?:\n|$|\.|\||—)',
        # With minimum spend
        r'(\d{1,2})%\s+off\s+(?:orders?|purchases?)\s+(?:of|over)\s+\$(\d+)',
        r'(?:save|get|take|enjoy|receive)\s+(\d{1,2})%\s+off\s+(?:when you spend|on orders over|orders over|purchases over)\s+\$(\d+)',
        r'(\d{1,2})%\s+off.{0,50}orders?\s+\$(\d+)\+',  # "25% off with orders $100+"
        r'(?:get|take|enjoy)\s+up\s+to\s+(\d{1,2})%\s+off.{0,50}minimum.{0,30}\$(\d+)',  # "up to 45% off with minimum $100"
        # "Receive 25% off when you purchase" and look for minimum spend nearby
        r'(?:Receive|Get|Take)\s+(\d{1,2})%\s+off\s+when\s+you\s+purchase.{0,150}(?:with|on)\s+orders?\s+\$(\d+)',
    ]
    
    for pattern in detailed_percent_patterns:
        matches = re.finditer(pattern, body, re.IGNORECASE)
        for match in matches:
            percent = match.group(1)
            second_group = match.group(2) if len(match.groups()) >= 2 else None
            
            if second_group and not second_group.isdigit() and not second_group.startswith('$'):
                # Item/category discount: "30% off Nike/Puma"
                item = second_group.strip()
                # Clean up item name - remove trailing punctuation/words and limit length
                item = re.sub(r'\s+', ' ', item)
                item = re.sub(r'\s+(and|or|with|from)\s*$', '', item, flags=re.IGNORECASE)
                
                # Skip if item is too generic or too long
                generic_words = ['any', 'all', 'our', 'the', 'your', 'when', 'you', 'purchase']
                if any(word in item.lower() for word in generic_words) or len(item) > 30:
                    # Skip this match and continue to next
                    continue
                
                detail = f"{percent}% OFF {item}"
                if detail not in offers['discount_details']:
                    offers['discount_details'].append(detail)
                    offers['discounts'].append(f"{percent}%")
            elif second_group and second_group.isdigit():
                # Minimum spend discount
                minimum = second_group
                detail = f"{percent}% OFF orders over ${minimum}"
                if detail not in offers['discount_details']:
                    offers['discount_details'].append(detail)
                    offers['discounts'].append(f"{percent}%")
    
    # New: Look for "with orders $125+" or "minimum $125" pattern separately
    min_spend_pattern = r'(?:with|on|minimum(?:\s+purchase)?|orders?(?:\s+of)?)\s+\$(\d+)\+'
    min_spend_match = re.search(min_spend_pattern, body, re.IGNORECASE)
    
    # If we found a minimum spend but no detailed discount yet, try to find the percentage
    if min_spend_match and not offers['discount_details']:
        minimum = min_spend_match.group(1)
        # Look backwards for the percentage in the 300 chars before
        before_text = body[:min_spend_match.start()]
        percent_match = re.search(r'(?:up\s+to\s+)?(\d{1,2})%\s+off', before_text[-300:], re.IGNORECASE)
        if percent_match:
            percent = percent_match.group(1)
            detail = f"{percent}% OFF orders ${minimum}+"
            offers['discount_details'].append(detail)
            offers['discounts'].append(f"{percent}%")
    
    # Extract simple discount percentages (if no detailed version found)
    if not offers['discounts']:
        discount_patterns = [
            r'(?:up\s+to\s+)?(\d{1,2})%\s*(?:off|discount|savings)',
            r'(?:save|get|enjoy|take)\s+(?:up\s+to\s+)?(\d{1,2})%',
        ]
        
        for pattern in discount_patterns:
            matches = re.findall(pattern, body, re.IGNORECASE)
            for match in matches:
                percent = match
                # Try to find context around this discount for better details (within 150 chars)
                context_pattern = rf'[^\n]{{0,75}}(\d{{1,2}})%\s+off[^\n]{{0,75}}'
                context_match = re.search(context_pattern.replace(r'(\d{1,2})', percent), body, re.IGNORECASE)
                
                if context_match:
                    context_text = context_match.group(0).strip()
                    
                    # Check for brand/item mentions (Nike, Puma, Adidas, etc.)
                    brand_pattern = r'(\b(?:Nike|Puma|Adidas|Reebok|Under Armour|New Balance|Converse|Vans|Jordan|Skechers)[/\s&,]+(?:Nike|Puma|Adidas|Reebok|Under Armour|New Balance|Converse|Vans|Jordan|Skechers)?)'
                    brand_match = re.search(brand_pattern, context_text, re.IGNORECASE)
                    if brand_match:
                        brands = brand_match.group(1).strip()
                        detail = f"{percent}% OFF {brands}"
                        if detail not in offers['discount_details']:
                            offers['discount_details'].append(detail)
                    # Check for category mentions
                    elif re.search(r'\b(?:shoes|sneakers|footwear|apparel|clothing|gear|sportswear|activewear)\b', context_text, re.IGNORECASE):
                        category_match = re.search(r'\b(shoes|sneakers|footwear|apparel|clothing|gear|sportswear|activewear)\b', context_text, re.IGNORECASE)
                        category = category_match.group(1)
                        detail = f"{percent}% OFF {category}"
                        if detail not in offers['discount_details']:
                            offers['discount_details'].append(detail)
                    # Clean up and add as detail with meaningful context
                    elif 'new' in context_text.lower() and 'deal' in context_text.lower():
                        detail = f"{percent}% OFF (on new deals)"
                    elif 'new' in context_text.lower():
                        detail = f"{percent}% OFF (on new items)"
                    elif 'select' in context_text.lower() or 'selected' in context_text.lower():
                        detail = f"{percent}% OFF (on select items)"
                    elif 'everything' in context_text.lower() or 'sitewide' in context_text.lower() or 'storewide' in context_text.lower():
                        detail = f"{percent}% OFF (sitewide)"
                    elif 'clearance' in context_text.lower():
                        detail = f"{percent}% OFF (clearance items)"
                    else:
                        # No specific context, don't add to details
                        detail = None
                    
                    if detail and detail not in offers['discount_details']:
                        offers['discount_details'].append(detail)
                
                offers['discounts'].append(f"{percent}%")
    
    # Extract simple dollar discounts (if no detailed version found)
    if not offers['discounts']:
        dollar_patterns = [
            r'\$(\d+)\s*(?:off|discount)',
            r'(?:save|get|enjoy|take)\s+\$(\d+)',
        ]
        
        for pattern in dollar_patterns:
            matches = re.findall(pattern, body, re.IGNORECASE)
            for match in matches:
                offers['discounts'].append(f"${match}")
    
    # Check for free shipping
    if re.search(r'\bfree\s+shipping\b', body, re.IGNORECASE):
        offers['free_shipping'] = True
    
    # Extract promo codes
    offers['promo_codes'] = extract_promo_codes_from_body(body)
    
    # Extract expiry dates - GENERALIZED comprehensive patterns
    date_patterns = [
        # Pattern 1: "Offer ends at 11:59 p.m. PT on December 3, 2025"
        r'(?:Offer|Sale|Deal|Promotion|Discount)\s+(?:ends?|expires?|valid)\s+(?:at\s+)?(?:[\d:]+\s*[ap]\.?m\.?\s*)?(?:PT|ET|CT|MT)?\s*(?:on\s+)?([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',
        
        # Pattern 2: "expires December 3, 2025" or "valid December 3, 2025"
        r'(?:expires?|valid|ends?|through|thru|until|till)[\s:]+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',
        
        # Pattern 3: "by December 3, 2025" or "before December 3, 2025"
        r'(?:by|before)[\s:]+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',
        
        # Pattern 4: "12/03/2025" or "12/3/25"
        r'(?:expires?|valid|ends?|through|thru|until|till)[\s:]+(\d{1,2}/\d{1,2}/\d{2,4})',
        
        # Pattern 5: "from Nov 28 through December 2, 2025"
        r'through\s+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',
        
        # Pattern 6: "valid until December 3" or "ends December 3" (with optional year)
        r'(?:valid|ends?|expires?)\s+(?:until|on|through)?\s*([A-Z][a-z]+\s+\d{1,2}(?:,?\s+\d{4})?)',
        
        # Pattern 7: Just a date after keywords (very general fallback)
        r'(?:Offer|promotion|sale|discount).*?([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            offers['expiry_date'] = match.group(1)
            break
    
    # Remove duplicates from discounts
    offers['discounts'] = list(set(offers['discounts']))
    
    return offers


def get_enhanced_email_data(body: str, sender: str = "", subject: str = "") -> Dict:
    """
    Extract all available data from email body, subject, and footer.
    
    Args:
        body: Email body text
        sender: Email sender string
        subject: Email subject line
    
    Returns:
        Dictionary with all extracted data
    """
    footer_data = extract_footer_content(body)
    
    # Extract offers from body AND subject (subject often has the main offer)
    body_offers = extract_offers_from_body(body)
    
    # Also check subject for discount offers to supplement body extraction
    if subject:
        subject_offers = extract_offers_from_body(subject)
        # Merge subject offers into body offers (subject takes priority for details)
        if subject_offers['discount_details'] and not body_offers['discount_details']:
            body_offers['discount_details'] = subject_offers['discount_details']
        if subject_offers['discounts'] and not body_offers['discounts']:
            body_offers['discounts'] = subject_offers['discounts']
    
    return {
        'footer': footer_data,
        'offers': body_offers,
        'store_name': extract_store_name_from_footer(body)
    }
