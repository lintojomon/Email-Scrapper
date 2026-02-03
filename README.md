# 📧 Email Analyzer - Web Application

A web application that analyzes your Gmail inbox to discover memberships, credit card offers, and coupons.

## ✨ Features

- **🔔 Membership Detection**: Amazon Prime, Netflix, Costco, Spotify, and more
- **💳 Credit Card Offers**: Rewards, benefits, and special promotions
- **🏷️ Coupon Finder**: Discounts, promo codes, and cashback offers
- **🔐 Secure**: OAuth 2.0 authentication, read-only access, no data stored

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Google OAuth Credentials

**IMPORTANT**: For the web app, you need **Web Application** OAuth credentials (not Desktop).

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Enable the **Gmail API**:
   - Go to APIs & Services → Library
   - Search for "Gmail API"
   - Click Enable
4. Create OAuth credentials:
   - Go to APIs & Services → Credentials
   - Click "Create Credentials" → "OAuth client ID"
   - Select **"Web application"** as application type
   - Name it (e.g., "Email Analyzer Web")
   - Add **Authorized redirect URIs**:
     - For local development: `http://localhost:5000/oauth/callback`
     - For production: `https://yourdomain.com/oauth/callback`
   - Click Create
5. Download the credentials JSON
6. Save it as `credentials.json` in the project folder

### 3. Run the Web Application

```bash
python app.py
```

Open http://localhost:5000 in your browser.

## 🌐 Deployment Options

### Option 1: Local Network Testing

To let others on your network test:

```bash
python app.py
```

Share your local IP: `http://<your-ip>:5000`

### Option 2: Deploy to a Cloud Provider

#### Heroku
```bash
# Create Procfile
echo "web: gunicorn app:app" > Procfile

# Deploy
heroku create your-app-name
heroku config:set FLASK_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
git push heroku main
```

#### Railway / Render / Fly.io

1. Push code to GitHub
2. Connect repository to the platform
3. Set environment variables:
   - `FLASK_SECRET_KEY`: A secure random string
4. Deploy

### Option 3: ngrok (Quick Testing)

```bash
# Install ngrok
brew install ngrok  # macOS

# Run the app
python app.py

# In another terminal, expose it
ngrok http 5000
```

**Note**: Update your Google OAuth redirect URI to include the ngrok URL.

## 📁 Project Structure

```
Email-Scrapper/
├── app.py                 # Flask web application (NEW)
├── analyzer.py            # Core analysis logic
├── auth.py               # OAuth authentication (CLI)
├── gmail_reader.py       # Gmail API integration
├── patterns.py           # Regex patterns for detection
├── credentials.json      # Google OAuth credentials
├── requirements.txt      # Python dependencies
├── templates/            # HTML templates (NEW)
│   ├── index.html       # Login page
│   ├── dashboard.html   # Analysis options
│   ├── results.html     # Results display
│   └── error.html       # Error page
└── README.md            # This file
```

## 🔒 Security Notes

- **Read-only access**: The app only requests read access to emails
- **No storage**: Emails are analyzed in memory and not stored
- **Session-based**: Each user's authentication is stored in their session
- **HTTPS recommended**: Use HTTPS in production

## 🛠️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_SECRET_KEY` | Secret key for sessions | Auto-generated |
| `OAUTHLIB_INSECURE_TRANSPORT` | Allow HTTP (dev only) | `1` |

### Production Checklist

- [ ] Set a strong `FLASK_SECRET_KEY`
- [ ] Enable HTTPS
- [ ] Remove `OAUTHLIB_INSECURE_TRANSPORT`
- [ ] Update OAuth redirect URIs
- [ ] Configure proper session storage (Redis/database)

## 📝 CLI Usage (Original)

The original CLI is still available:

```bash
# Analyze last 50 emails
python analyzer.py

# Analyze last 100 emails
python analyzer.py -n 100

# Analyze emails from last 30 days
python analyzer.py -d 30

# Export to JSON with HTML viewer
python analyzer.py --json
```

## 🤝 Contributing

Feel free to submit issues and pull requests!

## 📄 License

MIT License
