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
# Use generalized patterns that work for ANY store/card/membership
from patterns_generalized import analyze_text, categorize_email, is_commercial_domain, categorize_from_sender
from image_extractor import get_email_images_with_ocr
from footer_extractor import get_enhanced_email_data, extract_store_name_from_footer


def extract_credit_card_name(subject: str, body: str = "") -> str:
    """
    Extract credit card name from email subject or body.
    PRIORITY: Extract from body first (more accurate full names), then subject.
    
    Args:
        subject: Email subject
        body: Email body for additional context
    
    Returns:
        Credit card name string
    """
    # STEP 1: Try to extract from body first (most accurate)
    if body:
        # Pattern: "Welcome to <Full Card Name> Card" or "Congratulations on your <Card Name> approval"
        body_patterns = [
            r'Welcome to\s+([A-Z][A-Za-z0-9\s®]+?)\s+(?:Credit )?Card',
            r'Congratulations on your\s+([A-Z][A-Za-z0-9\s®]+?)\s+approval',
            r'Your\s+([A-Z][A-Za-z0-9\s®]+?)\s+(?:Credit )?Card\s+(?:is|has been)',
            r'activate your\s+([A-Z][A-Za-z0-9\s®]+?)\s+(?:Credit )?Card',
        ]
        
        for pattern in body_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                card_name = match.group(1).strip()
                # Clean up
                card_name = re.sub(r'\s+', ' ', card_name)
                card_name = re.sub(r'\s*®\s*', '®', card_name)
                # Filter out generic words
                if len(card_name) > 5 and card_name.lower() not in ['your new', 'new us', 'us cardmember', 'the new']:
                    return card_name
    
    # STEP 2: Try specific patterns for known card issuers in subject + body
    text = f"{subject} {body}"
    
    # Known credit card patterns - ordered by specificity (most specific first)
    card_patterns = [
        # American Express cards
        r'(American Express[\s®]*(?:Blue Cash Everyday|Blue Cash Preferred|Gold|Platinum|Green|Delta SkyMiles|Hilton Honors|Marriott Bonvoy)?)[\s®]*(?:Credit )?Card',
        r'(Amex[\s®]*(?:Blue Cash Everyday|Blue Cash Preferred|Gold|Platinum|Green)?)[\s®]*(?:Credit )?Card',
        
        # Delta SkyMiles cards
        r'(Delta SkyMiles[\s®]*(?:Gold|Platinum|Reserve|Blue)?[\s®]*(?:Business)?[\s®]*(?:American Express)?)[\s®]*(?:Credit )?Card',
        
        # Chase cards - order matters! More specific first
        r'(Chase[\s®]*Sapphire Reserve)[\s®]*(?:Credit )?Card',
        r'(Chase[\s®]*Sapphire Preferred)[\s®]*(?:Credit )?Card',
        r'(Chase[\s®]*Freedom Unlimited)[\s®]*(?:Credit )?Card',
        r'(Chase[\s®]*Freedom Flex)[\s®]*(?:Credit )?Card',
        r'(Chase[\s®]*Freedom)[\s®]*(?:Credit )?Card',
        r'(Chase[\s®]*Ink Business)[\s®]*(?:Credit )?Card',
        
        # Capital One cards - order matters! More specific first
        r'(Capital One[\s®]*Venture X Rewards?)[\s®]*(?:Credit )?Card',
        r'(Capital One[\s®]*Venture Rewards?)[\s®]*(?:Credit )?Card',
        r'(Capital One[\s®]*Venture)[\s®]*(?:Credit )?Card',
        r'(Capital One[\s®]*Quicksilver)[\s®]*(?:Credit )?Card',
        r'(Capital One[\s®]*SavorOne)[\s®]*(?:Credit )?Card',
        r'(Capital One[\s®]*Spark)[\s®]*(?:Credit )?Card',
        
        # Citi cards
        r'(Citi[\s®]*(?:Double Cash|Premier|Custom Cash|Diamond Preferred)?)[\s®]*(?:Credit )?Card',
        
        # Discover cards - order matters!
        r'(Discover[\s®]*it Miles)[\s®]*(?:Credit )?Card',
        r'(Discover[\s®]*it Chrome)[\s®]*(?:Credit )?Card',
        r'(Discover[\s®]*it)[\s®]*(?:Credit )?Card',
        
        # Bank of America cards - order matters!
        r'(Bank of America[\s®]*Premium Rewards)[\s®]*(?:Credit )?Card',
        r'(Bank of America[\s®]*Cash Rewards)[\s®]*(?:Credit )?Card',
        r'(Bank of America[\s®]*Travel Rewards)[\s®]*(?:Credit )?Card',
        r'(Bank of America[\s®]*Customized Cash)[\s®]*(?:Credit )?Card',
        
        # Wells Fargo cards
        r'(Wells Fargo[\s®]*(?:Active Cash|Autograph|Reflect)?)[\s®]*(?:Credit )?Card',
        
        # Generic card patterns
        r'((?:Visa|Mastercard|Discover)[\s®]*(?:Signature|Platinum|Gold|Rewards)?)[\s®]*(?:Credit )?Card',
    ]
    
    for pattern in card_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            card_name = match.group(1).strip()
            # Clean up the card name
            card_name = re.sub(r'\s+', ' ', card_name)
            # Keep ® symbol but remove extra spaces around it
            card_name = re.sub(r'\s*®\s*', '®', card_name)
            if len(card_name) > 5:
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
    GENERALIZED APPROACH: Dynamically extracts store name + program name from email body.
    Falls back to hardcoded mappings only if dynamic extraction fails.
    
    Args:
        subject: Email subject
        body: Email body for additional context
    
    Returns:
        Membership name string (e.g., "Walmart+", "Amazon Prime", "Sephora Beauty Insider")
    """
    text = f"{subject} {body}"
    # Normalize apostrophes (replace curly/smart quotes with straight quotes)
    text_lower = text.lower().replace('\u2019', "'").replace('\u2018', "'")
    
    # === STEP 1: DYNAMIC EXTRACTION FROM BODY ===
    # Try to extract membership name from email body using generalized patterns
    # This handles cases like "Your Sephora Beauty Insider membership" dynamically
    
    if body:
        # Pattern 1: "Your <StoreName> <ProgramName> membership/rewards/program"
        # Example: "Your Sephora Beauty Insider membership" → "Sephora Beauty Insider"
        # More specific patterns to avoid false matches
        body_patterns = [
            # "Your Sam's Club Plus Membership is now active" - looks for full proper name before "Membership"
            r'(?:your|the)\s+([A-Z][A-Za-z0-9\s\'\+®\.&-]{3,50}?)\s+(?:Membership|membership)\s+is\s+(?:now\s+)?active',
            
            # "Your Sephora Beauty Insider membership" - requires capital letter start
            r'Your\s+([A-Z][A-Za-z][A-Za-z0-9\s\'\+®\.&-]{3,50}?)\s+(?:membership|rewards?|program)\s+(?:is|keeps|unlocks|provides)',
            
            # "Program: Bank of America Preferred Rewards®" - from structured sections
            r'Program:\s+([A-Z][A-Za-z0-9\s\'\+®\.&-]{3,50}?)(?:\s*\n|\s*Tier:)',
            
            # "Membership Plan: Sam's Club Plus Membership" - from membership details section
            r'Membership Plan:\s+([A-Z][A-Za-z0-9\s\'\+®\.&-]{3,50}?)\s+(?:\(|$)',
            
            # "enrolled in Bank of America Preferred Rewards®"
            r'enrolled in\s+([A-Z][A-Za-z0-9\s\'\+®\.&-]{3,50}?)(?:\s*\.\s*|\s*$)',
            
            # "joining Sam's Club" - extract store name from joining context
            r'Thank you for joining\s+([A-Z][A-Za-z0-9\s\'\+®\.&-]{3,50}?)(?:\s*\.\s*|\s*$)',
        ]
        
        for pattern in body_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                membership_name = match.group(1).strip()
                # Clean up extra spaces and special characters
                membership_name = re.sub(r'\s+', ' ', membership_name)
                membership_name = membership_name.strip('.,;:')
                
                # Filter out generic/invalid names
                invalid_names = ['membership', 'membership details', 'your membership', 
                                'active membership', 'tier', 'gold tier', 'platinum tier',
                                'exclusive to us', 'us members', 'us shoppers']
                if membership_name.lower() in invalid_names:
                    continue
                
                # Must be at least 2 words or have special characters like + or '
                words = membership_name.split()
                if len(words) >= 2 or '+' in membership_name or "'" in membership_name:
                    # Clean up the name
                    membership_name = membership_name.replace('®', '').strip()
                    
                    # Check if this extracted name has a better mapping in known_memberships
                    # e.g., "Ultamate Rewards" → "Ulta Beauty Ultamate Rewards"
                    text_lower_check = (subject + " " + body).lower().replace('\u2019', "'").replace('\u2018', "'")
                    
                    # Quick check for hardcoded mappings of the extracted name
                    membership_lower = membership_name.lower()
                    known_membership_keys = {
                        'ultamate rewards': 'Ulta Beauty Ultamate Rewards',
                        'ulta ultamate rewards': 'Ulta Beauty Ultamate Rewards',
                        'ulta rewards': 'Ulta Beauty Ultamate Rewards',
                        'sephora beauty insider': 'Sephora Beauty Insider',
                        'beauty insider': 'Sephora Beauty Insider',
                        'kroger boost+': 'Kroger Boost+',
                        'kroger boost plus': 'Kroger Boost+',
                        "bj's club+": "BJ's Club+",
                        "bjs club+": "BJ's Club+",
                    }
                    
                    if membership_lower in known_membership_keys:
                        return known_membership_keys[membership_lower]
                    
                    return membership_name
    
    # === STEP 2: CHECK HARDCODED MAPPINGS ===
    # Check hardcoded mappings BEFORE subject patterns for known programs
    # This ensures "Ultamate Rewards" → "Ulta Beauty Ultamate Rewards"
    
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
        "bj's club+": "BJ's Club+",
        "bj's club plus": "BJ's Club+",
        "bjs club+": "BJ's Club+",
        "bj's wholesale": "BJ's Club+",
        'bjs wholesale': "BJ's Club+",
        "bj's": "BJ's Club+",
        
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
        'ultamate rewards': 'Ulta Beauty Ultamate Rewards',
        'ulta ultamate rewards': 'Ulta Beauty Ultamate Rewards',
        'ulta rewards': 'Ulta Beauty Ultamate Rewards',
        'ulta beauty': 'Ulta Beauty Ultamate Rewards',
        'nordstrom nordy club': 'Nordstrom Nordy Club',
        "kohl's rewards": "Kohl's Rewards",
        "macy's star rewards": "Macy's Star Rewards",
        'rei co-op': 'REI Co-op Membership',
        "dick's scorecard": "Dick's Scorecard",
        'nike membership': 'Nike Membership',
        'adidas creators club': 'Adidas Creators Club',
        'lululemon membership': 'Lululemon Membership',
        'j.crew passport': 'J.Crew Passport',
        'jcrew passport': 'J.Crew Passport',
        
        # === FOOD / GROCERY MEMBERSHIPS ===
        'kroger boost+': 'Kroger Boost+',
        'kroger boost plus': 'Kroger Boost+',
        'kroger boost': 'Kroger Boost+',
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
    
    # Check hardcoded mappings (longer keys first for specificity)
    for key in sorted(known_memberships.keys(), key=len, reverse=True):
        if key in text_lower:
            return known_memberships[key]
    
    # === STEP 3: SUBJECT LINE PATTERNS ===
    # Extract from subject if body extraction and hardcoded mappings failed
    # Pattern: "Beauty Insider:" → extract "Beauty Insider"
    subject_tier_pattern = r'\b([\w\s\'\+]+)\s+(club\+|boost\+|plus|premium|pro|rewards?|insider|member|circle|perks?):\s'
    subject_match = re.search(subject_tier_pattern, subject, re.IGNORECASE)
    if subject_match:
        store_part = subject_match.group(1).strip()
        program_part = subject_match.group(2).strip()
        membership_name = f"{store_part.title()} {program_part.capitalize()}"
        # Fix common capitalizations
        membership_name = membership_name.replace("Club+", "Club+").replace("Boost+", "Boost+")
        return membership_name
    
    # === STEP 4: FINAL FALLBACK ===
    # If nothing else works, return generic "Membership"
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
    # EXCEPTION: Skip extraction for testing emails from @innovinlabs.com
    # These are forwarded emails, so prioritize image/footer extraction instead
    if '@innovinlabs.com' in sender.lower():
        return "Unknown Store"
    
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
        # "Happy shopping,\nFreshMart Foods Team"
        # "Warm regards,\nCompany Name"
        # "Best regards,\nThe Amazon Team"
        # "Customer Support Team\nWalmart"
        # "Thanks,\nFlipkart Team"
        # "Cheers,\nNike"
        
        signature_patterns = [
            # === GENERAL PATTERNS (Highest Priority) ===
            # Pattern: "<Any phrase>, <Company> Team" (same line)
            # Matches: "Happy shopping, FreshMart Team", "Stay fit, Nike Team", "Keep saving, Walmart Team", etc.
            r'[A-Za-z\s]+[!,]\s*(?:the\s+)?([A-Z][A-Za-z0-9\s&\'.]+?)\s+team\s',
            
            # Pattern: "<Any phrase>,\n<Company> Team" or "<Any phrase>,\n<Company>"
            # Matches multi-line signatures with any closing phrase
            r'[A-Za-z\s]+[!,]\s*\n+\s*(?:the\s+)?([A-Z][A-Za-z0-9\s&\'.]+?)(?:\s+team)?\s*(?:\n|$)',
            
            # Pattern: "Customer Support Team\n<Company>"
            r'(?:customer\s+)?(?:support|service|care)\s+team\s*\n+\s*([A-Z][A-Za-z0-9\s\&\'.]+?)\s*(?:\n|$)',
            
            # Pattern: "Customer Support Team <Company>" (same line)
            r'(?:customer\s+)?(?:support|service|care)\s+team[,\s]+([A-Z][A-Za-z0-9\s\&\'.]+?)(?:\s*$|\s*\n)',
            
            # Pattern: "Warm regards,\n<Company>" or "Warm regards,\n<Company> Team"
            r'(?:warm\s+)?regards[!,]*\s*\n+\s*(?:the\s+)?([A-Z][A-Za-z0-9\s\&\'.]+?)(?:\s+team)?\s*(?:\n|$)',
            
            # Pattern: "regards, <Company>" (same line)
            r'(?:warm\s+)?regards[!,]*\s+([A-Z][A-Za-z0-9\s\&\'.]+?)(?:\s+team)?\s*(?:\n|$)',
            
            # Pattern: "Thanks,\n<Company> Team"
            r'thanks[!,]*\s*\n+\s*(?:the\s+)?([A-Z][A-Za-z0-9\s\&\'.]+?)(?:\s+team)?\s*(?:\n|$)',
            
            # Pattern: "Cheers,\n<Company>"
            r'cheers[!,]*\s*\n+\s*(?:the\s+)?([A-Z][A-Za-z0-9\s\&\'.]+?)(?:\s+team)?\s*(?:\n|$)',
            
            # Pattern: "Best,\n<Company>"
            r'best[!,]*\s*\n+\s*(?:the\s+)?([A-Z][A-Za-z0-9\s\&\'.]+?)(?:\s+team)?\s*(?:\n|$)',
            
            # Pattern: "Sincerely,\n<Company>"
            r'sincerely[!,]*\s*\n+\s*(?:the\s+)?([A-Z][A-Za-z0-9\s\&\'.]+?)(?:\s+team)?\s*(?:\n|$)',
            
            # Pattern: "The <Company> Team" (standalone)
            r'\bthe\s+([A-Z][A-Za-z0-9\s&\'.]+?)\s+team\b',
        ]
        
        for pattern in signature_patterns:
            match = re.search(pattern, body, re.IGNORECASE | re.MULTILINE)
            if match:
                company = match.group(1).strip()
                # Clean up the extracted name
                company = re.sub(r'\s+', ' ', company)  # Remove extra spaces
                # Skip if it looks like generic text
                skip_words = ['customer', 'support', 'service', 'team', 'regards', 'thanks', 'best', 'the', 'shopping']
                if company.lower() not in skip_words and len(company) > 2 and len(company) < 50:
                    # Return the extracted company name if it looks valid (starts with capital letter)
                    if company[0].isupper():
                        # Check if it matches a known brand for normalization
                        for key, brand in brand_map.items():
                            if key in company.lower():
                                return brand
                        # Return the extracted company name as-is (prioritize signature over body content)
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
            # Skip if it looks like a personal name (First Last format)
            # Personal names typically have exactly 2 or 3 parts
            name_parts = name_part.split()
            if len(name_parts) >= 2 and len(name_parts) <= 3:
                # Likely a personal name like "Linto Jomon" or "John Q. Smith"
                # Skip this and try domain extraction instead
                pass
            elif ' ' not in name_part or len(name_part) < 20:
                # Single word name or short compound - likely a company
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


def extract_giftcard_details(subject: str, body: str = "") -> Dict:
    """
    Extract gift card details from email subject and body.
    
    Args:
        subject: Email subject
        body: Email body
    
    Returns:
        Dictionary with card_number, pin, value, and store_name
    """
    text = f"{subject} {body}"
    
    details = {
        'card_number': None,
        'pin': None,
        'value': None,
        'store_name': None,
        'redemption_url': None
    }
    
    # Extract card number (various formats)
    card_patterns = [
        r'(?:Card|Gift\s*Card)\s*(?:Number|#|No\.?)?\s*:?\s*([0-9]{4}[\s-]?[0-9]{4}[\s-]?[0-9]{4}[\s-]?[0-9]{4})',  # 16 digits
        r'(?:Card|Gift\s*Card)\s*(?:Number|#|No\.?)?\s*:?\s*([0-9]{10,19})',  # 10-19 digits
        r'Card\s*Code\s*:?\s*([A-Z0-9]{10,20})',  # Alphanumeric code
    ]
    
    for pattern in card_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            details['card_number'] = match.group(1).strip()
            break
    
    # Extract PIN
    pin_patterns = [
        r'PIN\s*:?\s*(\d{4,8})',
        r'Security\s*Code\s*:?\s*(\d{3,4})',
        r'Access\s*Code\s*:?\s*(\d{4,8})',
    ]
    
    for pattern in pin_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            details['pin'] = match.group(1).strip()
            break
    
    # Extract card value
    value_patterns = [
        r'(?:Card\s*)?(?:Value|Amount|Balance)\s*:?\s*\$?([0-9,]+(?:\.[0-9]{2})?)',
        r'\$([0-9,]+(?:\.[0-9]{2})?)\s*(?:Gift\s*Card|Card)',
        r'(?:Worth|Valued\s*at)\s*\$?([0-9,]+(?:\.[0-9]{2})?)',
    ]
    
    for pattern in value_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            details['value'] = '$' + match.group(1).strip()
            break
    
    # Extract redemption URL
    url_pattern = r'(?:Redeem\s*(?:at|here)|Visit)\s*:?\s*(https?://[^\s<>\"]+)'
    match = re.search(url_pattern, text, re.IGNORECASE)
    if match:
        details['redemption_url'] = match.group(1).strip()
    
    return details


def analyze_emails(emails: List[Dict], strict_mode: bool = False, enable_ocr: bool = False) -> Dict[str, List[Dict]]:
    """
    Analyze a list of emails and categorize them.
    
    Categories:
    - membership: Service subscriptions (Amazon Prime, Netflix, Costco, etc.)
    - offer: Credit card benefits/rewards (Amex, Delta SkyMiles, etc.)
    - giftcard: Gift cards and store credits
    - coupon: Discounts, promo codes, sales
    - excluded: Social media, forums, newsletters
    - normal: Other emails
    
    Args:
        emails: List of email dictionaries from gmail_reader
        strict_mode: If True, only include emails from known shopping domains
        enable_ocr: If True, extract and analyze images with OCR
    
    Returns:
        Dictionary with categorized emails
    """
    import gc
    
    results = {
        'membership': [],
        'offer': [],
        'giftcard': [],
        'coupon': [],
        'excluded': [],
        'normal': []
    }
    
    for email in emails:
        # PRIVACY-FOCUSED: Only use subject line + sender domain
        # Body is only read when needed to verify coupon codes (not for content analysis)
        sender = email.get('sender', '')
        subject = email['subject']
        body = email.get('body', '')
        
        # PRIVACY-FOCUSED: Analyze subject + sender + body (body only for coupon code verification)
        # analyze_text internally uses categorize_from_sender for privacy
        analysis = analyze_text(subject, sender, body)
        
        # Add analysis results to email dict
        email['category'] = analysis['category']
        email['membership_matches'] = analysis['membership_matches']
        email['offer_matches'] = analysis['offer_matches']
        email['coupon_matches'] = analysis.get('coupon_matches', [])
        email['giftcard_matches'] = analysis.get('giftcard_matches', [])
        email['is_shopping_domain'] = analysis['is_shopping_domain']
        
        # Extract gift card details if category is GiftCard
        if analysis['category'] == 'GiftCard':
            email['giftcard_details'] = extract_giftcard_details(subject, body)
        
        # ENHANCED: Extract promotional content from email footer/body/subject
        footer_data = get_enhanced_email_data(body, sender, subject)
        email['footer_offers'] = footer_data['offers']
        email['footer_store_name'] = footer_data['store_name']
        
        # SMART OCR: Use OCR as fallback when subject/footer data is incomplete
        # Priority flow: 1) Subject/Footer -> 2) OCR (if data incomplete) -> 3) Store name from domain
        needs_ocr = False
        
        # Check if we have complete offer data from footer
        footer_offers = footer_data['offers']
        has_discount = bool(footer_offers.get('discount_details') or footer_offers.get('discounts'))
        has_promo = bool(footer_offers.get('promo_codes'))
        has_expiry = bool(footer_offers.get('expiry_date'))
        has_store = bool(footer_data.get('store_name'))
        
        # Check if we need OCR to supplement missing data
        # Use OCR if we're missing critical offer information OR store name
        if not has_discount or not has_promo or not has_expiry or not has_store:
            needs_ocr = True
            missing_items = []
            if not has_discount:
                missing_items.append("discount")
            if not has_promo:
                missing_items.append("promo code")
            if not has_expiry:
                missing_items.append("expiry date")
            if not has_store:
                missing_items.append("store name")
        
        # CONDITIONAL OCR: Extract from images to supplement or complete offer data
        # MEMORY LIMIT: Only process OCR if really needed to conserve memory
        if needs_ocr and enable_ocr and 'payload' in email:
            try:
                print(f"   🔍 Missing data ({', '.join(missing_items)}), using OCR...")
                image_result = get_email_images_with_ocr(email['payload'])
                image_offers = image_result.get('offers', [])
                image_stores = image_result.get('store_names', [])
                
                # Store image analysis results
                email['image_offers'] = image_offers
                email['image_stores'] = image_stores
                
                # Clear image_result to free memory
                del image_result
                gc.collect()
                
                # Re-categorize based on image content if category was Normal
                if image_offers and email['category'] == 'Normal':
                    # Check if images contain discounts/promo codes -> Coupon
                    has_discount = any(o.get('discount') or o.get('promo_code') for o in image_offers)
                    has_coupon_keywords = any(any(k in ['sale', 'clearance', 'limited time', 'free shipping'] 
                                                      for k in o.get('keywords', [])) for o in image_offers)
                    
                    if has_discount or has_coupon_keywords:
                        email['category'] = 'Coupon'
                        email['coupon_matches'] = ['[IMAGE] Promotional offer detected']
            except Exception as e:
                # Don't fail the entire analysis if image processing fails
                print(f"   ⚠ Image extraction failed for email: {e}")
                email['image_offers'] = []
                email['image_stores'] = []
        else:
            email['image_offers'] = []
            email['image_stores'] = []
        
        # MEMORY OPTIMIZATION: Remove large payload data after processing
        # Keep only essential fields for display
        if 'payload' in email:
            del email['payload']
        
        # In strict mode, only include shopping domain emails
        if strict_mode and not analysis['is_shopping_domain']:
            if analysis['category'] in ['Membership', 'Offer', 'GiftCard', 'Coupon']:
                # Demote to normal if not from shopping domain
                email['category'] = 'Normal'
                results['normal'].append(email)
                continue
        
        # Categorize
        category = analysis['category'].lower()
        if category in results:
            results[category].append(email)
    
    # Force garbage collection after processing all emails
    gc.collect()
    
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
    print(f"   • Gift Cards: {len(results.get('giftcard', []))}")
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
    
    # Gift Card emails
    if results.get('giftcard'):
        print("\n" + "-" * 60)
        print("🎁 GIFT CARDS:")
        print("   Digital gift cards, store credits, etc.")
        print("-" * 60)
        for i, email in enumerate(results['giftcard'], 1):
            shopping_badge = "🛒" if email.get('is_shopping_domain') else ""
            
            # Get store name
            footer_store = email.get('footer_store_name')
            if footer_store:
                store_name = footer_store
            else:
                store_name = extract_company_name(email['sender'], email['subject'], email.get('body', ''))
            
            # Get gift card details
            giftcard_details = email.get('giftcard_details', {})
            
            print(f"\n  {i}. {shopping_badge} {email['subject']}")
            print(f"     🏪 Store: {store_name}")
            print(f"     From: {email['sender']}")
            print(f"     Date: {email['date']}")
            
            if giftcard_details.get('card_number'):
                print(f"     💳 Card Number: {giftcard_details['card_number']}")
            if giftcard_details.get('pin'):
                print(f"     🔒 PIN: {giftcard_details['pin']}")
            if giftcard_details.get('value'):
                print(f"     💰 Value: {giftcard_details['value']}")
            if giftcard_details.get('redemption_url'):
                print(f"     🔗 Redeem: {giftcard_details['redemption_url']}")
    
    # Coupon emails (Discounts, promo codes)
    if results['coupon']:
        print("\n" + "-" * 60)
        print("🏷️  COUPON (Discounts & Promo Codes):")
        print("   Sales, cashback, free shipping, etc.")
        print("-" * 60)
        for i, email in enumerate(results['coupon'], 1):
            shopping_badge = "🛒" if email.get('is_shopping_domain') else ""
            
            # Priority for store name: Images > Footer > Email extraction
            image_stores = email.get('image_stores', [])
            footer_store = email.get('footer_store_name')
            
            if image_stores:
                store_name = image_stores[0]
            elif footer_store:
                store_name = footer_store
            else:
                store_name = extract_company_name(email['sender'], email['subject'], email.get('body', ''))
            
            print(f"\n  {i}. {shopping_badge} {email['subject']}")
            print(f"     🏪 Store: {store_name}")
            print(f"     From: {email['sender']}")
            print(f"     Date: {email['date']}")
            
            # Show footer-extracted offers
            footer_offers = email.get('footer_offers', {})
            if footer_offers:
                # Show detailed discount descriptions first (e.g., "$15 OFF YOUR ORDER OVER $75")
                if footer_offers.get('discount_details'):
                    print(f"     💰 Offer: {', '.join(footer_offers['discount_details'])}")
                elif footer_offers.get('discounts'):
                    print(f"     💰 Discounts: {', '.join(footer_offers['discounts'])}")
                
                if footer_offers.get('promo_codes'):
                    print(f"     📝 Promo Codes: {', '.join(footer_offers['promo_codes'])}")
                if footer_offers.get('free_shipping'):
                    print(f"     📦 Free Shipping Available")
                if footer_offers.get('expiry_date'):
                    print(f"     ⏰ Expires: {footer_offers['expiry_date']}")
            
            # Show image-extracted offers
            image_offers = email.get('image_offers', [])
            if image_offers and verbose:
                print(f"     🖼️  Image Offers ({len(image_offers)}):")
                for offer in image_offers[:3]:  # Show max 3
                    details = []
                    if offer.get('discount'):
                        details.append(f"Discount: {offer['discount']}")
                    if offer.get('promo_code'):
                        details.append(f"Code: {offer['promo_code']}")
                    if offer.get('expiry_date'):
                        details.append(f"Expires: {offer['expiry_date']}")
                    if offer.get('keywords'):
                        details.append(f"Keywords: {', '.join(offer['keywords'])}")
                    
                    # Show details or raw text snippet
                    if details:
                        for detail in details:
                            print(f"        • {detail}")
                    else:
                        raw_text = offer.get('raw_text', '')[:60]
                        if raw_text:
                            print(f"        • {raw_text}...")
            
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
    parser.add_argument('--no-ocr', action='store_true',
                        help='Disable OCR (OCR is enabled by default and runs only when needed)')
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
        
        # OCR is enabled by default, disabled only with --no-ocr flag
        enable_ocr = not args.no_ocr
        if enable_ocr:
            print("   (Smart OCR: Will extract from images only when domain/footer extraction fails)")
        else:
            print("   (OCR disabled)")
            
        results = analyze_emails(emails, strict_mode=args.strict, enable_ocr=enable_ocr)
        
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
