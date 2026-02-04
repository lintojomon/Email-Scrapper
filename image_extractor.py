# image_extractor.py - Email Image Extraction & OCR Module
# ========================================================
# Extracts images from emails and performs OCR to extract text

"""
Image Extractor - Download and OCR images from emails

This module handles:
- Extracting image URLs from HTML email content
- Downloading images from URLs
- Performing OCR on images to extract text (Tesseract or Cloud Vision)
- Parsing promotional offers, discounts, and expiry dates from images
"""

import re
import base64
import io
import os
import requests
from typing import List, Dict, Optional
from PIL import Image

# Try to import Tesseract (for local/Render deployments)
try:
    import pytesseract
    # Configure Tesseract path for macOS Homebrew installation
    pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("⚠️  Tesseract not available, will use Cloud Vision API if configured")

# Import cloud OCR
from cloud_ocr import extract_text_from_image_cloud, get_ocr_provider


def extract_image_urls_from_html(html_content: str) -> List[Dict[str, str]]:
    """
    Extract all image URLs from HTML content.
    
    Args:
        html_content: HTML email content
    
    Returns:
        List of dictionaries with 'src' and 'alt' keys
    """
    images = []
    
    # Find all img tags
    img_tags = re.findall(r'<img[^>]+>', html_content, re.IGNORECASE)
    
    for img_tag in img_tags:
        # Extract src
        src_match = re.search(r'src=["\']([^"\']+)["\']', img_tag, re.IGNORECASE)
        # Extract alt text
        alt_match = re.search(r'alt=["\']([^"\']+)["\']', img_tag, re.IGNORECASE)
        
        if src_match:
            src = src_match.group(1)
            alt = alt_match.group(1) if alt_match else ""
            
            # Filter out tracking pixels and small icons (likely not promotional content)
            if not any(skip in src.lower() for skip in ['open.aspx', 'tracking', 'pixel', 'spacer']):
                # Filter by alt text or filename to focus on promotional images
                if (alt and len(alt) > 3) or any(keyword in src.lower() for keyword in ['.jpg', '.png', '.jpeg', 'image', 'promo', 'offer', 'sale']):
                    images.append({
                        'src': src,
                        'alt': alt
                    })
    
    return images


def download_image(url: str, timeout: int = 10) -> Optional[Image.Image]:
    """
    Download image from URL.
    
    Args:
        url: Image URL
        timeout: Request timeout in seconds
    
    Returns:
        PIL Image object or None if download fails
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=timeout, headers=headers)
        response.raise_for_status()
        
        # Convert to PIL Image
        img = Image.open(io.BytesIO(response.content))
        return img
    
    except Exception as e:
        print(f"   ⚠ Failed to download image from {url[:50]}...: {e}")
        return None


def extract_text_from_image(image: Image.Image) -> str:
    """
    Perform OCR on image to extract text.
    Uses Tesseract (local) or Cloud Vision API (serverless) based on availability.
    
    Args:
        image: PIL Image object
    
    Returns:
        Extracted text string
    """
    try:
        # Determine OCR provider
        ocr_provider = get_ocr_provider()
        
        if ocr_provider == 'tesseract' and TESSERACT_AVAILABLE:
            # Use local Tesseract OCR
            text = pytesseract.image_to_string(image)
            return text.strip()
        
        elif ocr_provider == 'cloud':
            # Use Cloud Vision API
            # Convert PIL Image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            
            text = extract_text_from_image_cloud(img_bytes)
            return text.strip()
        
        else:
            print("   ⚠ No OCR provider available")
            return ""
    
    except Exception as e:
        print(f"   ⚠ OCR failed: {e}")
        return ""


def parse_promotional_offers(text: str) -> Dict[str, any]:
    """
    Parse promotional offers from OCR text.
    
    Args:
        text: Extracted text from image
    
    Returns:
        Dictionary with parsed offer details
    """
    offer_data = {
        'raw_text': text,
        'discount': None,
        'promo_code': None,
        'expiry_date': None,
        'keywords': []
    }
    
    # Extract discount percentages (e.g., "60% OFF", "Save 40%")
    discount_patterns = [
        r'(\d{1,2})%\s*(?:OFF|off|discount)',
        r'(?:save|Save|SAVE)\s+(\d{1,2})%',
        r'UP TO\s+(\d{1,2})%',
    ]
    for pattern in discount_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            offer_data['discount'] = f"{match.group(1)}%"
            break
    
    # Extract dollar discounts (e.g., "$20 OFF", "Save $50")
    dollar_patterns = [
        r'\$(\d+)\s*(?:OFF|off)',
        r'(?:save|Save|SAVE)\s+\$(\d+)',
    ]
    for pattern in dollar_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            offer_data['discount'] = f"${match.group(1)} OFF"
            break
    
    # Extract promo codes
    promo_patterns = [
        r'(?:code|CODE|Code)[:\s]+([A-Z0-9]{4,15})',
        r'(?:use|USE|Use)[:\s]+([A-Z0-9]{4,15})',
        r'\b([A-Z]{4,15}\d{0,4})\b(?=\s*(?:at checkout|to save))',
    ]
    for pattern in promo_patterns:
        match = re.search(pattern, text)
        if match:
            offer_data['promo_code'] = match.group(1)
            break
    
    # Extract expiry dates
    date_patterns = [
        r'(?:expires?|valid|ends?)[:\s]+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',
        r'(?:through|thru|until|till)[:\s]+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',
        r'(?:expires?|valid|ends?)[:\s]+(\d{1,2}/\d{1,2}/\d{2,4})',
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            offer_data['expiry_date'] = match.group(1)
            break
    
    # Extract keywords
    keywords = []
    keyword_list = ['free shipping', 'bogo', 'buy one get one', 'clearance', 'sale', 
                    'limited time', 'today only', 'flash sale', 'exclusive', 'member']
    for keyword in keyword_list:
        if re.search(keyword, text, re.IGNORECASE):
            keywords.append(keyword)
    
    offer_data['keywords'] = keywords
    
    return offer_data


def extract_offers_from_email_images(html_content: str, max_images: int = 10) -> List[Dict]:
    """
    Extract and parse promotional offers from email images.
    
    Args:
        html_content: HTML email content
        max_images: Maximum number of images to process
    
    Returns:
        List of dictionaries with offer details including store names
    """
    print(f"🖼️  Extracting images from email...")
    
    # Extract image URLs
    images = extract_image_urls_from_html(html_content)
    
    if not images:
        print("   No promotional images found")
        return []
    
    print(f"   Found {len(images)} potential promotional images")
    
    # Limit processing
    images = images[:max_images]
    
    offers = []
    store_names = set()
    
    for i, img_data in enumerate(images, 1):
        print(f"   Processing image {i}/{len(images)}...")
        
        # Extract store name from alt text (often has store branding)
        alt_text = img_data['alt']
        if alt_text and len(alt_text) > 3:
            # Common store name patterns in alt text
            if any(brand in alt_text.lower() for brand in ['crew', 'target', 'walmart', 'amazon', 'costco', 'sephora', 'ulta', 'kroger']):
                store_names.add(alt_text)
                print(f"      ✓ Found store in alt text: {alt_text}")
        
        # Download image
        img = download_image(img_data['src'])
        
        if img:
            # Extract text via OCR
            text = extract_text_from_image(img)
            
            # Extract store names from OCR text
            if text and len(text) > 5:
                # Common store/brand names to look for in OCR text
                store_brands = {
                    # Department Stores
                    'bloomingdale': "Bloomingdale's", 'bloomingdales': "Bloomingdale's",
                    'mingdale': "Bloomingdale's",  # OCR often garbles "Bloomingdale's"
                    'olapm': "Bloomingdale's",  # Another common OCR garble
                    'nordstrom': 'Nordstrom', 'macys': "Macy's", "macy's": "Macy's",
                    'saks': 'Saks Fifth Avenue', 'neiman': 'Neiman Marcus',
                    'dillards': "Dillard's", 'jcpenney': 'JCPenney', 'kohls': "Kohl's",
                    # Fashion
                    'j.crew': 'J.Crew', 'jcrew': 'J.Crew', 'gap': 'GAP',
                    'old navy': 'Old Navy', 'banana republic': 'Banana Republic',
                    'zara': 'ZARA', 'h&m': 'H&M', 'uniqlo': 'Uniqlo',
                    # Big Box
                    'target': 'Target', 'walmart': 'Walmart', 'costco': 'Costco',
                    'best buy': 'Best Buy', 'bestbuy': 'Best Buy',
                    # Specialty
                    'sephora': 'Sephora', 'ulta': 'Ulta Beauty',
                    'sur la table': 'Sur La Table', 'williams sonoma': 'Williams Sonoma',
                    'bed bath': 'Bed Bath & Beyond', 'pottery barn': 'Pottery Barn',
                    'crate and barrel': 'Crate and Barrel', 'crate&barrel': 'Crate and Barrel',
                    'west elm': 'West Elm', 'cb2': 'CB2',
                    'home depot': 'Home Depot', 'lowes': "Lowe's", "lowe's": "Lowe's",
                    'aveda': 'Aveda', 'anthropologie': 'Anthropologie',
                    'free people': 'Free People', 'urban outfitters': 'Urban Outfitters',
                }
                
                text_lower = text.lower()
                for brand_key, brand_name in store_brands.items():
                    if brand_key in text_lower:
                        store_names.add(brand_name)
                        print(f"      ✓ Found store in OCR: {brand_name}")
                        break  # Only match first store found
            
            # Process even short text - might have discounts or codes
            if text and len(text) > 5:
                # Parse offers
                offer = parse_promotional_offers(text)
                offer['alt_text'] = img_data['alt']
                offer['image_url'] = img_data['src']
                
                # Only add if we found something useful (discount, code, date, or keywords)
                if offer['discount'] or offer['promo_code'] or offer['expiry_date'] or offer['keywords']:
                    offers.append(offer)
                    print(f"      ✓ Found offer: {offer['discount'] or offer['promo_code'] or 'promotional content'}")
    
    # Add store names to summary
    summary = {
        'offers': offers,
        'store_names': list(store_names)
    }
    
    print(f"✓ Extracted {len(offers)} offers from images")
    if store_names:
        print(f"✓ Detected stores: {', '.join(store_names)}")
    
    return summary


def get_email_images_with_ocr(payload: Dict) -> Dict:
    """
    Extract images from email payload and perform OCR.
    
    Args:
        payload: Gmail message payload
    
    Returns:
        Dictionary with 'offers' (list) and 'store_names' (list)
    """
    # Extract HTML content
    html_content = ""
    parts = payload.get('parts', [])
    
    if parts:
        for part in parts:
            if part.get('mimeType') == 'text/html':
                data = part.get('body', {}).get('data', '')
                if data:
                    html_content = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    break
    else:
        # Single part HTML
        if payload.get('mimeType') == 'text/html':
            data = payload.get('body', {}).get('data', '')
            if data:
                html_content = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    
    if not html_content:
        return {'offers': [], 'store_names': []}
    
    # Extract and process images
    return extract_offers_from_email_images(html_content)
