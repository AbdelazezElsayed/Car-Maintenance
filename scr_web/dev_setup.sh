#!/bin/bash

# Development setup script for CarCare Pro

echo "Setting up development environment for CarCare Pro..."

# Check if MongoDB is running
if ! pgrep -x "mongod" > /dev/null; then
    echo "MongoDB is not running. Starting MongoDB..."
    if command -v systemctl &> /dev/null; then
        sudo systemctl start mongod
    elif command -v brew &> /dev/null; then
        brew services start mongodb-community
    else
        echo "Could not start MongoDB automatically. Please start it manually."
    fi
else
    echo "MongoDB is already running."
fi

# Set environment variable to indicate development mode
export UVICORN_RELOAD=1

# Install required Python packages
echo "Installing required Python packages..."
pip install -r backend/requirements.txt

# Create necessary directories if they don't exist
echo "Creating necessary directories..."
mkdir -p frontend/pages/admin
mkdir -p frontend/pages/verify-email
mkdir -p frontend/pages/chat
mkdir -p frontend/pages/tire
mkdir -p frontend/pages/maintenance
mkdir -p frontend/pages/auth-success
mkdir -p frontend/pages/login
mkdir -p frontend/pages/register

echo "Setup complete! You can now run the application with:"
echo "python -m uvicorn main:app --reload"
