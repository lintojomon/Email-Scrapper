# Enable Google Cloud Vision API for Vercel OCR

## Why Cloud Vision API?

Vercel's serverless environment can't run Tesseract (native binary), so we use Google Cloud Vision API instead. It's:
- ✅ **Cloud-based** - works on serverless
- ✅ **Free tier** - 1,000 images/month free
- ✅ **Same credentials** - uses your existing Google OAuth credentials
- ✅ **Better accuracy** - Google's advanced ML models

## Quick Enable (2 Minutes)

### Step 1: Open Google Cloud Console
Visit: https://console.cloud.google.com/

### Step 2: Select Your Project
Click the project dropdown (top left) and select the project where you enabled Gmail API.

### Step 3: Enable Cloud Vision API
1. Click **Navigation Menu** (☰) → **APIs & Services** → **Library**
2. In the search box, type: **"Cloud Vision API"**
3. Click on **Cloud Vision API**
4. Click the blue **Enable** button
5. Wait 10-20 seconds for activation

### Step 4: Verify
Go to **APIs & Services** → **Dashboard** and you should see:
- ✅ Gmail API (enabled)
- ✅ Cloud Vision API (enabled)

### Step 5: Done!
Your existing `credentials.json` now works for both Gmail and Vision API. No additional configuration needed!

## Pricing

**Free Tier (Monthly):**
- First 1,000 images: **FREE**
- After 1,000: $1.50 per 1,000 images

**Typical usage:**
- 15 emails with 2 images each = 30 images
- Can analyze ~33 batches per month for free
- More than enough for personal use

## Verifying OCR Works

After deploying to Vercel and enabling Vision API:

1. Analyze some emails with images
2. Check Vercel logs:
   ```bash
   vercel logs <your-url>
   ```
3. Look for:
   ```
   📧 Analysis requested: 15 emails, OCR=enabled (Cloud Vision API)
   🔍 Missing data (promo code), using OCR...
   ```

If you see errors about Vision API:
- Make sure API is enabled in Cloud Console
- Verify your GOOGLE_CREDENTIALS environment variable is set correctly in Vercel
- Redeploy: `vercel --prod`

## Disabling OCR (Optional)

If you don't want to use Cloud Vision API, you can disable OCR:
1. In the dashboard, uncheck **"Enable OCR"**
2. OCR will be skipped (faster, no API calls)
3. Email analysis still works, just without image text extraction

## Cost Control

To avoid unexpected charges:

**Set up billing alerts:**
1. Go to [Billing](https://console.cloud.google.com/billing)
2. Click **Budgets & alerts**
3. Create budget: $5/month
4. Set alerts at 50%, 90%, 100%

**Monitor usage:**
- Check [Vision API Quotas](https://console.cloud.google.com/apis/api/vision.googleapis.com/quotas)
- View monthly usage in billing reports

## Alternative: Disable Cloud OCR

If you prefer not to use Cloud Vision:

**Option 1:** Uncheck OCR in UI
- Simple, per-analysis control
- OCR checkbox still visible

**Option 2:** Force disable in code
- Edit `app.py`, find line ~193
- Change: `enable_ocr = False  # Force disable`
- Commit and redeploy

**Option 3:** Keep using Render for OCR
- Render uses Tesseract (free, local)
- Vercel for everything else
- Choose based on feature needs

## Troubleshooting

**Error: "Cloud Vision API has not been used"**
→ Enable the API in Google Cloud Console (see Step 3 above)

**Error: "Permission denied"**
→ Make sure GOOGLE_CREDENTIALS in Vercel matches credentials.json exactly

**No text extracted from images**
→ Check that images contain readable text
→ Verify Vision API is receiving requests in Cloud Console

**High costs**
→ Set billing alerts
→ Consider disabling OCR for high-volume use
→ Stick with Render deployment (free Tesseract)
