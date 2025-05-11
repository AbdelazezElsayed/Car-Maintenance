#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== CarCare Pro Setup ===${NC}"
echo "This script will set up the CarCare Pro application."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3 and try again.${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d " " -f 2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

echo -e "${GREEN}Found Python $PYTHON_VERSION${NC}"

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo -e "${YELLOW}Warning: Python 3.8 or higher is recommended. You have Python $PYTHON_VERSION.${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${GREEN}Creating virtual environment...${NC}"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create virtual environment. Please install venv package and try again.${NC}"
        exit 1
    fi
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r backend/requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install dependencies. Please check the error message above.${NC}"
    exit 1
fi

# Check if MongoDB is installed
echo -e "${GREEN}Checking MongoDB...${NC}"
if command -v mongod &> /dev/null; then
    echo -e "${GREEN}MongoDB is installed.${NC}"
else
    echo -e "${YELLOW}MongoDB is not installed. You will need to install MongoDB to run the application.${NC}"
    echo "For Ubuntu: sudo apt install -y mongodb"
    echo "For macOS: brew install mongodb-community"
    echo "For other systems, please refer to the MongoDB documentation."
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}No .env file found. Creating a default one...${NC}"
    cat > .env << EOL
# MongoDB Connection
MONGODB_URI=mongodb://localhost:27017/CAR

# JWT Authentication
SECRET_KEY=your-secret-key-keep-it-secret
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Admin User (created on first run if no admin exists)
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=admin123

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM=noreply@carcarepro.com

# Gemini API Key
# You need to replace this with your own valid Gemini API key
# Get one from https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your-gemini-api-key
EOL
    echo -e "${YELLOW}Please edit the .env file to set your configuration.${NC}"
fi

# Make scripts executable
chmod +x start_app.sh
chmod +x check_gemini_api.py

echo -e "${GREEN}Setup complete!${NC}"
echo -e "To start the application, run: ${YELLOW}./start_app.sh${NC}"
echo -e "To check your Gemini API key, run: ${YELLOW}python check_gemini_api.py${NC}"
echo -e "${GREEN}Happy coding!${NC}"
