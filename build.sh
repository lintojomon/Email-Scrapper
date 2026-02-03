#!/usr/bin/env bash
# Build script for Render deployment

echo "Installing system dependencies..."

# Install Tesseract OCR
apt-get update
apt-get install -y tesseract-ocr

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Build complete!"
