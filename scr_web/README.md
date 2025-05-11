# CarCare Pro

A comprehensive vehicle maintenance tracking application with features for service reminders, repair history management, and AI-powered assistance.

## Features

- User authentication with email verification
- Google OAuth integration
- Vehicle maintenance tracking
- Tire analysis
- AI-powered chat assistance using Google Gemini
- Admin dashboard for user management

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- MongoDB 4.4 or higher
- Node.js and npm (for frontend development)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/carcare-pro.git
   cd carcare-pro
   ```

2. Run the setup script:
   ```bash
   ./setup.sh
   ```

   This script will:
   - Create a virtual environment
   - Install dependencies
   - Check for MongoDB
   - Create a default .env file if one doesn't exist
   - Make scripts executable

3. Configure environment variables:
   Edit the `.env` file in the root directory with your settings:
   ```
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
   GEMINI_API_KEY=your-gemini-api-key
   ```

   Notes:
   - For Gmail, you need to use an App Password. See instructions below.
   - For the Gemini API key, get one from [Google AI Studio](https://makersuite.google.com/app/apikey).

### Setting up Gmail App Password

To use Gmail for sending verification emails, you need to set up an App Password:

1. Enable 2-Step Verification on your Google account:
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Click on "2-Step Verification" and follow the steps to enable it

2. Generate an App Password:
   - Go to [App Passwords](https://myaccount.google.com/apppasswords)
   - Select "Mail" as the app and "Other" as the device (name it "CarCare Pro")
   - Click "Generate"
   - Copy the 16-character password that appears

3. Update your .env file:
   ```
   EMAIL_USERNAME=your-gmail-address@gmail.com
   EMAIL_PASSWORD=your-16-character-app-password
   ```

4. Restart the application for the changes to take effect

### Checking Gemini API Key

To check if your Gemini API key is valid and working:

```bash
python check_gemini_api.py
```

This script will:
1. Check if the API key is present in the .env file
2. List available Gemini models
3. Test the API with a simple query
4. Provide troubleshooting information if there are issues

### Running the Application

#### Option 1: Running Locally

1. Start MongoDB:
   ```bash
   sudo systemctl start mongod  # Linux
   brew services start mongodb-community  # macOS
   ```

2. Start the application:
   ```bash
   ./start_app.sh
   ```

   Or manually:
   ```bash
   python -m uvicorn main:app --reload
   ```

3. Access the application at http://localhost:8000

#### Option 2: Running with Docker

The application can be run using Docker and Docker Compose:

1. Make sure Docker and Docker Compose are installed:
   ```bash
   docker --version
   docker-compose --version
   ```

2. Build and start the containers:
   ```bash
   docker-compose build
   docker-compose up -d
   ```

3. To stop the containers:
   ```bash
   docker-compose down
   ```

4. To view logs:
   ```bash
   docker-compose logs -f
   ```

5. To rebuild from scratch:
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

6. Access the application:
   - Frontend: http://localhost:8080
   - Backend API: http://localhost:8001/api
   - MongoDB: localhost:27018

### Development Mode

In development mode:
- Email verification codes are printed to the console
- A development endpoint is available to retrieve verification codes
- The application will work even if MongoDB authentication is not set up

## Email Verification

The application includes email verification for new user registrations:

1. When a user registers, a verification code is sent to their email
2. The user must enter this code on the verification page to activate their account
3. In development mode, verification codes are printed to the console and can be retrieved via the development endpoint

## API Documentation

API documentation is available at:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Troubleshooting

### Datetime Errors

If you encounter errors related to `datetime.timezone.utc`, make sure you're using Python 3.9 or higher, or that you have the correct imports in your code.

### Bcrypt Warnings

If you see warnings about bcrypt version, you can safely ignore them or install a specific version of bcrypt:
```bash
pip install bcrypt==4.0.1
```

### Gemini API Issues

If the chat functionality is not working:
1. Check your Gemini API key using the provided script:
   ```bash
   python check_gemini_api.py
   ```
2. Make sure you have a valid API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
3. Update your .env file with the new key
4. Restart the application

### MongoDB Connection Issues

If you have issues connecting to MongoDB:
1. Make sure MongoDB is running:
   ```bash
   sudo systemctl status mongod  # Linux
   brew services list            # macOS
   ```
2. Check the MongoDB connection string in your .env file
3. If using Docker, make sure the MongoDB container is running

### Email Configuration Issues

If you're having issues with email verification:

1. Check your email configuration using the admin dashboard:
   - Log in as an admin user
   - Go to the Settings tab
   - Click "Test Configuration" in the Email Configuration section

2. Or use the command-line tool:
   ```bash
   python check_email_config.py
   ```

3. Common issues:
   - Using your Google account password instead of an App Password
   - Not enabling 2-Step Verification on your Google account
   - Incorrect email address in the .env file
   - Firewall blocking outgoing SMTP connections

4. In development mode, verification codes are printed to the console, so you can still test the application without setting up email

### Docker Configuration

The application uses a simple Docker setup:

- `docker-compose.yml`: Configuration file for all services
- `backend/Dockerfile`: Dockerfile for the backend service
- `frontend/Dockerfile`: Dockerfile for the frontend service

#### Docker Volumes

The application uses Docker volumes for data persistence:

- `mongo-data`: MongoDB data files
- `mongo-config`: MongoDB configuration

#### Port Configuration

The Docker setup uses the following ports:

- Frontend: `8080` (http://localhost:8080)
- Backend API: `8001` (http://localhost:8001/api)
- MongoDB: `27018` (localhost:27018)

Note: MongoDB uses port 27018 on the host to avoid conflicts with any locally running MongoDB instance.

#### Troubleshooting Docker Issues

If you encounter issues with Docker:

1. Check container logs:
   ```bash
   docker-compose logs -f
   ```

2. Restart containers:
   ```bash
   docker-compose restart
   ```

3. Rebuild from scratch:
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

4. Check container status:
   ```bash
   docker-compose ps
   ```

5. To reset all data:
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
