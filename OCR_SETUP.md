# Image OCR Setup Instructions

## What Was Added

The email scraper can now extract text from images in promotional emails using OCR (Optical Character Recognition). This allows the scraper to read:
- Discount percentages (e.g., "60% OFF")
- Promo codes (e.g., "SAVE20")
- Expiry dates
- Other promotional content embedded in images

## Installation Required

### Install Tesseract OCR Engine

Tesseract is the OCR engine that reads text from images. You need to install it:

#### On macOS (with Homebrew):
```bash
brew install tesseract
```

If you don't have Homebrew, install it first:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### On macOS (without Homebrew):
Download the installer from: https://github.com/UB-Mannheim/tesseract/wiki

#### On Linux (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

### Verify Installation

After installing, verify Tesseract is working:
```bash
tesseract --version
```

You should see output like: `tesseract 5.x.x`

## Usage

### Test Image Extraction

Run this to test image extraction on the latest email:
```bash
python3 -c "
import sys
sys.path.append('.')
from auth import get_gmail_service
from image_extractor import get_email_images_with_ocr

service = get_gmail_service()
results = service.users().messages().list(userId='me', maxResults=1).execute()
messages = results.get('messages', [])

if messages:
    msg_id = messages[0]['id']
    message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    offers = get_email_images_with_ocr(message.get('payload', {}))
    
    print(f'\nFound {len(offers)} promotional offers:')
    for i, offer in enumerate(offers, 1):
        print(f'\nOffer {i}:')
        if offer.get('discount'):
            print(f'  Discount: {offer[\"discount\"]}')
        if offer.get('promo_code'):
            print(f'  Code: {offer[\"promo_code\"]}')
        if offer.get('expiry_date'):
            print(f'  Expires: {offer[\"expiry_date\"]}')
"
```

## Features

### What the Image Extractor Does:

1. **Finds Images**: Extracts all image URLs from HTML emails
2. **Downloads**: Fetches images from URLs
3. **OCR Processing**: Extracts text using Tesseract
4. **Smart Parsing**: Identifies:
   - Discount amounts (60% OFF, $20 OFF)
   - Promo codes (SAVE20, NEWYEAR25)
   - Expiry dates (various formats)
   - Keywords (free shipping, BOGO, sale, etc.)

### Filters Applied:

- Skips tracking pixels and small icons
- Only processes images likely to contain promotional content
- Requires minimum text length (10 characters) from OCR
- Only saves offers with actual discount/code/date data

### Configuration:

In `image_extractor.py`, you can adjust:
- `max_images`: Limit number of images to process (default: 10)
- Filtering keywords in `extract_image_urls_from_html()`
- Parsing patterns in `parse_promotional_offers()`

## Integration

The image extractor is a standalone module. To integrate it into your main analyzer:

```python
from image_extractor import get_email_images_with_ocr

# In your email processing loop:
offers = get_email_images_with_ocr(message_payload)
```

## Troubleshooting

### "tesseract is not installed or it's not in your PATH"
- Install Tesseract using instructions above
- Verify it's in your PATH: `which tesseract` (macOS/Linux)

### "Failed to download image"
- Images might be behind authentication
- Check internet connection
- Some promotional images might have expired URLs

### OCR Not Finding Text
- Image quality might be low
- Text might be part of a graphic design (not readable by OCR)
- Try adjusting Tesseract settings in `extract_text_from_image()`

### Performance Issues
- Reduce `max_images` parameter
- OCR is CPU-intensive, processing 10 images takes ~10-30 seconds

## Example Output

```
🖼️  Extracting images from email...
   Found 31 potential promotional images
   Processing image 1/10...
      ✓ Found offer: 60%
   Processing image 2/10...
      ✓ Found offer: UNBOX70
   ...
✓ Extracted 5 offers from images

Offer 1:
  Discount: 60%
  Keywords: free shipping, sale
  
Offer 2:
  Promo Code: UNBOX70
  Discount: 70%
  Expires: December 2, 2025
  Keywords: clearance, limited time
```
