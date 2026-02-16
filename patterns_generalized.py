# patterns_generalized.py - Generalized Pattern Detection
# ========================================================
# Universal patterns that work for ANY store/card/membership in USA
# without relying on hardcoded lists

"""
Generalized Regex patterns for detecting:
- Memberships/subscriptions from ANY service
- Credit card offers from ANY bank/issuer  
- Coupons/discounts from ANY store

Works by detecting language patterns rather than specific brand names.
"""

import re
from typing import Tuple, List, Dict

# ============================================
# GENERALIZED MEMBERSHIP PATTERNS
# Detects subscription language for ANY service
# ============================================
MEMBERSHIP_PATTERNS = [
    # PRIORITY: Strong membership indicators with tier names
    # Pattern: "StoreName TierName:" (Kroger Boost+:, Beauty Insider:, Ultamate Rewards:, myWalgreens+:, etc.)
    # Handles both "Kroger Boost+:" (with space) and "myWalgreens+:" (no space)
    r'\b[\w\s\']+[\s]?(club\+|boost\+|plus\+|\+|premium|pro|rewards|insider|member|circle|perks|benefits|advantage|privileges):\s',
    r'\b(club\+|boost\+|rewards|insider)\s+members?\b',  # "Rewards member", "Insider member"
    
    # ANNIVERSARY/BIRTHDAY patterns (membership milestones)
    r'\b(membership|member|subscriber|account)\s+(anniversary|birthday)\b',
    r'\b(anniversary|birthday)\b.*\b(membership|member|rewards|program|account|passport|insider|perks)\b',
    r'\byour\s+[\w\s\+\-\'\.]+\s+anniversary\b',  # "Your J.Crew Passport anniversary", "Your anniversary"
    r'\banniversary\b',  # Standalone anniversary (often membership-related)
    r'\bhappy\s+birthday\b',  # Birthday emails often membership perks
    r'\bcelebrating\s+(your|you)\b',  # Common in anniversary/birthday emails
    
    # Very broad core membership/subscription terms
    r'\bmembership\b',  # Any mention of membership
    r'\bsubscription\b',  # Any mention of subscription
    r'\bmember\s+(benefits|perks|rewards|exclusive|since|portal|access|account|card|number|id)\b',
    r'\byour\s+[\w\s\+\-\']+\s+(membership|subscription|member|account)\b',
    r'\bwelcome\s+to\s+[\w\s\+\-\']+[!\s,]',  # Welcome emails are often memberships
    
    # Membership status/expiry patterns (Sam's Club, Costco, etc.)
    r'\b(membership|subscription)\s+(?:ending|expir(?:es?|ing)|renew(?:al|ing)?)\b',  # "Membership ending/expiring/renewal"
    r'\b(membership|subscription)\s+(?:status|details|information|summary)\b',  # "Membership status/details"
    
    # Activation/start language
    r'\b(activated|active|confirmed|enrolled|registered|started|begins?)\b.*\b(membership|subscription|member|account)\b',
    r'\b(membership|subscription|member|account)\b.*\b(activated|active|confirmed|enrolled|started|is\s+now|has\s+started)\b',
    
    # Warehouse/club specific
    r'\b(warehouse|club|plus|prime)\s+(membership|member|account)\b',
    r'\b(member|membership)\s+(card|number|id|portal|dashboard)\b',
    
    # Trial/renewal terms
    r'\b(trial|renewal|renew)\b.*\b(started|begins?|ends?|expir(es?|ing|ation)|period|notice|reminder)\b',
    r'\bfree\s*(trial|membership|subscription)\b',
    r'\bauto[-\s]?renew(al|ed|s)?\b',
    
    # Billing/payment terms (subscription-related)
    r'\b(monthly|annual|yearly)\s*(plan|subscription|membership|fee|payment|billing)\b',
    r'\brecurring\s*(charge|payment|billing|subscription|fee)\b',
    r'\bsubscription\s*(fee|dues|payment|invoice|billing|charge)\b',
    r'\bmembership\s*(fee|dues|payment|invoice|billing|charge)\b',
    
    # Tier/level terms (very common in memberships)
    r'\b(plus|premium|pro|elite|gold|platinum|executive|star|select|preferred|priority|boost)\s+(membership|subscription|member|account|program)\b',
    r'\b(basic|standard|advanced|essentials?)\s+(membership|subscription|member|plan|tier)\b',
    # Club/Boost names with tier suffixes (e.g., "BJ's Club+", "Kroger Boost+")
    r'\b[\w\']+\s*(club\+|boost\+)\b',  # Matches "BJ's Club+", "Kroger Boost+", etc.
    r'\b(club\+|boost\+|club\s+plus|boost\s+plus)\b',  # Explicit Club+/Boost+ or Club Plus/Boost Plus
    
    # Access/benefits terms
    r'\b(unlock|unlocked|enjoy|access|get)\b.*\b(membership|subscription|member|benefits|perks|privileges)\b',
    r'\b(membership|subscription)\b.*\b(unlock|unlocked|benefits|perks|privileges|exclusive|rewards)\b',
    r'\bjoin(ed)?\s+(our\s+)?[\w\s\+\-\']+\s+(membership|program|club|family|community)\b',
    r'\bexclusive\s*(member|membership|subscriber)\s*(access|benefits|perks|pricing|offers?|deals?)\b',
    
    # Service-specific but broad
    r'\b(streaming|delivery|shipping|rewards?|loyalty|points)\s*(membership|subscription|service|program|plan)\b',
    r'\b(gym|fitness|health|wellness)\s*(membership|subscription|plan)\b',
    r'\b(student|family|business|corporate|individual)\s*(membership|subscription|plan)\b',
    
    # Welcome/confirmation phrases (very common in membership emails)
    r'\bwelcome\s+(to\s+)?(our\s+)?[\w\s\+\-\']+\b',
    r'\bthank\s+you\s+for\s+(joining|subscribing|signing\s+up)\b',
    r'\byou\'?re\s+(now\s+)?a\s+(member|subscriber)\b',
    r'\byour\s+[\w\s\+\-\']+\s+(account|profile)\s+is\s+(ready|active|set\s+up)\b',
    
    # Numbers/IDs associated with memberships
    r'\bmember(ship)?\s*(number|id|#)\s*:?\s*\d+\b',
    r'\baccount\s*(number|id|#)\s*:?\s*\d+\b.*\b(membership|subscription|member)\b',
]

# ============================================
# GENERALIZED CREDIT CARD PATTERNS
# Detects card language for ANY issuer/bank
# ============================================
OFFER_PATTERNS = [
    # Core card terms
    r'\b(credit|debit|charge|prepaid)\s*card\s*(benefits|rewards|activated|active|approved|application|member)\b',
    r'\bcard\s*(benefits|rewards|activated|active|approved|application|member|perks|privilege)\b',
    r'\byour\s+[\w\s]+\s+card\s+(is\s+)?(now\s+)?(ready|active|activated|approved|issued)\b',
    
    # Welcome messages with card
    r'\bwelcome[!\s]+.*\bcard\b',  # "Welcome! Your ... Card"
    r'\byour\s+[\w\s®]+\s+card\b',  # "Your Chase Freedom Unlimited® Card"
    r'\bcongratulations\b.*\bcard\b',  # "Congratulations on your ... card"
    r'\bcongratulations\b.*\b(approval|approved)\b',  # "Congratulations on your approval"
    
    # Card networks
    r'\b(visa|mastercard|american\s*express|amex|discover|diners|jcb|unionpay)\s*(card|benefits|rewards|signature|infinite|world|elite)?\b',
    
    # Card member terms
    r'\bcard\s*member\s*(benefits|rewards|exclusive|perks|offers|privileges)\b',
    r'\bcardmember\b',
    r'\bcard\s*holder\b',
    
    # Rewards/points terms
    r'\brewards?\s*(card|program|points|activated|active|benefits|earned|balance)\b',
    r'\bpoints\s*(earned|balance|card|rewards|program|redemption|transfer)\b',
    r'\bcash\s*back\s*(card|rewards|earned|program)?\b',
    r'\bmiles\s*(card|rewards|earned|program|balance|transfer)\b',
    r'\bfrequent\s*flyer\s*(card|program|miles)\b',
    r'\bairline\s*(miles|rewards|card|partner)\b',
    r'\btravel\s*(card|rewards|benefits|credits)\b',
    
    # Welcome/activation
    r'\bwelcome\s*(bonus|offer|kit|package)\b.*\bcard\b',
    r'\bcard\s*(application|approval|activation|welcome)\b',
    r'\bapproved\b.*\bcard\b',
    r'\bactivate\s+your\s+(new\s+)?card\b',
    
    # Card tiers
    r'\b(platinum|gold|silver|premier|signature|infinite|world|elite|prestige|reserve)\s*(card|membership|status)\b',
    r'\b(business|corporate|commercial)\s*card\b',
    r'\bco[-\s]?brand(ed)?\s*card\b',
    r'\bstore\s*card\b',
    
    # Benefits
    r'\bcard\s+benefit(s)?\s+(are\s+)?(now\s+)?(active|activated|available|unlocked)\b',
    r'\binsurance\s*coverage\b.*\bcard\b',
    r'\btravel\s*insurance\b',
    r'\bpurchase\s*protection\b',
    r'\bextended\s*warranty\b',
    r'\bconcierge\s*service\b',
    r'\blounge\s*access\b',
    r'\bpriority\s*(pass|boarding|access)\b',
]

# ============================================
# GENERALIZED COUPON/DISCOUNT PATTERNS
# Detects deals/sales language for ANY store
# ============================================
COUPON_PATTERNS = [
    # Percentage discounts
    r'\b\d+%\s*off\b',
    r'\bup\s*to\s*\d+%\s*off\b',
    r'\bflat\s*\d+%?\s*(off|discount)\b',
    r'\bextra\s*\d+%\s*off\b',
    r'\badditional\s*\d+%\s*off\b',
    
    # Dollar/currency discounts
    r'\bsave\s*(up\s*to\s*)?\$?\₹?€?£?¥?\d+',
    r'\bget\s*\$?\₹?€?£?¥?\d+\s*off\b',
    r'\b\$?\₹?€?£?¥?\d+\s*off\b',
    r'\b\$?\₹?€?£?¥?\d+\s*(discount|savings|rebate)\b',
    
    # Promo/coupon codes
    r'\bpromo\s*(code|offer)\b',
    r'\bcoupon\s*code\b',
    r'\bdiscount\s*code\b',
    r'\buse\s*code\b',
    r'\bapply\s*code\b',
    r'\benter\s*code\b',
    r'\bcode\s*:\s*[\w\d]+',
    r'\bredeem\s*(code|coupon|offer|points)\b',
    r'\bvoucher\s*code\b',
    
    # Free offers
    r'\bfree\s*(shipping|delivery|gift|sample|trial|returns?|item|product)\b',
    r'\bcomplimentary\s*(shipping|gift|upgrade)\b',
    r'\bno\s*(shipping|delivery)\s*(fee|cost|charge)\b',
    
    # BOGO/Multi-buy
    r'\bbuy\s*\d+\s*get\s*\d+\b',
    r'\bbogo\b',
    r'\bbuy\s*one\s*get\s*one\b',
    r'\b\d+\s*for\s*\$?\₹?€?£?\d+\b',
    
    # Sales
    r'\bsale\s*(now|today|ends|starts?|event|online)\b',
    r'\bflash\s*sale\b',
    r'\bclearance\s*sale\b',
    r'\bliquidation\s*sale\b',
    r'\bwarehouse\s*sale\b',
    r'\bgarage\s*sale\b',
    r'\bblowout\s*sale\b',
    r'\bseasonal\s*sale\b',
    r'\bend\s*of\s*season\s*sale\b',
    r'\bpre[-\s]?season\s*sale\b',
    r'\bmid[-\s]?season\s*sale\b',
    
    # Time-sensitive
    r'\blimited\s*time\s*(offer|deal|sale|only|discount)\b',
    r'\btoday\s*only\b',
    r'\bweekend\s*(sale|offer|deal|special)\b',
    r'\b(24|48|72)\s*hour(s)?\s*(sale|flash|deal)\b',
    r'\bends?\s*(today|tonight|tomorrow|soon|this\s+week|in\s*\d+)\b',
    r'\bhurry!?\s*(limited|offer|ends|stock|time)\b',
    r'\blast\s*chance\b',
    r'\bfinal\s*(hours?|days?|call)\b',
    r'\bdon\'?t\s*miss\s*(this|out|it)\b',
    r'\bwhile\s*(supplies|stocks?)\s*last\b',
    r'\bact\s*now\b',
    r'\bexpir(es?|ing|ation)\s*(soon|today|tomorrow)\b',
    
    # Exclusive/special
    r'\bexclusive\s*(offer|deal|discount|sale|access|price|savings)\b',
    r'\bspecial\s*(offer|deal|discount|price|promotion|savings)\b',
    r'\bmember\s*(exclusive|only|special|pricing|discount)\b',
    r'\bvip\s*(offer|sale|discount|access|pricing)\b',
    r'\bearly\s*(access|bird|shopper)\b',
    r'\bprivate\s*sale\b',
    r'\binvite[-\s]?only\b',
    
    # Holiday/seasonal
    r'\bblack\s*friday\b',
    r'\bcyber\s*monday\b',
    r'\bprime\s*day\b',
    r'\bholiday\s*(sale|offer|deal|savings|event)\b',
    r'\bchristmas\s*(sale|offer|deals?)\b',
    r'\bnew\s*year\s*(sale|offer|deals?)\b',
    r'\bvalentine\'?s?\s*(sale|deals?)\b',
    r'\bmother\'?s?\s*day\s*(sale|deals?)\b',
    r'\bfather\'?s?\s*day\s*(sale|deals?)\b',
    r'\bmemorial\s*day\s*(sale|deals?)\b',
    r'\blabor\s*day\s*(sale|deals?)\b',
    r'\bback\s*to\s*school\b',
    r'\bsummer\s*(sale|savings|clearance)\b',
    r'\bwinter\s*(sale|savings|clearance)\b',
    r'\bspring\s*(sale|savings)\b',
    r'\bfall\s*(sale|savings)\b',
    
    # Rewards/cashback
    r'\bcashback\b',
    r'\bcash\s*back\b',
    r'\brewards?\s*(points|dollars|earnings)\b',
    r'\bearn\s*\d+[x%]?\s*(points|rewards|cashback)\b',
    r'\bdouble\s*(points|rewards|cashback)\b',
    r'\btriple\s*(points|rewards)\b',
    
    # Call to action (deal-related)
    r'\bshop\s*now\s*(and|to|&)?\s*(save|get)\b',
    r'\border\s*now\s*(and|to|&)?\s*(get|save)\b',
    r'\bbuy\s*now\s*(and|to|&)?\s*(save|get)\b',
    r'\bclick\s*(here|now)\s*to\s*save\b',
    r'\bsave\s*(big|more|today|now)\b',
    r'\bhuge\s*(savings|discounts?)\b',
    r'\bmassive\s*(savings|discounts?|sale)\b',
    r'\bunbeatable\s*(price|deal|offer)\b',
    r'\blowest\s*price\b',
    r'\bbest\s*(price|deal|offer)\b',
    r'\bprice\s*drop\b',
    r'\bmark(ed)?\s*down\b',
]

# ============================================
# GIFT CARD PATTERNS
# Detects gift card emails
# ============================================
GIFTCARD_PATTERNS = [
    # Gift card terms
    r'\bgift\s*card\b',
    r'\be[-\s]?gift\s*card\b',
    r'\bgift\s*certificate\b',
    r'\bdigital\s*gift\s*card\b',
    r'\bvirtual\s*gift\s*card\b',
    r'\belectronic\s*gift\s*card\b',
    
    # Gift card actions
    r'\bgift\s*card\s*(sent|delivered|received|ready|activated)\b',
    r'\breceived\s*a\s*gift\s*card\b',
    r'\byour\s*gift\s*card\b',
    r'\bredeem\s*(your\s*)?gift\s*card\b',
    r'\bclaim\s*(your\s*)?gift\s*card\b',
    
    # Gift card numbers/PIN
    r'\bcard\s*number\s*:?\s*[\d\s-]+\b',
    r'\bpin\s*:?\s*\d+\b',
    r'\bcard\s*value\s*:?\s*[$₹€£¥]?\d+',
    r'\bgift\s*card\s*balance\b',
    r'\bgift\s*card\s*code\b',
    
    # Store credit (gift card related)
    r'\bstore\s*credit\b',
    r'\baccount\s*credit\b',
]

# ============================================
# ORDER CONFIRMATION PATTERNS
# Detects order/shipping/delivery related emails
# ============================================
ORDER_PATTERNS = [
    # Order confirmation
    r'\border\s+(confirmation|confirmed|received|placed)\b',
    r'\bwe\s+(received|got)\s+(your\s+)?order\b',
    r'\byour\s+order\s+(has\s+been|is|was)\s+(received|confirmed|placed|processing)\b',
    r'\bthank\s+you\s+for\s+(your\s+)?order\b',
    r'\border\s+(number|#|id)\s*:?\s*[A-Z0-9-]+\b',
    
    # Shipping/delivery
    r'\b(shipped|shipping|delivery|delivered|dispatched)\s+(confirmation|notification|update|status)\b',
    r'\byour\s+(order|package|item)\s+(has\s+)?(shipped|been\s+shipped|is\s+on\s+the\s+way)\b',
    r'\btracking\s+(number|#|id|information|details)\b',
    r'\bdelivery\s+(date|time|estimate|scheduled)\b',
    r'\bout\s+for\s+delivery\b',
    
    # Order status
    r'\border\s+status\b',
    r'\bprocessing\s+your\s+order\b',
    r'\bpreparing\s+(your\s+)?(order|shipment)\b',
]

# Compile for performance
MEMBERSHIP_REGEX = re.compile('|'.join(MEMBERSHIP_PATTERNS), re.IGNORECASE)
OFFER_REGEX = re.compile('|'.join(OFFER_PATTERNS), re.IGNORECASE)
COUPON_REGEX = re.compile('|'.join(COUPON_PATTERNS), re.IGNORECASE)
GIFTCARD_REGEX = re.compile('|'.join(GIFTCARD_PATTERNS), re.IGNORECASE)
ORDER_REGEX = re.compile('|'.join(ORDER_PATTERNS), re.IGNORECASE)


def is_commercial_domain(sender: str) -> bool:
    """
    Detect if email is from a SHOPPING/RETAIL domain only.
    Strict filtering to avoid false positives from random company domains.
    PRIVACY-FOCUSED: Analyzes only sender domain, not email content.
    """
    if not sender or '@' not in sender:
        return False
    
    try:
        # Extract domain
        email_part = sender.split('<')[-1].split('>')[0].strip()
        domain = email_part.split('@')[1].lower()
        base_domain = '.'.join(domain.split('.')[-2:])  # Get main domain
        
        # Exclude personal email providers
        personal_domains = [
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 
            'aol.com', 'icloud.com', 'mail.com', 'protonmail.com',
            'live.com', 'msn.com', 'yandex.com', 'zoho.com',
            'inbox.com', 'gmx.com', 'fastmail.com'
        ]
        if base_domain in personal_domains:
            return False
        
        # Special case: innovinlabs.com is forwarding service for shopping emails
        # Not marked as shopping domain (handled separately in strict mode logic)
        if 'innovinlabs.com' in domain:
            return False
        
        # Exclude social/tech/forum platforms
        excluded_platforms = [
            'reddit.com', 'twitter.com', 'x.com', 'facebook.com', 'instagram.com',
            'linkedin.com', 'github.com', 'gitlab.com', 'slack.com', 'discord.com',
            'telegram.org', 'whatsapp.com', 'quora.com', 'medium.com', 'substack.com',
            'stackoverflow.com', 'meetup.com', 'eventbrite.com',
            # Dev platforms and tech product newsletters
            'replit.com', 'vercel.com', 'netlify.com', 'heroku.com', 'digitalocean.com',
            'aws.amazon.com', 'cloud.google.com', 'azure.microsoft.com',
            'notion.so', 'figma.com', 'canva.com', 'airtable.com', 'trello.com',
            'asana.com', 'monday.com', 'atlassian.com', 'jira.com', 'confluence.com'
        ]
        if any(ex in domain for ex in excluded_platforms):
            return False
        
        # Known major shopping/retail brands (whitelist approach)
        known_shopping_domains = [
            'amazon.com', 'ebay.com', 'walmart.com', 'target.com', 'bestbuy.com',
            'costco.com', 'macys.com', 'nordstrom.com', 'nordstromrack.com', 'kohls.com', 'jcpenney.com',
            'homedepot.com', 'lowes.com', 'wayfair.com', 'overstock.com', 'etsy.com',
            'zappos.com', 'sephora.com', 'ulta.com', 'nike.com', 'adidas.com',
            'gap.com', 'oldnavy.com', 'bananarepublic.com', 'athleta.com',
            'victoriassecret.com', 'bathandbodyworks.com', 'bedbathandbeyond.com',
            'crateandbarrel.com', 'potterybarn.com', 'westelm.com', 'ikea.com',
            'staples.com', 'officedepot.com', 'petco.com', 'petsmart.com',
            'chewy.com', 'wholefoodsmarket.com', 'kroger.com', 'safeway.com',
            'albertsons.com', 'ralphs.com', 'instacart.com', 'shipt.com',
            'shopify.com', 'square.com', 'stripe.com', 'paypal.com',
            'rei.com', 'dickssportinggoods.com', 'samsclub.com', 'bjs.com',
            'traderjoes.com', 'aldi.us', 'lidl.com', 'tjmaxx.com', 'marshalls.com',
            'homegoods.com', 'ross.com', 'burlington.com', 'dsw.com', 'footlocker.com',
            'fanatics.com', 'nfl.com', 'nba.com', 'mlb.com', 'underarmour.com',
            'lululemon.com', 'patagonia.com', 'northface.com', 'columbia.com',
            'anthropologie.com', 'urbanoutfitters.com', 'freepeople.com',
            'forever21.com', 'hm.com', 'zara.com', 'uniqlo.com', 'guess.com',
            'ralphlauren.com', 'calvinklein.com', 'tommy.com', 'express.com',
            'ae.com', 'abercrombie.com', 'hollisterco.com', 'aeropostale.com',
            'williams-sonoma.com', 'surlatable.com', 'chefswarehouse.com',
            'autozone.com', 'advanceautoparts.com', 'oreilly.com', 'pepboys.com',
            'gamestop.com', 'barnesandnoble.com', 'michaels.com', 'joann.com',
            'hobbylobby.com', 'acmoore.com', 'partycity.com', 'spirithalloween.com',
            'build.com', 'houzz.com', 'roomstogo.com', 'ashleyfurniture.com',
            'bobs.com', 'valuecityfurniture.com', 'americansignaturefurniture.com',
            'pier1.com', 'kirklands.com', 'worldmarket.com', 'atgstores.com'
        ]
        
        # Check if it's a known shopping domain
        if any(known in domain for known in known_shopping_domains):
            return True
        
        # STRICT shopping/retail indicators - must have these keywords
        # Only mark as shopping if domain contains these RETAIL-SPECIFIC terms
        shopping_indicators = [
            'shop', 'store', 'retail', 'market', 'mall', 'outlet',
            'ecom', 'commerce', 'cart', 'deals', 'sale'
        ]
        
        # Must have shopping indicator AND be .com/.shop/.store to qualify
        has_shopping_keyword = any(indicator in domain for indicator in shopping_indicators)
        is_commerce_tld = domain.endswith(('.com', '.shop', '.store', '.biz'))
        
        if has_shopping_keyword and is_commerce_tld:
            return True
        
        # Explicit shopping TLDs
        if domain.endswith(('.shop', '.store')):
            return True
        
        # Gift card provider domains
        giftcard_providers = [
            'freecash.com', 'yougov.com', 'swagbucks.com', 'mypoints.com',
            'inboxdollars.com', 'prizerebel.com', 'grabpoints.com',
            'giftcardgranny.com', 'raise.com', 'cardcash.com', 'cardpool.com',
            'giftcards.com', 'egifter.com', 'gyft.com'
        ]
        if any(provider in domain for provider in giftcard_providers):
            return True
        
        # If none of the above, it's NOT a shopping domain
        return False
        
    except:
        return False


def categorize_from_sender(sender: str) -> str:
    """
    Categorize email based ONLY on sender domain.
    PRIVACY-FIRST: No email content reading required.
    
    Returns: 'membership', 'offer', 'coupon', or 'unknown'
    """
    if not sender:
        return 'unknown'
    
    try:
        # Extract domain and email parts
        email_part = sender.split('<')[-1].split('>')[0].strip().lower()
        name_part = sender.split('<')[0].strip().lower() if '<' in sender else ''
        domain = email_part.split('@')[1] if '@' in email_part else ''
        
        # Check for credit card/banking keywords in sender
        card_keywords = ['card', 'amex', 'chase', 'citi', 'capital', 'discover', 
                        'visa', 'mastercard', 'bank', 'credit', 'rewards']
        if any(keyword in domain or keyword in name_part for keyword in card_keywords):
            return 'offer'
        
        # Check for membership keywords in sender (enhanced with insider, rewards)
        membership_keywords = ['member', 'subscription', 'prime', 'plus', 'premium',
                              'club', 'boost', 'vip', 'elite', 'loyalty', 'insider', 'rewards']
        if any(keyword in domain or keyword in name_part for keyword in membership_keywords):
            return 'membership'
        
        # Check for retail/shopping keywords
        retail_keywords = ['shop', 'store', 'retail', 'deals', 'offers', 'promo',
                          'sale', 'discount', 'coupon', 'market', 'mall']
        if any(keyword in domain or keyword in name_part for keyword in retail_keywords):
            return 'coupon'
        
        return 'unknown'
        
    except:
        return 'unknown'


def is_membership(text: str) -> bool:
    """Check if text contains membership/subscription language."""
    if not text:
        return False
    return bool(MEMBERSHIP_REGEX.search(text))


def is_offer(text: str) -> bool:
    """Check if text contains credit card offer language."""
    if not text:
        return False
    return bool(OFFER_REGEX.search(text))


def is_coupon(text: str) -> bool:
    """Check if text contains coupon/discount language."""
    if not text:
        return False
    return bool(COUPON_REGEX.search(text))


def is_order_related(text: str) -> bool:
    """Check if text contains order/shipping confirmation language."""
    if not text:
        return False
    return bool(ORDER_REGEX.search(text))


def is_giftcard(text: str) -> bool:
    """Check if text contains gift card language."""
    if not text:
        return False
    return bool(GIFTCARD_REGEX.search(text))


def analyze_text(text: str, sender: str = "", body: str = "") -> Dict:
    """
    Analyze email to categorize - PRIVACY-FOCUSED approach.
    Priority: 1) Sender domain, 2) Subject line patterns, 3) Body verification (only when needed)
    
    Args:
        text: Email subject (preferred) 
        sender: Email sender address
        body: Email body (optional, only used to verify coupon codes)
    
    Returns:
        Dict with category and analysis results
    """
    # STEP 1: Try to categorize from sender alone (most private)
    sender_category = categorize_from_sender(sender)
    
    # Check if sender is from a known gift card provider domain
    giftcard_provider_pattern = r'[a-zA-Z0-9._%+-]+@(?:freecash\.com|yougov\.com|surveyjunkie\.com|swagbucks\.com|inboxdollars\.com|prolific\.com|pineconeresearch\.com|surveynetwork\.com|mypoints\.com|usertesting\.com|fetch\.com|ibotta\.com|receipthog\.com|receiptpal\.com|coinout\.com|getmiles\.com|upside\.com|aarp\.org|aaa\.com|raise\.com|cardcash\.com)'
    is_giftcard_provider = bool(re.match(giftcard_provider_pattern, sender, re.IGNORECASE)) if sender else False
    
    # STEP 2: Analyze text patterns (subject line preferred)
    membership_found = is_membership(text)
    offer_found = is_offer(text)
    coupon_found = is_coupon(text)
    giftcard_found = is_giftcard(text)
    commercial = is_commercial_domain(sender)
    
    # Check if this is a promotional/sale email
    # Common sale patterns that indicate promotional content, not actual gift cards
    sale_keywords = r'\b(sale|clearance|promotion|promotional|flash\s*sale|half\s*yearly|end\s*of\s*season|seasonal\s*sale|warehouse\s*sale|up\s*to\s+\d+%\s*off|\d+%\s*off|\d+%[-\s]*\d+%\s*off)\b'
    is_promotional_sale = bool(re.search(sale_keywords, text, re.IGNORECASE))
    
    # Also check body for promotional patterns if available
    if not is_promotional_sale and body:
        is_promotional_sale = bool(re.search(sale_keywords, body, re.IGNORECASE))
    
    # STEP 2b: If not found in subject, check body for membership/giftcard patterns
    # (These are important enough to check body when subject doesn't reveal them)
    if not membership_found and body:
        membership_found = is_membership(body)
    if not giftcard_found and body:
        giftcard_found = is_giftcard(body)
        # If gift card mentioned in body but subject has strong promotional indicators, likely not a gift card email
        if giftcard_found and is_promotional_sale:
            # Check if body mentions gift cards as purchase options (not as the main purpose)
            gift_card_option_pattern = r'\b(buy|purchase|shop for|give|send)\s+(?:a\s+)?gift\s*card'
            if re.search(gift_card_option_pattern, body, re.IGNORECASE):
                # This is a promotional email that mentions gift cards as an option, not a gift card email
                giftcard_found = False
    
    # STEP 2c: Check if email is order/shipping related (should be Normal, not Coupon)
    is_order = is_order_related(text)
    if not is_order and body:
        is_order = is_order_related(body)
    
    # STEP 3: Verify coupon classification - check if actual coupon code exists
    # If both membership and coupon patterns match, check body for coupon code
    if coupon_found and (membership_found or 'rewards' in text.lower() or 'points' in text.lower()):
        # Check if email body has an actual coupon code
        if body:
            code_patterns = [
                r'(?:Coupon\s*Code|Promo\s*Code|Code|Use\s*Code|Discount\s*Code|Offer\s*Code)\s*[:\s]+([A-Z0-9]{4,20})',
                r'(?:Apply|Enter|Use)\s+(?:code\s+)?["\']?([A-Z0-9]{4,20})["\']?',
            ]
            has_coupon_code = False
            for pattern in code_patterns:
                if re.search(pattern, body, re.IGNORECASE):
                    has_coupon_code = True
                    break
            
            # If no coupon code found, it's likely a membership benefit, not a coupon
            if not has_coupon_code:
                coupon_found = False
    
    # STEP 4: Determine final category
    # Priority: Order confirmations > Gift cards > Coupons with promo codes > Membership > Offer > Normal
    # Order-related emails should always be Normal, not Coupon
    
    # Check if body has actual promo codes or discount details (stronger signal than patterns)
    has_promo_content = False
    if body:
        # Check for alphanumeric promo codes (e.g., "FREE26JAN", "SAVE20")
        promo_code_pattern = r'\b([A-Z]+\d+[A-Z0-9]*|[0-9]+[A-Z]+[A-Z0-9]*)\b'
        promo_codes = re.findall(promo_code_pattern, body)
        # Check for discount patterns
        discount_pattern = r'\b\d{1,2}%\s+off|\$\d+\s+off'
        has_discount = re.search(discount_pattern, body, re.IGNORECASE)
        
        if (promo_codes and len(promo_codes) > 0) or has_discount:
            has_promo_content = True
    
    # Categorize based on priority
    # Priority: Order > Gift Card Provider Domain > Gift Card (not promotional) > Coupon > Membership > Offer > Normal
    if is_order:
        # Order confirmations/shipping notifications are always Normal
        category = "Normal"
    elif is_giftcard_provider:
        # Emails from known gift card provider domains (freecash, yougov, swagbucks, etc.)
        category = "GiftCard"
    elif giftcard_found and not is_promotional_sale:
        # Only categorize as GiftCard if NOT a promotional sale
        # This prevents "Nordstrom Half Yearly Sale" from being GiftCard just because it mentions gift cards
        category = "GiftCard"
    elif has_promo_content or coupon_found:
        # If email has actual promotional content, it's a coupon regardless of sender
        category = "Coupon"
    elif sender_category == 'membership' or membership_found:
        category = "Membership"
    elif sender_category == 'offer' or offer_found:
        category = "Offer"
    else:
        category = "Normal"
    
    return {
        'category': category,
        'membership_matches': MEMBERSHIP_REGEX.findall(text)[:5] if membership_found else [],
        'offer_matches': OFFER_REGEX.findall(text)[:5] if offer_found else [],
        'coupon_matches': COUPON_REGEX.findall(text)[:5] if coupon_found else [],
        'giftcard_matches': GIFTCARD_REGEX.findall(text)[:5] if giftcard_found else [],
        'is_shopping_domain': commercial
    }


def categorize_email(text: str, sender: str = "") -> Tuple[str, List[str]]:
    """Categorize email and return category with matched keywords."""
    result = analyze_text(text, sender)
    
    if result['category'] == "GiftCard":
        return ("GiftCard", result['giftcard_matches'])
    elif result['category'] == "Membership":
        return ("Membership", result['membership_matches'])
    elif result['category'] == "Offer":
        return ("Offer", result['offer_matches'])
    elif result['category'] == "Coupon":
        return ("Coupon", result['coupon_matches'])
    else:
        return ("Normal", [])
