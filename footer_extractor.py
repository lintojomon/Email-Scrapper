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
            email_part = footer_data['contact_email'].split('@')[1]
            domain_parts = email_part.split('.')
            
            # Skip email marketing subdomains like 'eml', 'mail', 'mkt', 'email'
            marketing_subdomains = ['eml', 'mail', 'email', 'mkt', 'marketing', 'e', 'em', 'news', 'promo']
            
            # If first part is marketing subdomain and there are more parts, use next part
            if len(domain_parts) >= 3 and domain_parts[0].lower() in marketing_subdomains:
                domain = domain_parts[1]  # Use second part (actual brand)
            else:
                domain = domain_parts[0]  # Use first part
            
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
            if 'nordstromrack' in name.lower().replace(' ', ''):
                name = 'Nordstrom Rack'
            elif 'nordstrom' in name.lower():
                name = 'Nordstrom'
            
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


def extract_validity_terms(body: str) -> List[str]:
    """
    Extract validity/terms information from promotional offers.
    Captures date ranges, minimum purchase, store restrictions, and usage instructions.
    Looks for both "Valid" keyword and common symbols (‡, *, †, §, etc.) used for footnotes.
    
    Args:
        body: Email body text
    
    Returns:
        List of validity term strings describing how to avail discounts
    """
    terms = []
    
    # Strategy 1: Find all "Valid..." statements and extract until next sentence or paragraph
    segments = re.split(r'(Valid|valid)\s+', body)
    
    # Process segments in pairs (keyword + content)
    for i in range(1, len(segments), 2):
        if i + 1 < len(segments):
            keyword = segments[i]
            content = segments[i + 1]
            
            # Extract until we hit a clear sentence break
            match = re.match(r'([^\.]+(?:\.[^\.]{0,200}(?:checkout|barcode|number|supplies last|minimum|Department)[^\.\n]*)?\.?)', content, re.IGNORECASE)
            
            if match:
                term = match.group(1).strip()
                # Clean up
                term = re.sub(r'\s+', ' ', term)
                term = term.rstrip('.')
                term = re.split(r'\.\s*(?:Shop|Learn more|Click|View)', term, maxsplit=1)[0].strip()
                term = term.rstrip('.')
                term = re.sub(r'\s*Also available:\s*$', '', term, flags=re.IGNORECASE)
                
                # Only add if it has meaningful content
                if any(indicator in term.lower() for indicator in ['/', 'minimum', '$', 'purchase', 'store', 'online', 'department', 'while supplies', 'scan', 'barcode', 'phone', 'offer', 'discount', 'code']):
                    if term not in terms and len(term) >= 15:
                        terms.append(term)
    
    # Strategy 2: Extract terms marked with common symbols (‡, *, †, §, ¶, etc.)
    # These symbols are used in footers to denote terms and conditions
    symbol_patterns = [
        # Double/triple symbols first (more specific)
        r'(\*\*\*)\s*([^\n]{15,300}(?:offer|discount|valid|minimum|purchase|exclusion|code|promo|expires?|through|online|store|while supplies)[^\n]{0,200})',
        r'(\*\*)\s*([^\n]{15,300}(?:offer|discount|valid|minimum|purchase|exclusion|code|promo|expires?|through|online|store|while supplies)[^\n]{0,200})',
        r'(‡‡)\s*([^\n]{15,300}(?:offer|discount|valid|minimum|purchase|exclusion|code|promo|expires?|through|online|store|while supplies)[^\n]{0,200})',
        r'(††)\s*([^\n]{15,300}(?:offer|discount|valid|minimum|purchase|exclusion|code|promo|expires?|through|online|store|while supplies)[^\n]{0,200})',
        r'(§§)\s*([^\n]{15,300}(?:offer|discount|valid|minimum|purchase|exclusion|code|promo|expires?|through|online|store|while supplies)[^\n]{0,200})',
        
        # Single symbols
        r'(\*)\s*([^\n]{15,300}(?:offer|discount|valid|minimum|purchase|exclusion|code|promo|expires?|through|online|store|while supplies)[^\n]{0,200})',
        r'(‡)\s*([^\n]{15,300}(?:offer|discount|valid|minimum|purchase|exclusion|code|promo|expires?|through|online|store|while supplies)[^\n]{0,200})',
        r'(†)\s*([^\n]{15,300}(?:offer|discount|valid|minimum|purchase|exclusion|code|promo|expires?|through|online|store|while supplies)[^\n]{0,200})',
        r'(§)\s*([^\n]{15,300}(?:offer|discount|valid|minimum|purchase|exclusion|code|promo|expires?|through|online|store|while supplies)[^\n]{0,200})',
        r'(¶)\s*([^\n]{15,300}(?:offer|discount|valid|minimum|purchase|exclusion|code|promo|expires?|through|online|store|while supplies)[^\n]{0,200})',
        
        # Superscript numbers (often used as footnote markers)
        r'([¹²³⁴⁵⁶⁷⁸⁹])\s*([^\n]{15,300}(?:offer|discount|valid|minimum|purchase|exclusion|code|promo|expires?|through|online|store|while supplies)[^\n]{0,200})',
        
        # Dollar sign followed by terms (but not prices)
        r'(\$)\s*(?![\d])(See\s+[^\n]{10,300}(?:offer|discount|valid|minimum|purchase|exclusion|code|promo|expires?|through|online|store)[^\n]{0,200})',
    ]
    
    for pattern in symbol_patterns:
        matches = re.finditer(pattern, body, re.IGNORECASE)
        for match in matches:
            symbol = match.group(1)
            term_text = match.group(2).strip()
            
            # Clean up the term
            term_text = re.sub(r'\s+', ' ', term_text)
            # Remove trailing periods/commas
            term_text = term_text.rstrip('.,;:')
            # Remove "Also available" or "Shop now" at the end
            term_text = re.split(r'\.\s*(?:Shop|Also available|Learn more|Click here|View)', term_text, maxsplit=1)[0].strip()
            
            # Add symbol prefix to make it clear which symbol this is for
            if len(term_text) >= 15 and term_text not in [t.replace(f'{symbol} ', '') for t in terms]:
                # Add symbol marker
                formatted_term = f"{symbol} {term_text}"
                if formatted_term not in terms:
                    terms.append(formatted_term)
    
    # Strategy 3: Look for promo code context to associate with discounts
    code_context_patterns = [
        r'(?:Use|Enter|Apply)\s+code\s+([A-Z0-9]+)\s+(?:for|to get)\s+([^\.]{10,100})',
        r'([^\.]{10,100})\s+with\s+code\s+([A-Z0-9]+)',
    ]
    
    for pattern in code_context_patterns:
        matches = re.finditer(pattern, body, re.IGNORECASE)
        for match in matches:
            if len(match.groups()) >= 2:
                if 'code' in match.group(0).lower()[:20]:
                    code = match.group(1)
                    description = match.group(2).strip()
                else:
                    description = match.group(1).strip()
                    code = match.group(2)
                
                description = re.sub(r'\s+', ' ', description)
                description = description.strip('.,;:')
                
                if len(description) > 10 and len(code) >= 3:
                    term_text = f"Use code {code} - {description}"
                    if term_text not in terms:
                        terms.append(term_text)
    
    # Strategy 4: Standalone minimum purchase requirements (if not already captured)
    if not any('minimum purchase' in t.lower() for t in terms):
        min_purchase_pattern = r'\$\d+(?:\.\d{2})?\s+minimum\s+purchase'
        min_purchase_matches = re.findall(min_purchase_pattern, body, re.IGNORECASE)
        for match in min_purchase_matches:
            if match not in terms:
                terms.append(match)
    
    return terms


def extract_points_rewards(body: str) -> List[str]:
    """
    Extract points/rewards information from email body.
    Example: "You're 1,000 points from the next $2"
    
    Args:
        body: Email body text
    
    Returns:
        List of points/rewards strings
    """
    rewards = []
    
    # Pattern 1: "You're X points from the next $Y"
    points_patterns = [
        r"You[''']re\s+([\d,]+\s+points\s+from\s+(?:the\s+)?next\s+\$\d+)",
        r'You have\s+([\d,]+\s+points)',
        r'([\d,]+\s+points\s+available)',
        r'Earn\s+([\d,]+\s+(?:bonus\s+)?points)',
    ]
    
    for pattern in points_patterns:
        matches = re.finditer(pattern, body, re.IGNORECASE)
        for match in matches:
            # Get just the matched group
            context = match.group(1).strip()
            # Clean up
            context = re.sub(r'\s+', ' ', context)
            if context not in rewards and len(context) >= 10:
                # For "X points from the next $Y", prepend "You're"
                if 'from the next' in context.lower():
                    context = "You're " + context
                rewards.append(context)
    
    return rewards


def extract_membership_benefits(body: str) -> List[str]:
    """
    Extract membership benefits with full conditions and details from email body.
    Example: "Delivery from Club: Plus members get free Delivery from Club on eligible items 
    totaling $50 or more pre-tax. Otherwise, there is an $8 fee per order."
    
    Args:
        body: Email body text
    
    Returns:
        List of membership benefit strings with conditions
    """
    benefits = []
    
    # Strategy 1: Extract benefit details with colon-separated format
    # Pattern: "Benefit Name: description with conditions..."
    # Example: "Delivery from Club: Plus members get free Delivery..."
    colon_pattern = r'\b([A-Z][A-Za-z\s]{5,40}):\s+([^.]{20,300}(?:\.[^.]{0,200})?)'
    
    benefit_keywords = ['delivery', 'pickup', 'shipping', 'savings', 'rewards', 'cash back',
                       'discount', 'access', 'free', 'member', 'exclusive', 'gas', 'fuel',
                       'services', 'warranty', 'roadside', 'travel', 'streaming', 'unlimited',
                       'tire', 'optical', 'pharmacy', 'curbside', 'express', 'instant']
    
    colon_matches = re.finditer(colon_pattern, body, re.IGNORECASE | re.DOTALL)
    
    for match in colon_matches:
        benefit_name = match.group(1).strip()
        benefit_desc = match.group(2).strip()
        
        # Check if benefit name contains relevant keywords
        if any(keyword in benefit_name.lower() for keyword in benefit_keywords):
            # Clean up the description
            benefit_desc = re.sub(r'\s+', ' ', benefit_desc)
            # Take up to first 2-3 sentences (up to 300 chars)
            sentences = benefit_desc.split('.')
            if len(sentences) > 3:
                benefit_desc = '. '.join(sentences[:3]) + '.'
            else:
                benefit_desc = benefit_desc if benefit_desc.endswith('.') else benefit_desc + '.'
            
            full_benefit = f"{benefit_name}: {benefit_desc}"
            
            # Avoid duplicates and overly long descriptions
            if len(full_benefit) <= 400 and full_benefit not in benefits:
                benefits.append(full_benefit)
    
    # Strategy 2: Extract from bullet point lists with full descriptions
    # Pattern: "• Free Shipping on orders over $35 for members"
    bullet_pattern = r'[•\-]\s*([A-Z][^\n•\-]{15,250})'
    bullet_matches = re.finditer(bullet_pattern, body)
    
    for match in bullet_matches:
        benefit = match.group(1).strip()
        # Clean up
        benefit = re.sub(r'\s+', ' ', benefit)
        # Remove trailing punctuation
        benefit = benefit.rstrip('.,;:')
        
        # Check if contains benefit keywords
        if any(keyword in benefit.lower() for keyword in benefit_keywords):
            # Ensure it has substance (not just a title)
            if len(benefit) >= 15 and benefit not in benefits:
                # Check not already captured as part of colon format
                is_duplicate = False
                for existing in benefits:
                    if benefit.lower() in existing.lower():
                        is_duplicate = True
                        break
                if not is_duplicate:
                    benefits.append(benefit)
    
    # Strategy 3: Extract from footer lists with lookup for details
    # First, find benefit names from footer (like "Delivery from Club | Curbside Pickup")
    footer_section = body[-2500:] if len(body) > 2500 else body
    pipe_pattern = r'([A-Z][A-Za-z\s]{5,35})\s*[|•]'
    pipe_matches = re.finditer(pipe_pattern, footer_section)
    
    benefit_names_found = []
    for match in pipe_matches:
        item = match.group(1).strip()
        if any(keyword in item.lower() for keyword in benefit_keywords):
            benefit_names_found.append(item)
    
    # Now search the body for detailed descriptions of these benefits
    for benefit_name in benefit_names_found:
        # Skip if already found with details via colon pattern
        if any(benefit_name.lower() in b.lower() and ':' in b for b in benefits):
            continue
        
        # Look for this benefit name followed by description in the body
        # Pattern: "benefit_name ... description with conditions"
        escaped_name = re.escape(benefit_name)
        detail_pattern = rf'\b{escaped_name}[:\s]{{0,5}}([^.\n]{{30,300}}(?:\.[^.\n]{{0,150}})?)'
        
        detail_match = re.search(detail_pattern, body, re.IGNORECASE | re.DOTALL)
        if detail_match:
            description = detail_match.group(1).strip()
            description = re.sub(r'\s+', ' ', description)
            
            # Take first 1-2 sentences
            sentences = description.split('.')
            if len(sentences) > 2:
                description = '. '.join(sentences[:2]) + '.'
            else:
                description = description if description.endswith('.') else description + '.'
            
            full_benefit = f"{benefit_name}: {description}"
            
            if len(full_benefit) <= 400:
                # Check for duplicates
                is_duplicate = False
                for existing in benefits:
                    if benefit_name.lower() in existing.lower():
                        is_duplicate = True
                        break
                if not is_duplicate:
                    benefits.append(full_benefit)
        else:
            # No detailed description found, just add the benefit name
            if benefit_name not in benefits and len(benefit_name) >= 8:
                # Check not already in another benefit
                is_duplicate = False
                for existing in benefits:
                    if benefit_name.lower() in existing.lower():
                        is_duplicate = True
                        break
                if not is_duplicate:
                    benefits.append(benefit_name)
    
    # Strategy 4: Extract common benefit patterns with context
    # Look for patterns like "Plus members get free delivery..." or "Members save 10% on..."
    context_patterns = [
        # "Plus members get free X on Y conditions"
        r'((?:Plus|Premium|Gold|Member[s]?)\s+(?:members?|get)\s+(?:free|exclusive|unlimited)\s+[^.]{20,200})',
        # "Free X for members on Y"
        r'(Free\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\s+(?:for\s+)?(?:members?|Plus)\s+[^.]{10,150})',
        # "Members save/get X% on Y"
        r'(Members?\s+(?:save|get|receive)\s+\d+%[^.]{10,150})',
        # "Earn X points/rewards on Y"
        r'(Earn\s+(?:\d+%?|bonus)\s+(?:points|rewards|cash\s+back)[^.]{10,150})',
    ]
    
    for pattern in context_patterns:
        matches = re.finditer(pattern, body, re.IGNORECASE)
        for match in matches:
            benefit = match.group(1).strip()
            benefit = re.sub(r'\s+', ' ', benefit)
            
            # Ensure ends with period
            if not benefit.endswith('.'):
                # Try to extend to end of sentence
                start_pos = match.start(1)
                end_pos = match.end(1)
                # Look ahead for sentence end
                remaining = body[end_pos:end_pos+150]
                sentence_end = re.search(r'^[^.]*\.', remaining)
                if sentence_end:
                    benefit = benefit + sentence_end.group(0)
                else:
                    benefit = benefit + '.'
            
            if len(benefit) >= 20 and len(benefit) <= 400:
                # Check for duplicates
                is_duplicate = False
                for existing in benefits:
                    if benefit.lower() in existing.lower() or existing.lower() in benefit.lower():
                        is_duplicate = True
                        break
                if not is_duplicate:
                    benefits.append(benefit)
    
    # Strategy 5: Extract benefits marked with symbols (‡, *, †, §, ¶, etc.)
    # Similar to extract_validity_terms but for membership benefits
    symbol_patterns = [
        # More specific patterns first (double/triple symbols)
        (r'\*{3}\s*([^‡*†§¶]{20,350})', '*** '),
        (r'\*{2}\s*([^‡*†§¶]{20,350})', '** '),
        (r'‡{2}\s*([^‡*†§¶]{20,350})', '‡‡ '),
        (r'†{2}\s*([^‡*†§¶]{20,350})', '†† '),
        (r'§{2}\s*([^‡*†§¶]{20,350})', '§§ '),
        
        # Single symbols
        (r'(?<![‡*†§¶])\*\s*([^‡*†§¶]{20,350})', '* '),
        (r'(?<![‡*†§¶])‡\s*([^‡*†§¶]{20,350})', '‡ '),
        (r'(?<![‡*†§¶])†\s*([^‡*†§¶]{20,350})', '† '),
        (r'(?<![‡*†§¶])§\s*([^‡*†§¶]{20,350})', '§ '),
        (r'(?<![‡*†§¶])¶\s*([^‡*†§¶]{20,350})', '¶ '),
        
        # Superscript numbers
        (r'[¹²³⁴⁵⁶⁷⁸⁹]+\s*([^‡*†§¶¹²³⁴⁵⁶⁷⁸⁹]{20,350})', ''),
    ]
    
    # Keywords that indicate this is a membership benefit, not just any footnote
    membership_keywords = ['member', 'membership', 'benefit', 'perk', 'free', 'discount',
                          'shipping', 'delivery', 'access', 'exclusive', 'save', 'reward',
                          'points', 'cashback', 'upgrade', 'priority', 'complimentary',
                          'unlimited', 'premium', 'plus', 'service', 'assistance']
    
    for pattern, prefix in symbol_patterns:
        matches = re.finditer(pattern, body, re.IGNORECASE | re.DOTALL)
        for match in matches:
            term = match.group(1).strip()
            # Only extract if it contains membership-related keywords
            if any(keyword in term.lower() for keyword in membership_keywords):
                # Clean up the term
                term = re.sub(r'\s+', ' ', term)  # Normalize whitespace
                # Take first 2-3 sentences or up to 350 chars
                sentences = term.split('.')
                if len(sentences) > 3:
                    term = '. '.join(sentences[:3]) + '.'
                else:
                    # Find natural end point
                    if len(term) > 350:
                        term = term[:350].rsplit(' ', 1)[0] + '...'
                    elif not term.endswith('.'):
                        term = term.rstrip('.,;:') + '.'
                
                full_term = f"{prefix}{term}" if prefix else term
                
                # Check for duplicates
                is_duplicate = False
                for existing in benefits:
                    # Check if significant overlap
                    if (term.lower()[:30] in existing.lower() or 
                        existing.lower()[:30] in term.lower()):
                        is_duplicate = True
                        break
                
                if not is_duplicate and len(full_term) >= 25:
                    benefits.append(full_term)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_benefits = []
    for benefit in benefits:
        benefit_lower = benefit.lower()
        # Use first 50 chars as duplicate check (to allow slight variations)
        key = benefit_lower[:50] if len(benefit_lower) > 50 else benefit_lower
        if key not in seen:
            seen.add(key)
            unique_benefits.append(benefit)
    
    return unique_benefits[:15]  # Limit to 15 benefits max


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
        'expiry_date': None,
        'validity_terms': [],  # New: Validity/terms information
        'points_rewards': []   # New: Points/rewards information
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
    
    # Extract validity terms and conditions
    offers['validity_terms'] = extract_validity_terms(body)
    
    # Extract points/rewards information
    offers['points_rewards'] = extract_points_rewards(body)
    
    # Extract expiry dates - GENERALIZED comprehensive patterns
    date_patterns = [
        # Pattern 0: Date ranges like "1/19/26-2/2/26" or "2/2 - 2/8/26" (HIGHEST PRIORITY)
        r'(?:Valid|valid|Expires?|expires?)\s+(?:online\s+only\s+)?(?:in-store\s+(?:and|&)\s+online\s+)?(?:from\s+)?(\d{1,2}/\d{1,2}/\d{2,4})\s*[-–—]\s*(\d{1,2}/\d{1,2}/\d{2,4})',
        
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
            # For date ranges, take the end date (group 2)
            if len(match.groups()) >= 2 and match.group(2):
                offers['expiry_date'] = match.group(2)
            else:
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
    
    # Extract membership benefits (for membership emails)
    membership_benefits = extract_membership_benefits(body)
    
    return {
        'footer': footer_data,
        'offers': body_offers,
        'store_name': extract_store_name_from_footer(body),
        'membership_benefits': membership_benefits
    }
