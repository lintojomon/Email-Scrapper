# Docker Setup Guide

## Prerequisites
- Docker installed on your system
- Docker Compose (optional, but recommended)
- `credentials.json` file from Google Cloud Console

## Quick Start

### Option 1: Using Docker Compose (Recommended)

1. **Make sure you have `credentials.json` in the project root**
   ```bash
   ls credentials.json  # Should exist
   ```

2. **Build and run the container**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - Open browser: http://localhost:8080
   - The app will be running with Tesseract OCR support

4. **Stop the container**
   ```bash
   docker-compose down
   ```

### Option 2: Using Docker CLI

1. **Build the Docker image**
   ```bash
   docker build -t email-analyzer .
   ```

2. **Run the container**
   ```bash
   docker run -d \
     --name email-analyzer \
     -p 8080:8080 \
     -e BASE_URL=http://localhost:8080 \
     -e OAUTHLIB_INSECURE_TRANSPORT=1 \
     -v $(pwd)/credentials.json:/app/credentials.json:ro \
     -v $(pwd)/flask_session:/app/flask_session \
     email-analyzer
   ```

3. **Check logs**
   ```bash
   docker logs -f email-analyzer
   ```

4. **Stop and remove container**
   ```bash
   docker stop email-analyzer
   docker rm email-analyzer
   ```

## Configuration

### Environment Variables

- `BASE_URL`: Base URL for OAuth callbacks (default: `http://localhost:8080`)
- `FLASK_SECRET_KEY`: Secret key for Flask sessions (auto-generated if not set)
- `PORT`: Port to run the app (default: `8080`)
- `OAUTHLIB_INSECURE_TRANSPORT`: Set to `1` for local HTTP development
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account JSON for Cloud Vision API

### Volumes

- `./credentials.json:/app/credentials.json:ro` - OAuth credentials (read-only)
- `./flask_session:/app/flask_session` - Session storage (persistent)

## Google OAuth Setup

Before running the application, make sure your OAuth credentials are configured:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select a project
3. Enable Gmail API
4. Create OAuth 2.0 Client ID (Web application)
5. Add authorized redirect URI: `http://localhost:8080/oauth/callback`
6. Download `credentials.json` and place it in the project root

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs email-analyzer

# Verify credentials.json exists
docker exec email-analyzer ls -la credentials.json
```

### OCR not working
The Dockerfile includes Tesseract OCR. If you still have issues:
```bash
# Check Tesseract installation
docker exec email-analyzer tesseract --version
```

### Port already in use
```bash
# Use a different port
docker run -p 8081:8080 ... email-analyzer
# Then access at http://localhost:8081
```

## Development Mode

To enable hot-reload for development:

```yaml
# Add to docker-compose.yml under volumes:
- .:/app
```

Then restart with:
```bash
docker-compose up --build
```

## Production Deployment

For production:
1. Remove `OAUTHLIB_INSECURE_TRANSPORT=1`
2. Set proper `BASE_URL` (https://your-domain.com)
3. Use proper secret key: `-e FLASK_SECRET_KEY=$(openssl rand -hex 32)`
4. Update OAuth redirect URI in Google Cloud Console

## Cleanup

```bash
# Remove container and image
docker-compose down
docker rmi email-analyzer

# Or with Docker CLI
docker stop email-analyzer
docker rm email-analyzer
docker rmi email-analyzer
```
