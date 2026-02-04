# Quick Start - Deploy to Vercel in 5 Minutes

## ⚡ Fast Track Deployment

### 1. Install Vercel CLI (if not installed)
```bash
npm install -g vercel
```

### 2. Login to Vercel
```bash
vercel login
```
Follow the browser authentication.

### 3. Enable Google Cloud Vision API

**For OCR to work on Vercel, you need Cloud Vision API:**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (same one with Gmail API)
3. Go to **APIs & Services** → **Library**
4. Search for **"Cloud Vision API"**
5. Click **Enable**
6. ✅ Done! Your existing credentials will work for both Gmail and Vision API

### 4. Prepare Environment Variables

**Generate a secret key:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```
Copy this - you'll need it as `FLASK_SECRET_KEY`

**Get your Google credentials:**
```bash
cat credentials.json | tr -d '\n'
```
Copy this entire JSON - you'll need it as `GOOGLE_CREDENTIALS`

### 4. Deploy
```bash
cd /Users/lintojomon/Desktop/testing/Email-Scrapper
vercel
```

**Answer the prompts:**
- Set up and deploy? → **Y**
- Which scope? → Select your account
- Link to existing project? → **N**
- Project name? → **email-analyzer** (or your choice)
- Directory? → **./** (just press Enter)

### 5. Add Environment Variables

After deployment, you'll get a URL like: `https://email-analyzer-abc123.vercel.app`

**Go to Vercel Dashboard:**
```
https://vercel.com/dashboard
```

1. Click your project **email-analyzer**
2. Go to **Settings** → **Environment Variables**
3. Add three variables:

   **GOOGLE_CREDENTIALS** (Production, Preview, Development)
   ```
   Paste the JSON from step 3
   ```

   **FLASK_SECRET_KEY** (Production, Preview, Development)
   ```
   Paste the secret from step 3
   ```

   **BASE_URL** (Production only)
   ```
   https://email-analyzer-abc123.vercel.app
   (Use your actual Vercel URL)
   ```

### 6. Update Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Click your OAuth 2.0 Client ID
3. Under **Authorized redirect URIs**, add:
   ```
   https://email-analyzer-abc123.vercel.app/oauth/callback
   ```
   (Replace with your actual Vercel URL)
4. Click **Save**

### 7. Redeploy to Production
```bash
vercel --prod
```

### 8. Test Your App
Visit your Vercel URL and test:
- ✅ Login with Google
- ✅ Analyze emails
- ✅ OCR now works using Cloud Vision API!

## 🔥 Done!

Your app is now live at: `https://email-analyzer-abc123.vercel.app`

---

## 📌 Important Notes

**OCR on Vercel Uses Cloud Vision API**
- Automatically switches from Tesseract (local) to Cloud Vision (cloud)
- Works seamlessly on serverless
- Make sure Cloud Vision API is enabled in Google Cloud Console
- Uses same credentials as Gmail API

**Session Storage**
- Uses filesystem sessions (works but limited on serverless)
- For production, consider Redis (see VERCEL_DEPLOYMENT.md)

**Private Repository**
- Your repo stays private
- Only you can deploy
- To allow team deployments, add them in Vercel project settings

---

## 🆘 Troubleshooting

**Error: OAuth callback fails**
→ Check that redirect URI in Google Console matches your Vercel URL exactly

**Error: 500 Internal Server Error**
→ Check logs: `vercel logs <your-url>`

**Error: Module not found**
→ Make sure all imports work without OCR dependencies

**Need help?**
See detailed guide: [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md)
