#!/bin/bash

# Start MongoDB if not running
if ! pgrep -x "mongod" > /dev/null; then
    echo "Starting MongoDB..."
    if command -v systemctl &> /dev/null; then
        sudo systemctl start mongod
    elif command -v brew &> /dev/null; then
        brew services start mongodb-community
    else
        echo "Could not start MongoDB automatically. Please start it manually."
        exit 1
    fi
    
    # Wait for MongoDB to start
    echo "Waiting for MongoDB to start..."
    sleep 3
fi

# Set development mode environment variable
export UVICORN_RELOAD=1

# Start the application
echo "Starting CarCare Pro application..."
python -m uvicorn main:app --reload

# This script will exit when the application is stopped
echo "Application stopped."
