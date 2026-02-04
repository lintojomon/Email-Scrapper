# api/index.py - Vercel Serverless Entry Point
"""
Vercel serverless function entry point for Flask app.
This wraps the main Flask app for serverless deployment.
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel serverless function handler
def handler(request, context):
    """Vercel serverless handler."""
    return app(request, context)

# For Vercel, we need to export the Flask app
# Vercel will handle the WSGI interface
application = app

# This is important for Vercel
if __name__ == "__main__":
    app.run()
