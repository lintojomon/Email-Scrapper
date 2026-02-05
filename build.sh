#!/usr/bin/env bash
# Build script for Render deployment

echo "Installing Python dependencies..."
# Note: System packages (tesseract-ocr) are installed automatically from apt-packages.txt
pip install -r requirements-render.txt

echo "Build complete!"
