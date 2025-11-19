#!/bin/bash

echo "Starting GCP/GKE Monitoring Dashboard..."
echo ""

# Check if config.json exists
if [ ! -f "config.json" ]; then
    echo "ERROR: config.json not found!"
    echo "Please copy config.example.json to config.json and configure your projects."
    echo "Example: cp config.example.json config.json"
    exit 1
fi

# Check if backend dependencies are installed
if [ ! -d "backend/venv" ]; then
    echo "Backend virtual environment not found. Creating..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
else
    echo "Backend virtual environment found."
fi

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "Frontend node_modules not found. Installing..."
    cd frontend
    npm install
    cd ..
else
    echo "Frontend dependencies found."
fi

echo ""
echo "Starting services..."
echo "Backend will start on http://localhost:8000"
echo "Frontend will start on http://localhost:3000"
echo ""

# Start backend in background
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait a bit for backend to start
sleep 3

# Start frontend
cd frontend
npm run dev

# When frontend exits, kill backend
kill $BACKEND_PID
