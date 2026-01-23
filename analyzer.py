# analyzer.py - Main Email Analysis Script
# =========================================
# Main entry point for the email scraper POC

"""
Main analyzer script - orchestrates the email analysis workflow

This script:
1. Authenticates with Gmail using OAuth
2. Fetches emails from inbox
3. Analyzes email content using regex patterns
4. Categorizes emails into Membership, Offer, or Normal
5. Displays categorized results
6. Optionally exports to CSV
"""

import argparse
import re
from typing import List, Dict
from auth import get_gmail_service, revoke_token
from gmail_reader import fetch_emails, fetch_emails_by_days
from patterns import analyze_text, categorize_email, is_shopping_domain, is_excluded_domain


def extract_credit_card_name(subject: str, body: str = "") -> str:
    """
    Extract credit card name from email subject or body.
    
    Args:
        subject: Email subject
        body: Email body for additional context
    
    Returns:
        Credit card name string
    """
    text = f"{subject} {body}"
    
    # Known credit card patterns - specific card names
    card_patterns = [
        # American Express cards
        r'(American Express[\s®]*(?:Blue Cash Everyday|Blue Cash Preferred|Gold|Platinum|Green|Delta SkyMiles|Hilton Honors|Marriott Bonvoy)?[\s®]*Card)',
        r'(Amex[\s®]*(?:Blue Cash Everyday|Blue Cash Preferred|Gold|Platinum|Green)?[\s®]*Card)',
        
        # Delta SkyMiles cards
        r'(Delta SkyMiles[\s®]*(?:Gold|Platinum|Reserve|Blue)?[\s®]*(?:Business)?[\s®]*(?:American Express)?[\s®]*Card)',
        
        # Chase cards
        r'(Chase[\s®]*(?:Sapphire Preferred|Sapphire Reserve|Freedom|Freedom Unlimited|Freedom Flex|Ink Business)?[\s®]*Card)',
        
        # Capital One cards
        r'(Capital One[\s®]*(?:Venture|Venture X|Quicksilver|SavorOne|Spark)?[\s®]*Card)',
        
        # Citi cards
        r'(Citi[\s®]*(?:Double Cash|Premier|Custom Cash|Diamond Preferred)?[\s®]*Card)',
        
        # Discover cards
        r'(Discover[\s®]*(?:it|it Miles|it Chrome)?[\s®]*Card)',
        
        # Bank of America cards
        r'(Bank of America[\s®]*(?:Cash Rewards|Travel Rewards|Premium Rewards|Customized Cash)?[\s®]*Card)',
        
        # Wells Fargo cards
        r'(Wells Fargo[\s®]*(?:Active Cash|Reflect|Autograph)?[\s®]*Card)',
        
        # Generic card patterns
        r'((?:Visa|Mastercard|Discover)[\s®]*(?:Signature|Platinum|Gold|Rewards)?[\s®]*Card)',
        
        # Pattern for "Your <Card Name> Card Benefits"
        r'Your\s+([A-Za-z\s®]+(?:Card))\s+Benefits',
        
        # Pattern for "<Card Name> Card" at the beginning
        r'^.*?([A-Z][A-Za-z\s®]+(?:Card))',
    ]
    
    for pattern in card_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            card_name = match.group(1).strip()
            # Clean up the card name
            card_name = re.sub(r'\s+', ' ', card_name)  # Remove extra spaces
            card_name = card_name.replace('®', '').strip()  # Remove ® symbol
            if len(card_name) > 5 and 'card' in card_name.lower():
                return card_name
    
    # Try to extract from subject directly
    # Pattern: "Your <Something> Card Benefits Are Now Active"
    subject_match = re.search(r'Your\s+(.+?)\s+(?:Benefits|Is|Has|Are)', subject, re.IGNORECASE)
    if subject_match:
        potential_card = subject_match.group(1).strip()
        potential_card = potential_card.replace('®', '').strip()
        if 'card' in potential_card.lower():
            return potential_card
    
    # Known card issuer detection from text (comprehensive US list)
    issuers = {
        # === MAJOR CARD NETWORKS ===
        'american express': 'American Express Card',
        'amex': 'American Express Card',
        'visa signature': 'Visa Signature Card',
        'visa infinite': 'Visa Infinite Card',
        'mastercard world': 'Mastercard World Card',
        'mastercard world elite': 'Mastercard World Elite Card',
        'discover it': 'Discover it Card',
        
        # === CHASE CARDS ===
        'chase sapphire reserve': 'Chase Sapphire Reserve',
        'chase sapphire preferred': 'Chase Sapphire Preferred',
        'chase sapphire': 'Chase Sapphire Card',
        'chase freedom unlimited': 'Chase Freedom Unlimited',
        'chase freedom flex': 'Chase Freedom Flex',
        'chase freedom': 'Chase Freedom Card',
        'chase slate': 'Chase Slate Card',
        'chase ink business': 'Chase Ink Business Card',
        'chase ink': 'Chase Ink Card',
        'amazon prime rewards visa': 'Amazon Prime Rewards Visa',
        'amazon rewards visa': 'Amazon Rewards Visa',
        'united club infinite': 'United Club Infinite Card',
        'united explorer': 'United Explorer Card',
        'southwest rapid rewards': 'Southwest Rapid Rewards Card',
        'southwest priority': 'Southwest Priority Card',
        'marriott bonvoy boundless': 'Marriott Bonvoy Boundless',
        'marriott bonvoy bold': 'Marriott Bonvoy Bold',
        'ihg rewards': 'IHG Rewards Card',
        'world of hyatt': 'World of Hyatt Card',
        'aeroplan': 'Aeroplan Card',
        'disney visa': 'Disney Visa Card',
        'starbucks rewards visa': 'Starbucks Rewards Visa',
        
        # === AMERICAN EXPRESS CARDS ===
        'platinum card': 'American Express Platinum Card',
        'amex platinum': 'American Express Platinum Card',
        'amex gold': 'American Express Gold Card',
        'gold card': 'American Express Gold Card',
        'amex green': 'American Express Green Card',
        'blue cash preferred': 'Blue Cash Preferred Card',
        'blue cash everyday': 'Blue Cash Everyday Card',
        'amex everyday': 'Amex EveryDay Card',
        'hilton honors amex': 'Hilton Honors American Express',
        'hilton honors aspire': 'Hilton Honors Aspire Card',
        'hilton honors surpass': 'Hilton Honors Surpass Card',
        'marriott bonvoy amex': 'Marriott Bonvoy American Express',
        'delta skymiles gold': 'Delta SkyMiles Gold Card',
        'delta skymiles platinum': 'Delta SkyMiles Platinum Card',
        'delta skymiles reserve': 'Delta SkyMiles Reserve Card',
        'delta skymiles blue': 'Delta SkyMiles Blue Card',
        'delta skymiles': 'Delta SkyMiles Card',
        'amex business gold': 'Amex Business Gold Card',
        'amex business platinum': 'Amex Business Platinum Card',
        
        # === CAPITAL ONE CARDS ===
        'capital one venture x': 'Capital One Venture X',
        'capital one venture': 'Capital One Venture Card',
        'capital one ventureone': 'Capital One VentureOne',
        'capital one quicksilver': 'Capital One Quicksilver',
        'capital one savor': 'Capital One Savor',
        'capital one savorone': 'Capital One SavorOne',
        'capital one spark': 'Capital One Spark Business',
        'capital one platinum': 'Capital One Platinum Card',
        'capital one': 'Capital One Card',
        
        # === CITI CARDS ===
        'citi double cash': 'Citi Double Cash Card',
        'citi premier': 'Citi Premier Card',
        'citi custom cash': 'Citi Custom Cash Card',
        'citi diamond preferred': 'Citi Diamond Preferred',
        'citi rewards+': 'Citi Rewards+ Card',
        'citi simplicity': 'Citi Simplicity Card',
        'costco anywhere visa': 'Costco Anywhere Visa',
        'at&t access card': 'AT&T Access Card',
        'aadvantage platinum': 'AAdvantage Platinum Card',
        'aadvantage executive': 'AAdvantage Executive Card',
        'citi': 'Citi Card',
        
        # === BANK OF AMERICA CARDS ===
        'bank of america premium rewards': 'Bank of America Premium Rewards',
        'bank of america cash rewards': 'Bank of America Cash Rewards',
        'bank of america travel rewards': 'Bank of America Travel Rewards',
        'bank of america customized cash': 'Bank of America Customized Cash',
        'alaska airlines visa': 'Alaska Airlines Visa',
        'bank of america': 'Bank of America Card',
        
        # === WELLS FARGO CARDS ===
        'wells fargo active cash': 'Wells Fargo Active Cash',
        'wells fargo autograph': 'Wells Fargo Autograph',
        'wells fargo reflect': 'Wells Fargo Reflect',
        'wells fargo platinum': 'Wells Fargo Platinum Card',
        'bilt rewards': 'Bilt Rewards Card',
        'wells fargo': 'Wells Fargo Card',
        
        # === US BANK CARDS ===
        'us bank altitude reserve': 'U.S. Bank Altitude Reserve',
        'us bank altitude connect': 'U.S. Bank Altitude Connect',
        'us bank altitude go': 'U.S. Bank Altitude Go',
        'us bank cash+': 'U.S. Bank Cash+ Card',
        'us bank': 'U.S. Bank Card',
        
        # === DISCOVER CARDS ===
        'discover it chrome': 'Discover it Chrome',
        'discover it miles': 'Discover it Miles',
        'discover it student': 'Discover it Student',
        'discover it secured': 'Discover it Secured',
        'discover': 'Discover Card',
        
        # === SYNCHRONY / STORE CARDS ===
        'amazon store card': 'Amazon Store Card',
        'walmart rewards card': 'Walmart Rewards Card',
        'target redcard': 'Target REDcard',
        'sam\'s club mastercard': 'Sam\'s Club Mastercard',
        'lowes advantage': 'Lowe\'s Advantage Card',
        'home depot credit': 'Home Depot Credit Card',
        'best buy credit': 'Best Buy Credit Card',
        'apple card': 'Apple Card',
        'paypal cashback': 'PayPal Cashback Mastercard',
        'venmo credit card': 'Venmo Credit Card',
        
        # === CREDIT UNIONS ===
        'navy federal': 'Navy Federal Card',
        'penfed': 'PenFed Card',
        'usaa': 'USAA Card',
        'alliant': 'Alliant Card',
        
        # === FINTECH CARDS ===
        'sofi credit card': 'SoFi Credit Card',
        'apple card': 'Apple Card',
        'upgrade card': 'Upgrade Card',
        'petal card': 'Petal Card',
        'chime credit builder': 'Chime Credit Builder',
        
        # === BARCLAYS CARDS ===
        'barclays arrival': 'Barclays Arrival Card',
        'jetblue card': 'JetBlue Card',
        'jetblue plus': 'JetBlue Plus Card',
        'wyndham rewards': 'Wyndham Rewards Card',
        'frontier airlines': 'Frontier Airlines Card',
        'hawaiian airlines': 'Hawaiian Airlines Card',
        'barclays': 'Barclays Card',
    }
    
    text_lower = text.lower()
    # Check longer keys first for more specific matches
    for key in sorted(issuers.keys(), key=len, reverse=True):
        if key in text_lower:
            return issuers[key]
    
    return "Credit Card"


def extract_membership_name(subject: str, body: str = "") -> str:
    """
    Extract membership/subscription name from email subject or body.
    
    Args:
        subject: Email subject
        body: Email body for additional context
    
    Returns:
        Membership name string (e.g., "Walmart+", "Amazon Prime")
    """
    text = f"{subject} {body}"
    # Normalize apostrophes (replace curly/smart quotes with straight quotes)
    text_lower = text.lower().replace('\u2019', "'").replace('\u2018', "'")
    
    # Check known memberships FIRST (more specific to less specific)
    known_memberships = {
        # === BANK / FINANCIAL MEMBERSHIPS ===
        'bank of america preferred rewards platinum': 'Bank of America Preferred Rewards Platinum',
        'bank of america preferred rewards gold': 'Bank of America Preferred Rewards Gold',
        'bank of america preferred rewards': 'Bank of America Preferred Rewards',
        'preferred rewards gold': 'Bank of America Preferred Rewards Gold',
        'preferred rewards platinum': 'Bank of America Preferred Rewards Platinum',
        'chase private client': 'Chase Private Client',
        'chase sapphire banking': 'Chase Sapphire Banking',
        'wells fargo premier': 'Wells Fargo Premier',
        'citi priority': 'Citi Priority',
        'capital one 360': 'Capital One 360',
        
        # === WAREHOUSE / WHOLESALE CLUBS ===
        'costco gold star': 'Costco Gold Star Membership',
        'gold star membership': 'Costco Gold Star Membership',
        'costco executive': 'Costco Executive Membership',
        'executive membership': 'Costco Executive Membership',
        'costco business': 'Costco Business Membership',
        'costco': 'Costco Membership',
        "sam's club plus": "Sam's Club Plus",
        'sams club plus': "Sam's Club Plus",
        "sam's club": "Sam's Club Membership",
        'sams club': "Sam's Club Membership",
        "bj's inner circle": "BJ's Inner Circle Membership",
        "bj's perks rewards": "BJ's Perks Rewards",
        "bj's wholesale": "BJ's Wholesale Membership",
        'bjs wholesale': "BJ's Wholesale Membership",
        "bj's": "BJ's Wholesale Membership",
        
        # === RETAIL MEMBERSHIPS ===
        'walmart+': 'Walmart+',
        'walmart plus': 'Walmart+',
        'amazon prime': 'Amazon Prime',
        'prime membership': 'Amazon Prime',
        'target circle 360': 'Target Circle 360',
        'target circle': 'Target Circle',
        'best buy totaltech': 'Best Buy Totaltech',
        'best buy plus': 'Best Buy Plus',
        'cvs carepass': 'CVS CarePass',
        'walgreens mywalgreens': 'myWalgreens+',
        'rite aid wellness+': 'Rite Aid Wellness+',
        'petco vital care': 'Petco Vital Care',
        'petsmart treats': 'PetSmart Treats Rewards',
        'chewy autoship': 'Chewy Autoship',
        'sephora beauty insider': 'Sephora Beauty Insider',
        'ulta ultamate rewards': 'Ulta Ultamate Rewards',
        'nordstrom nordy club': 'Nordstrom Nordy Club',
        "kohl's rewards": "Kohl's Rewards",
        "macy's star rewards": "Macy's Star Rewards",
        'rei co-op': 'REI Co-op Membership',
        "dick's scorecard": "Dick's Scorecard",
        'nike membership': 'Nike Membership',
        'adidas creators club': 'Adidas Creators Club',
        'lululemon membership': 'Lululemon Membership',
        
        # === FOOD / GROCERY MEMBERSHIPS ===
        'instacart+': 'Instacart+',
        'instacart express': 'Instacart Express',
        'shipt': 'Shipt Membership',
        'freshly': 'Freshly Subscription',
        'hello fresh': 'HelloFresh',
        'blue apron': 'Blue Apron',
        'home chef': 'Home Chef',
        'factor meals': 'Factor Meals',
        'green chef': 'Green Chef',
        'panera unlimited sip club': 'Panera Unlimited Sip Club',
        'panera bread': 'Panera Bread Rewards',
        'starbucks rewards': 'Starbucks Rewards',
        'dunkin rewards': "Dunkin' Rewards",
        'chick-fil-a one': 'Chick-fil-A One',
        'chipotle rewards': 'Chipotle Rewards',
        'taco bell rewards': 'Taco Bell Rewards',
        "mcdonald's rewards": "McDonald's Rewards",
        "wendy's rewards": "Wendy's Rewards",
        
        # === FOOD DELIVERY ===
        'dashpass': 'DoorDash DashPass',
        'uber one': 'Uber One',
        'grubhub+': 'Grubhub+',
        
        # === STREAMING - VIDEO ===
        'netflix premium': 'Netflix Premium',
        'netflix standard': 'Netflix Standard',
        'netflix basic': 'Netflix Basic',
        'netflix': 'Netflix',
        'disney+': 'Disney+',
        'disney plus': 'Disney+',
        'hulu': 'Hulu',
        'hbo max': 'HBO Max',
        'max': 'Max (HBO)',
        'peacock premium': 'Peacock Premium',
        'peacock': 'Peacock',
        'paramount+': 'Paramount+',
        'paramount plus': 'Paramount+',
        'apple tv+': 'Apple TV+',
        'discovery+': 'Discovery+',
        'espn+': 'ESPN+',
        'youtube premium': 'YouTube Premium',
        'youtube tv': 'YouTube TV',
        'sling tv': 'Sling TV',
        'fubo tv': 'FuboTV',
        'philo': 'Philo',
        'crunchyroll': 'Crunchyroll',
        'funimation': 'Funimation',
        
        # === STREAMING - MUSIC ===
        'spotify premium': 'Spotify Premium',
        'spotify': 'Spotify',
        'apple music': 'Apple Music',
        'amazon music unlimited': 'Amazon Music Unlimited',
        'tidal': 'TIDAL',
        'pandora plus': 'Pandora Plus',
        'pandora premium': 'Pandora Premium',
        'sirius xm': 'SiriusXM',
        'siriusxm': 'SiriusXM',
        
        # === STREAMING - AUDIOBOOKS/READING ===
        'audible': 'Audible',
        'audible premium': 'Audible Premium Plus',
        'kindle unlimited': 'Kindle Unlimited',
        'scribd': 'Scribd',
        'kobo plus': 'Kobo Plus',
        
        # === FITNESS ===
        'planet fitness': 'Planet Fitness',
        'la fitness': 'LA Fitness',
        '24 hour fitness': '24 Hour Fitness',
        'equinox': 'Equinox',
        'orangetheory': 'Orangetheory Fitness',
        'crossfit': 'CrossFit',
        'peloton': 'Peloton',
        'apple fitness+': 'Apple Fitness+',
        'fitbit premium': 'Fitbit Premium',
        'noom': 'Noom',
        'weight watchers': 'WW (Weight Watchers)',
        
        # === GAMING ===
        'xbox game pass': 'Xbox Game Pass',
        'xbox live gold': 'Xbox Live Gold',
        'playstation plus': 'PlayStation Plus',
        'ps plus': 'PlayStation Plus',
        'nintendo switch online': 'Nintendo Switch Online',
        'ea play': 'EA Play',
        'ubisoft+': 'Ubisoft+',
        'geforce now': 'GeForce NOW',
        
        # === AIRLINES / TRAVEL ===
        'delta skymiles': 'Delta SkyMiles',
        'american aadvantage': 'American AAdvantage',
        'united mileageplus': 'United MileagePlus',
        'southwest rapid rewards': 'Southwest Rapid Rewards',
        'jetblue trueblue': 'JetBlue TrueBlue',
        'alaska mileage plan': 'Alaska Mileage Plan',
        'marriott bonvoy': 'Marriott Bonvoy',
        'hilton honors': 'Hilton Honors',
        'ihg one rewards': 'IHG One Rewards',
        'world of hyatt': 'World of Hyatt',
        'wyndham rewards': 'Wyndham Rewards',
        'choice privileges': 'Choice Privileges',
        'hertz gold plus': 'Hertz Gold Plus Rewards',
        'national emerald club': 'National Emerald Club',
        'enterprise plus': 'Enterprise Plus',
        'avis preferred': 'Avis Preferred',
        'tsa precheck': 'TSA PreCheck',
        'global entry': 'Global Entry',
        'clear': 'CLEAR',
        'priority pass': 'Priority Pass',
        
        # === CLOUD / SOFTWARE ===
        'microsoft 365': 'Microsoft 365',
        'office 365': 'Microsoft 365',
        'adobe creative cloud': 'Adobe Creative Cloud',
        'google one': 'Google One',
        'icloud+': 'iCloud+',
        'dropbox plus': 'Dropbox Plus',
        'evernote': 'Evernote',
        '1password': '1Password',
        'lastpass': 'LastPass',
        'nordvpn': 'NordVPN',
        'expressvpn': 'ExpressVPN',
        
        # === AUTO ===
        'aaa': 'AAA Membership',
        'onstar': 'OnStar',
        'sirius xm': 'SiriusXM',
    }
    
    # Check more specific patterns first (longer keys first)
    for key in sorted(known_memberships.keys(), key=len, reverse=True):
        if key in text_lower:
            return known_memberships[key]
    
    # Fallback to regex patterns for less common memberships
    membership_patterns = [
        # Pattern for "Welcome to <Membership>"  (stops at dash, exclamation, or "Your")
        r'Welcome to\s+([A-Za-z0-9\+]+)(?:\s*[–—!\-]|\s+Your)',
        
        # Pattern for "Your <Membership> Membership"
        r'Your\s+([A-Za-z0-9\+\s]+?)\s+(?:Membership|subscription)',
    ]
    
    for pattern in membership_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            membership = match.group(1).strip()
            # Clean up
            membership = re.sub(r'\s+', ' ', membership)
            if len(membership) > 2:
                return membership
    
    return "Membership"


def extract_company_name(sender: str, subject: str = "", body: str = "") -> str:
    """
    Extract company/brand name from sender email, subject, or body.
    Also checks email signatures like "Customer Support Team\\nWalmart"
    
    Args:
        sender: Email sender (e.g., "Amazon <deals@amazon.com>")
        subject: Email subject for additional context
        body: Email body for additional context
    
    Returns:
        Company name string
    """
    # Known brand mappings
    brand_map = {
        'amazon': 'Amazon',
        'flipkart': 'Flipkart',
        'myntra': 'Myntra',
        'ajio': 'AJIO',
        'meesho': 'Meesho',
        'snapdeal': 'Snapdeal',
        'ebay': 'eBay',
        'walmart': 'Walmart',
        'target': 'Target',
        'bestbuy': 'Best Buy',
        'costco': 'Costco',
        'swiggy': 'Swiggy',
        'zomato': 'Zomato',
        'ubereats': 'Uber Eats',
        'doordash': 'DoorDash',
        'dominos': 'Domino\'s',
        'pizzahut': 'Pizza Hut',
        'starbucks': 'Starbucks',
        'mcdonalds': 'McDonald\'s',
        'netflix': 'Netflix',
        'spotify': 'Spotify',
        'hotstar': 'Hotstar',
        'disney': 'Disney+',
        'paytm': 'Paytm',
        'phonepe': 'PhonePe',
        'gpay': 'Google Pay',
        'paypal': 'PayPal',
        'nike': 'Nike',
        'adidas': 'Adidas',
        'puma': 'Puma',
        'zara': 'Zara',
        'hm.com': 'H&M',
        'h&m': 'H&M',
        'uniqlo': 'Uniqlo',
        'shein': 'SHEIN',
        'nykaa': 'Nykaa',
        'bigbasket': 'BigBasket',
        'blinkit': 'Blinkit',
        'zepto': 'Zepto',
        'makemytrip': 'MakeMyTrip',
        'booking': 'Booking.com',
        'expedia': 'Expedia',
        'airbnb': 'Airbnb',
        'uber': 'Uber',
        'ola': 'Ola',
        'apple': 'Apple',
        'samsung': 'Samsung',
        'oneplus': 'OnePlus',
        'ikea': 'IKEA',
        'sephora': 'Sephora',
        'nordstrom': 'Nordstrom',
        'macys': 'Macy\'s',
        'jcpenney': 'JCPenney',
        'kohls': 'Kohl\'s',
        'gap': 'GAP',
        'oldnavy': 'Old Navy',
        'lenskart': 'Lenskart',
        'croma': 'Croma',
        'reliance': 'Reliance',
        'tata': 'Tata',
    }
    
    # First, try to extract from email signature patterns in body
    if body:
        # Common signature patterns:
        # "Warm regards,\nCompany Name"
        # "Best regards,\nThe Amazon Team"
        # "Customer Support Team\nWalmart"
        # "Thanks,\nFlipkart Team"
        # "Cheers,\nNike"
        
        signature_patterns = [
            # Pattern: "Customer Support Team <Company>" (same line or next line)
            r'(?:customer\s+)?(?:support|service|care)\s+team\s+([A-Z][A-Za-z0-9\s&\'\.]+?)(?:\s*$|\s*\n)',
            
            # Pattern: "Customer Support Team\n<Company>"
            r'(?:customer\s+)?(?:support|service|care)\s+team\s*\n+\s*([A-Z][A-Za-z0-9\s&\'\.]+?)\s*(?:\n|$)',
            
            # Pattern: "regards,\n<Company>" or "regards,\n<Company> Team"
            r'(?:warm\s*)?regards,?\s*\n+\s*(?:the\s+)?([A-Z][A-Za-z0-9\s&\'\.]+?)(?:\s+team)?\s*(?:\n|$)',
            
            # Pattern: "regards, <Company>" (same line)
            r'(?:warm\s*)?regards,?\s+([A-Z][A-Za-z0-9\s&\'\.]+?)(?:\s+team)?\s*(?:\n|$)',
            
            # Pattern: "thanks,\n<Company>"
            r'thanks,?\s*\n+\s*(?:the\s+)?([A-Z][A-Za-z0-9\s&\'\.]+?)(?:\s+team)?\s*(?:\n|$)',
            
            # Pattern: "cheers,\n<Company>"
            r'cheers,?\s*\n+\s*(?:the\s+)?([A-Z][A-Za-z0-9\s&\'\.]+?)(?:\s+team)?\s*(?:\n|$)',
            
            # Pattern: "The <Company> Team"
            r'(?:the\s+)?([A-Z][A-Za-z0-9\s&\'\.]+?)\s+team\s*(?:\n|$)',
            
            # Pattern: "Happy shopping!\n...\n<Company>"
            r'happy\s+shopping[!]?\s*[😊🎉]*\s*\n+.*?\n+\s*([A-Z][A-Za-z0-9\s&\'\.]+?)\s*(?:\n|$)',
            
            # Pattern: "Best,\n<Company>"
            r'best,?\s*\n+\s*([A-Z][A-Za-z0-9\s&\'\.]+?)\s*(?:\n|$)',
            
            # Pattern: "Sincerely,\n<Company>"
            r'sincerely,?\s*\n+\s*(?:the\s+)?([A-Z][A-Za-z0-9\s&\'\.]+?)(?:\s+team)?\s*(?:\n|$)',
        ]
        
        for pattern in signature_patterns:
            match = re.search(pattern, body, re.IGNORECASE | re.MULTILINE)
            if match:
                company = match.group(1).strip()
                # Clean up the extracted name
                company = re.sub(r'\s+', ' ', company)  # Remove extra spaces
                # Skip if it looks like generic text
                skip_words = ['customer', 'support', 'service', 'team', 'regards', 'thanks', 'best', 'the']
                if company.lower() not in skip_words and len(company) > 2 and len(company) < 30:
                    # Check if it matches a known brand
                    for key, brand in brand_map.items():
                        if key in company.lower():
                            return brand
                    # Return the extracted company name if it looks valid
                    if company[0].isupper():
                        return company
    
    # Combine all text for searching known brands
    all_text = f"{sender} {subject} {body}".lower()
    
    # Try to find brand in text
    for key, brand in brand_map.items():
        if key in all_text:
            return brand
    
    # Try to extract name from sender format "Name <email@domain.com>"
    if '<' in sender:
        name_part = sender.split('<')[0].strip()
        if name_part and name_part.lower() not in ['noreply', 'no-reply', 'info', 'deals', 'offers', 'team', 'support']:
            # Check if it looks like a company name (not a personal name with space)
            if ' ' not in name_part or len(name_part) < 20:
                return name_part
    
    # Try to extract from email domain
    if '@' in sender:
        try:
            domain = sender.split('@')[1].split('>')[0].split('.')[0]
            if domain and domain.lower() not in ['gmail', 'yahoo', 'hotmail', 'outlook', 'mail', 'email']:
                return domain.capitalize()
        except:
            pass
    
    return "Store/Website"


def analyze_emails(emails: List[Dict], strict_mode: bool = False) -> Dict[str, List[Dict]]:
    """
    Analyze a list of emails and categorize them.
    
    Categories:
    - membership: Service subscriptions (Amazon Prime, Netflix, Costco, etc.)
    - offer: Credit card benefits/rewards (Amex, Delta SkyMiles, etc.)
    - coupon: Discounts, promo codes, sales
    - excluded: Social media, forums, newsletters
    - normal: Other emails
    
    Args:
        emails: List of email dictionaries from gmail_reader
        strict_mode: If True, only include emails from known shopping domains
    
    Returns:
        Dictionary with categorized emails
    """
    results = {
        'membership': [],
        'offer': [],
        'coupon': [],
        'excluded': [],
        'normal': []
    }
    
    for email in emails:
        # Combine subject and body for analysis
        full_text = f"{email['subject']} {email['body']}"
        sender = email.get('sender', '')
        
        # Analyze the text with sender info
        analysis = analyze_text(full_text, sender)
        
        # Add analysis results to email dict
        email['category'] = analysis['category']
        email['membership_matches'] = analysis['membership_matches']
        email['offer_matches'] = analysis['offer_matches']
        email['coupon_matches'] = analysis.get('coupon_matches', [])
        email['is_shopping_domain'] = analysis['is_shopping_domain']
        
        # In strict mode, only include shopping domain emails
        if strict_mode and not analysis['is_shopping_domain']:
            if analysis['category'] in ['Membership', 'Offer', 'Coupon']:
                # Demote to normal if not from shopping domain
                email['category'] = 'Normal'
                results['normal'].append(email)
                continue
        
        # Categorize
        category = analysis['category'].lower()
        if category in results:
            results[category].append(email)
    
    return results


def print_results(results: Dict[str, List[Dict]], verbose: bool = False):
    """
    Print categorized email results.
    
    Args:
        results: Dictionary of categorized emails
        verbose: If True, show more details
    """
    print("\n" + "=" * 60)
    print("📊 EMAIL ANALYSIS RESULTS")
    print("=" * 60)
    
    # Summary (exclude 'excluded' from main count)
    total = sum(len(v) for k, v in results.items() if k != 'excluded')
    excluded_count = len(results.get('excluded', []))
    
    print(f"\n📧 Total emails analyzed: {total}")
    print(f"   • Membership (Prime, Netflix, Costco): {len(results['membership'])}")
    print(f"   • Offer (Credit Cards, Rewards): {len(results['offer'])}")
    print(f"   • Coupon (Discounts, Promo Codes): {len(results['coupon'])}")
    print(f"   • Normal: {len(results['normal'])}")
    if excluded_count > 0:
        print(f"   • Excluded (non-shopping): {excluded_count}")
    
    # Membership emails (Service subscriptions)
    if results['membership']:
        print("\n" + "-" * 60)
        print("🔔 MEMBERSHIP (Service Subscriptions):")
        print("   Amazon Prime, Netflix, Costco, Spotify, etc.")
        print("-" * 60)
        for i, email in enumerate(results['membership'], 1):
            shopping_badge = "🛒" if email.get('is_shopping_domain') else ""
            membership_name = extract_membership_name(email['subject'], email.get('body', ''))
            print(f"\n  {i}. {shopping_badge} {email['subject']}")
            print(f"     🏪 Membership: {membership_name}")
            print(f"     From: {email['sender']}")
            print(f"     Date: {email['date']}")
            if verbose and email['membership_matches']:
                print(f"     Keywords: {', '.join(str(m) for m in email['membership_matches'][:5])}")
    
    # Offer emails (Credit cards, rewards)
    if results['offer']:
        print("\n" + "-" * 60)
        print("💳 OFFER (Credit Card Benefits & Rewards):")
        print("   Amex, Delta SkyMiles, Chase, Visa, etc.")
        print("-" * 60)
        for i, email in enumerate(results['offer'], 1):
            shopping_badge = "🛒" if email.get('is_shopping_domain') else ""
            card_name = extract_credit_card_name(email['subject'], email.get('body', ''))
            print(f"\n  {i}. {shopping_badge} {email['subject']}")
            print(f"     💳 Card: {card_name}")
            print(f"     From: {email['sender']}")
            print(f"     Date: {email['date']}")
            if verbose and email['offer_matches']:
                print(f"     Keywords: {', '.join(str(m) for m in email['offer_matches'][:5])}")
    
    # Coupon emails (Discounts, promo codes)
    if results['coupon']:
        print("\n" + "-" * 60)
        print("🏷️  COUPON (Discounts & Promo Codes):")
        print("   Sales, cashback, free shipping, etc.")
        print("-" * 60)
        for i, email in enumerate(results['coupon'], 1):
            shopping_badge = "🛒" if email.get('is_shopping_domain') else ""
            store_name = extract_company_name(email['sender'], email['subject'], email.get('body', ''))
            print(f"\n  {i}. {shopping_badge} {email['subject']}")
            print(f"     🏪 Applicable at: {store_name}")
            print(f"     From: {email['sender']}")
            print(f"     Date: {email['date']}")
            if verbose and email.get('coupon_matches'):
                print(f"     Keywords: {', '.join(str(m) for m in email['coupon_matches'][:5])}")
    
    # Excluded emails (only if verbose)
    if verbose and results.get('excluded'):
        print("\n" + "-" * 60)
        print("🚫 EXCLUDED EMAILS (Social/Forums/Newsletters):")
        print("-" * 60)
        for i, email in enumerate(results['excluded'][:5], 1):  # Show max 5
            print(f"\n  {i}. {email['subject']}")
            print(f"     From: {email['sender']}")
        if len(results['excluded']) > 5:
            print(f"\n  ... and {len(results['excluded']) - 5} more excluded")
    
    # Normal emails (only if verbose)
    if verbose and results['normal']:
        print("\n" + "-" * 60)
        print("📄 NORMAL EMAILS:")
        print("-" * 60)
        for i, email in enumerate(results['normal'][:5], 1):  # Show max 5
            print(f"\n  {i}. {email['subject']}")
            print(f"     From: {email['sender']}")
        if len(results['normal']) > 5:
            print(f"\n  ... and {len(results['normal']) - 5} more normal emails")
    
    print("\n" + "=" * 60)


def get_subscription_count(results: Dict[str, List[Dict]]) -> Dict[str, int]:
    """
    Count unique senders for subscription-related emails.
    
    Args:
        results: Categorized email results
    
    Returns:
        Dictionary with sender counts
    """
    membership_senders = set()
    offer_senders = set()
    
    for email in results['membership'] + results['both']:
        # Extract email from sender (e.g., "Name <email@example.com>" -> "email@example.com")
        sender = email['sender']
        if '<' in sender and '>' in sender:
            sender = sender.split('<')[1].split('>')[0]
        membership_senders.add(sender.lower())
    
    for email in results['offer'] + results['both']:
        sender = email['sender']
        if '<' in sender and '>' in sender:
            sender = sender.split('<')[1].split('>')[0]
        offer_senders.add(sender.lower())
    
    return {
        'unique_membership_senders': len(membership_senders),
        'unique_offer_senders': len(offer_senders),
        'membership_senders': list(membership_senders),
        'offer_senders': list(offer_senders)
    }


def main():
    """Main entry point for the email analyzer."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Gmail Email Analyzer - Detect memberships and offers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyzer.py                    # Analyze last 50 emails
  python analyzer.py -n 100             # Analyze last 100 emails
  python analyzer.py -d 30              # Analyze emails from last 30 days
  python analyzer.py -v                 # Verbose output with keywords
  python analyzer.py --export           # Export results to CSV
  python analyzer.py --revoke           # Revoke OAuth token and exit
        """
    )
    
    parser.add_argument('-n', '--num-emails', type=int, default=50,
                        help='Number of emails to fetch (default: 50)')
    parser.add_argument('-d', '--days', type=int,
                        help='Fetch emails from last N days')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Show verbose output with matched keywords')
    parser.add_argument('--export', action='store_true',
                        help='Export results to CSV file')
    parser.add_argument('--json', action='store_true',
                        help='Export results to JSON file with HTML viewer')
    parser.add_argument('--revoke', action='store_true',
                        help='Revoke OAuth token and exit')
    parser.add_argument('--stats', action='store_true',
                        help='Show subscription statistics')
    parser.add_argument('--strict', action='store_true',
                        help='Only show emails from known shopping domains')
    
    args = parser.parse_args()
    
    # Handle revoke token
    if args.revoke:
        revoke_token()
        return
    
    print("=" * 60)
    print("📧 GMAIL EMAIL ANALYZER")
    print("   Membership & Offer Detection POC")
    print("=" * 60)
    
    try:
        # Step 1: Authenticate
        print("\n🔐 Step 1: Authenticating with Gmail...")
        service = get_gmail_service()
        
        # Step 2: Fetch emails
        print("\n📥 Step 2: Fetching emails...")
        if args.days:
            emails = fetch_emails_by_days(service, days=args.days, max_results=args.num_emails)
        else:
            emails = fetch_emails(service, max_results=args.num_emails)
        
        if not emails:
            print("\n⚠️  No emails found to analyze.")
            return
        
        # Step 3: Analyze emails
        print(f"\n🔍 Step 3: Analyzing {len(emails)} emails...")
        if args.strict:
            print("   (Strict mode: Only showing shopping domain emails)")
        results = analyze_emails(emails, strict_mode=args.strict)
        
        # Step 4: Display results
        print_results(results, verbose=args.verbose)
        
        # Show statistics if requested
        if args.stats:
            stats = get_subscription_count(results)
            print("\n📊 SUBSCRIPTION STATISTICS:")
            print("-" * 40)
            print(f"   Unique membership senders: {stats['unique_membership_senders']}")
            print(f"   Unique offer senders: {stats['unique_offer_senders']}")
            
            if args.verbose:
                if stats['membership_senders']:
                    print(f"\n   Membership senders:")
                    for sender in stats['membership_senders'][:10]:
                        print(f"      • {sender}")
                if stats['offer_senders']:
                    print(f"\n   Offer senders:")
                    for sender in stats['offer_senders'][:10]:
                        print(f"      • {sender}")
        
        # Export to CSV if requested
        if args.export:
            try:
                from export_csv import export_to_csv
                filename = export_to_csv(results)
                print(f"\n✅ Results exported to: {filename}")
            except ImportError:
                print("\n⚠️  export_csv module not fully implemented yet.")
            except Exception as e:
                print(f"\n❌ Export failed: {e}")
        
        # Export to JSON with HTML viewer if requested
        if args.json:
            try:
                from export_json import export_to_json, generate_html_viewer
                
                # Get user email from the service
                profile = service.users().getProfile(userId='me').execute()
                user_email = profile.get('emailAddress', 'unknown@email.com')
                
                print(f"\n📤 Exporting JSON for: {user_email}")
                
                # Export JSON
                json_file = export_to_json(
                    results, 
                    user_email,
                    extract_membership_name,
                    extract_credit_card_name,
                    extract_company_name,
                    output_file="email_analysis.json"
                )
                
                # Generate HTML viewer
                html_file = generate_html_viewer(json_file, "email_viewer.html")
                
                print(f"\n✅ JSON exported to: {json_file}")
                print(f"✅ HTML viewer created: {html_file}")
                print(f"\n💡 Open {html_file} in a browser to view your analysis!")
                
            except Exception as e:
                print(f"\n❌ JSON export failed: {e}")
                raise
        
        print("\n✅ Analysis complete!")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


# For running directly
if __name__ == "__main__":
    main()
