# Deploying Email Analyzer to Vercel

## ✅ OCR Now Works on Vercel!

**How it works:**
- **Local/Render**: Uses Tesseract OCR (native binary)
- **Vercel**: Uses Google Cloud Vision API (cloud service)
- **Automatic switching**: App detects environment and uses appropriate OCR provider
- **Same credentials**: Uses your existing Google Cloud credentials

## Prerequisites

1. **Vercel Account**: Sign up at https://vercel.com (free tier available)
2. **Vercel CLI**: Install globally
   ```bash
   npm install -g vercel
   ```
3. **Git Repository**: Your code should be in a Git repository
4. **Google Cloud Vision API**: Enable in Google Cloud Console (free tier: 1000 images/month)

## Step-by-Step Deployment

### Step 1: Prepare Your Repository

Make sure you're in the project directory:
```bash
cd /Users/lintojomon/Desktop/testing/Email-Scrapper
```

### Step 2: Configure Google OAuth for Vercel

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Navigate to **APIs & Services** → **Credentials**
4. Click on your OAuth 2.0 Client ID
5. Add Vercel authorized redirect URIs:
   ```
   https://your-project-name.vercel.app/oauth/callback
   ```
   (You'll get the actual domain after first deployment)

### Step 3: Set Up Environment Variables

You'll need to set these as Vercel environment variables:

**Required:**
- `GOOGLE_CREDENTIALS` - Your entire credentials.json content (as JSON string)
- `FLASK_SECRET_KEY` - A random secret key
- `BASE_URL` - Your Vercel app URL (e.g., https://your-app.vercel.app)

**Generate a secret key:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**Get your credentials as JSON string:**
```bash
cat credentials.json | tr -d '\n'
```

### Step 4: Login to Vercel CLI

```bash
vercel login
```

Follow the prompts to authenticate.

### Step 5: Deploy to Vercel

**Initial deployment (test):**
```bash
vercel
```

This will:
- Create a new Vercel project
- Deploy to a preview URL
- Ask you to link to existing project or create new one

**Answer the prompts:**
```
? Set up and deploy "~/Desktop/testing/Email-Scrapper"? [Y/n] Y
? Which scope do you want to deploy to? <Your Vercel username>
? Link to existing project? [y/N] N
? What's your project's name? email-analyzer
? In which directory is your code located? ./
```

### Step 6: Configure Environment Variables (Web Dashboard)

After first deployment, configure environment variables:

1. Go to https://vercel.com/dashboard
2. Select your project "email-analyzer"
3. Click **Settings** → **Environment Variables**
4. Add these variables:

   **GOOGLE_CREDENTIALS**
   ```
   Paste the entire content from: cat credentials.json | tr -d '\n'
   ```

   **FLASK_SECRET_KEY**
   ```
   Your generated secret key from Step 3
   ```

   **BASE_URL**
   ```
   https://email-analyzer-<your-hash>.vercel.app
   (Copy from your deployment URL)
   ```

5. Click **Save** for each variable

### Step 7: Update Google OAuth Redirect URI

1. Copy your Vercel deployment URL (e.g., `https://email-analyzer-abc123.vercel.app`)
2. Go back to Google Cloud Console → Credentials
3. Edit your OAuth 2.0 Client ID
4. Add to **Authorized redirect URIs**:
   ```
   https://email-analyzer-<your-hash>.vercel.app/oauth/callback
   ```
5. Click **Save**

### Step 8: Redeploy with Environment Variables

```bash
vercel --prod
```

This deploys to production with your environment variables.

### Step 9: Test Your Deployment

Visit your Vercel URL:
```
https://email-analyzer-<your-hash>.vercel.app
```

**Test checklist:**
- ✅ Homepage loads
- ✅ Login button works
- ✅ Google OAuth redirects correctly
- ✅ Dashboard appears after login
- ✅ Can analyze emails (without OCR)
- ⚠️ OCR will be disabled (expected)

## Alternative: Deploy via GitHub Integration

### Step 1: Push to GitHub

Make sure your repo is pushed to GitHub:
```bash
git add .
git commit -m "Add Vercel deployment configuration"
git push origin main
```

### Step 2: Import from GitHub

1. Go to https://vercel.com/new
2. Click **Import Git Repository**
3. Authenticate with GitHub
4. Select your `Email-Scrapper` repository
5. Click **Import**

### Step 3: Configure Project

**Framework Preset**: Other
**Root Directory**: ./
**Build Command**: (leave empty)
**Output Directory**: (leave empty)

### Step 4: Add Environment Variables

Before deploying, click **Environment Variables** and add:
- `GOOGLE_CREDENTIALS`
- `FLASK_SECRET_KEY`
- `BASE_URL` (use `https://your-project.vercel.app` format)

### Step 5: Deploy

Click **Deploy** button and wait for deployment to complete.

### Step 6: Update Google OAuth

Follow Step 7 from CLI deployment above.

## Vercel CLI Commands

```bash
# Deploy to preview (development)
vercel

# Deploy to production
vercel --prod

# View deployment logs
vercel logs <deployment-url>

# List all deployments
vercel ls

# View environment variables
vercel env ls

# Add environment variable
vercel env add VARIABLE_NAME

# Remove deployment
vercel rm <deployment-name>
```

## Troubleshooting

### Issue: "Module not found" errors

**Solution**: Make sure `requirements-vercel.txt` is being used
```bash
# Rename requirements file
mv requirements.txt requirements-render.txt
mv requirements-vercel.txt requirements.txt
git add .
git commit -m "Use Vercel-compatible requirements"
vercel --prod
```

### Issue: OAuth callback not working

**Solution**: 
1. Check `BASE_URL` environment variable matches your Vercel URL
2. Verify redirect URI in Google Cloud Console matches exactly
3. Redeploy after changes: `vercel --prod`

### Issue: 500 Internal Server Error

**Solution**: Check logs
```bash
vercel logs <your-deployment-url>
```

### Issue: Session not persisting

**Solution**: Vercel serverless functions are stateless. The app uses filesystem sessions which work but may have issues. Consider upgrading to Redis sessions for production.

### Issue: OCR not working

**Expected**: OCR is disabled on Vercel. Users will see a checkbox to enable/disable OCR, but it won't work even when enabled. Consider:
- Using Google Vision API for OCR
- Keeping Render deployment for OCR functionality
- Removing OCR UI elements for Vercel deployment

## Production Considerations

### 1. Use Redis for Sessions (Recommended)

Vercel's filesystem is ephemeral. For production, use Redis:

```bash
# Install Redis client
pip install redis

# Add to requirements.txt
echo "redis==5.0.1" >> requirements.txt
```

Update app.py:
```python
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url(os.environ.get('REDIS_URL'))
```

**Redis providers:**
- Upstash (free tier, Vercel integration)
- Redis Labs (free tier)
- AWS ElastiCache (paid)

### 2. Custom Domain

Add custom domain in Vercel dashboard:
1. Go to **Settings** → **Domains**
2. Add your domain (e.g., `emailanalyzer.com`)
3. Update DNS records as instructed
4. Update Google OAuth redirect URIs

### 3. Analytics

Enable Vercel Analytics:
1. Go to **Analytics** tab
2. Enable Web Analytics
3. Add to your app:
```bash
vercel env add VERCEL_ANALYTICS_ID
```

## Cost Comparison

| Feature | Vercel Free | Vercel Pro |
|---------|-------------|------------|
| Bandwidth | 100 GB/month | 1 TB/month |
| Build Time | 6000 min/month | Unlimited |
| Functions | 100 GB-hours | 1000 GB-hours |
| Serverless Size | 50 MB | 50 MB |
| **Price** | **$0** | **$20/month** |

## When to Use Vercel vs Render

**Use Vercel if:**
- ✅ You don't need OCR functionality
- ✅ You want faster deployment and updates
- ✅ You want automatic preview deployments for PRs
- ✅ You need CDN and edge functions

**Use Render if:**
- ✅ You need OCR (Tesseract) functionality
- ✅ You need persistent filesystem
- ✅ You want longer-running processes
- ✅ You need native system dependencies

## Next Steps

1. Test the deployment thoroughly
2. Monitor usage in Vercel dashboard
3. Set up Redis for production sessions
4. Configure custom domain (optional)
5. Enable Vercel Analytics (optional)

## Support

- Vercel Documentation: https://vercel.com/docs
- Vercel Discord: https://vercel.com/discord
- GitHub Issues: https://github.com/<your-username>/Email-Scrapper/issues
