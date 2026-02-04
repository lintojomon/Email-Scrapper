# api/index.py - Vercel Serverless Entry Point
"""
Vercel serverless function entry point for Flask app.
This wraps the main Flask app for serverless deployment.
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask app
from app import app

# Export the app for Vercel
# Vercel automatically detects Flask apps and handles WSGI
app = app
