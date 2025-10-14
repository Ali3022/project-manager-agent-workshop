#!/bin/bash

# Project Management Assistant - Streamlit Web UI
# Run this script to start the web interface

echo "🚀 Starting Project Management Assistant Web UI..."
echo "Make sure you have set your GEMINI_API_KEY environment variable!"
echo ""

# Check if .env file exists
if [ -f .env ]; then
    echo "📄 Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  No .env file found. Make sure GEMINI_API_KEY is set in your environment."
fi

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ GEMINI_API_KEY is not set!"
    echo "Please set it by either:"
    echo "1. Creating a .env file with: GEMINI_API_KEY=your_api_key_here"
    echo "2. Exporting it: export GEMINI_API_KEY=your_api_key_here"
    exit 1
fi

echo "✅ API key found!"
echo "🌐 Starting Streamlit app..."
echo ""

# Run Streamlit
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
