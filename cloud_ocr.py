# cloud_ocr.py - Cloud-based OCR for Serverless Environments
"""
Cloud OCR implementation using Google Cloud Vision API.
Works on serverless platforms like Vercel where Tesseract isn't available.
"""

import os
import base64
from typing import List, Dict, Optional

# Try to import Google Vision API
try:
    from google.cloud import vision
    from google.oauth2 import service_account
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False
    print("⚠️  Google Vision API not available. Install with: pip install google-cloud-vision")


def is_cloud_ocr_available() -> bool:
    """Check if cloud OCR is available and configured."""
    if not VISION_AVAILABLE:
        return False
    
    # Check if credentials are available
    google_creds = os.environ.get('GOOGLE_CREDENTIALS') or os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    return google_creds is not None


def extract_text_from_image_cloud(image_data: bytes) -> str:
    """
    Extract text from image using Google Cloud Vision API.
    
    Args:
        image_data: Raw image bytes
        
    Returns:
        Extracted text string
    """
    if not VISION_AVAILABLE:
        return ""
    
    try:
        # Initialize Vision API client
        credentials_json = os.environ.get('GOOGLE_CREDENTIALS')
        if credentials_json:
            import json
            credentials_dict = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(credentials_dict)
            client = vision.ImageAnnotatorClient(credentials=credentials)
        else:
            # Use default credentials
            client = vision.ImageAnnotatorClient()
        
        # Create image object
        image = vision.Image(content=image_data)
        
        # Perform text detection
        response = client.text_detection(image=image)
        texts = response.text_annotations
        
        if texts:
            # First annotation contains all detected text
            return texts[0].description
        
        return ""
        
    except Exception as e:
        print(f"⚠️  Cloud OCR error: {e}")
        return ""


def extract_text_from_images_cloud(images_data: List[bytes]) -> List[str]:
    """
    Extract text from multiple images using Cloud Vision API.
    
    Args:
        images_data: List of image bytes
        
    Returns:
        List of extracted text strings
    """
    if not is_cloud_ocr_available():
        return []
    
    texts = []
    for image_data in images_data:
        if len(image_data) > 0:  # Skip empty images
            text = extract_text_from_image_cloud(image_data)
            if text:
                texts.append(text)
    
    return texts


def get_ocr_provider() -> str:
    """
    Determine which OCR provider to use.
    
    Returns:
        'tesseract', 'cloud', or 'none'
    """
    import subprocess
    
    # Check if running on Vercel
    is_vercel = os.environ.get('VERCEL') == '1' or os.environ.get('VERCEL_ENV') is not None
    
    if is_vercel:
        # On Vercel, use Cloud Vision if available
        if is_cloud_ocr_available():
            return 'cloud'
        return 'none'
    
    # On other platforms (Render/local), prefer Tesseract (faster, free, local)
    try:
        import pytesseract
        # Check if tesseract binary is actually installed
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, 
                              timeout=5)
        if result.returncode == 0:
            print("✓ Using Tesseract for OCR")
            return 'tesseract'
    except (ImportError, FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Fall back to Cloud Vision if Tesseract not available
    if is_cloud_ocr_available():
        print("✓ Using Google Cloud Vision API for OCR (Tesseract not available)")
        return 'cloud'
    
    # No OCR available
    print("⚠️  No OCR provider available")
    return 'none'
