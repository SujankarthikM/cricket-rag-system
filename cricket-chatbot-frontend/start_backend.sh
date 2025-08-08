#!/bin/bash

echo "🏏 Starting Cricket Match Query Backend..."

# Install Python dependencies
cd backend
pip install -r requirements.txt

# Start the FastAPI server
python main.py