#!/usr/bin/env bash
# Build script for Render deployment

echo "Installing system dependencies..."

# Install Tesseract OCR with English language data
apt-get update
apt-get install -y tesseract-ocr tesseract-ocr-eng libtesseract-dev

echo "Installing Python dependencies..."
pip install -r requirements-render.txt

echo "Build complete!"
