import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@carcarepro.com")
APP_NAME = "CarCare Pro"

# Development mode detection
import sys
DEV_MODE = os.environ.get("UVICORN_RELOAD", "0") == "1" or "--reload" in sys.argv

# Check if email credentials are set
email_configured = all([EMAIL_USERNAME, EMAIL_PASSWORD])

# Print guidance if email is not configured
if not email_configured and DEV_MODE:
    logger.warning("=" * 80)
    logger.warning("Email credentials not configured. Verification codes will be printed to console.")
    logger.warning("To enable email sending, update your .env file with the following:")
    logger.warning("EMAIL_USERNAME=your-email@gmail.com")
    logger.warning("EMAIL_PASSWORD=your-app-password")
    logger.warning("")
    logger.warning("For Gmail, you need to use an App Password:")
    logger.warning("1. Enable 2-Step Verification on your Google account")
    logger.warning("2. Go to https://myaccount.google.com/apppasswords")
    logger.warning("3. Generate an App Password for 'Mail' and use it in EMAIL_PASSWORD")
    logger.warning("=" * 80)

def send_verification_email(to_email, verification_code):
    """
    Send verification email with the verification code

    Args:
        to_email (str): Recipient email address
        verification_code (str): Verification code to include in the email

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if not email_configured:
        logger.warning("Email credentials not configured. Printing verification code instead.")
        logger.info(f"Verification code for {to_email}: {verification_code}")
        return False

    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f"{APP_NAME} <{EMAIL_FROM}>"
        msg['To'] = to_email
        msg['Subject'] = f"{APP_NAME} - Verify Your Email"

        # Email body
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                <h2 style="color: #3498db;">Email Verification</h2>
                <p>Thank you for registering with {APP_NAME}!</p>
                <p>Your verification code is:</p>
                <div style="background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 5px; margin: 20px 0;">
                    {verification_code}
                </div>
                <p>Please enter this code on the verification page to complete your registration.</p>
                <p>This code will expire in 24 hours.</p>
                <p>If you didn't request this verification, please ignore this email.</p>
                <p>Best regards,<br>The {APP_NAME} Team</p>
            </div>
        </body>
        </html>
        """

        # Attach HTML content
        msg.attach(MIMEText(body, 'html'))

        # Connect to SMTP server
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure the connection
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(msg)

        logger.info(f"Verification email sent to {to_email}")
        return True

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to send verification email: {error_msg}")

        # Print helpful guidance for common errors
        if "535" in error_msg and "5.7.8" in error_msg and "BadCredentials" in error_msg:
            logger.error("=" * 80)
            logger.error("Gmail authentication failed. This is likely because:")
            logger.error("1. Your email or password is incorrect")
            logger.error("2. You're using your Google account password instead of an App Password")
            logger.error("3. Less secure app access is disabled (Google now requires App Passwords)")
            logger.error("")
            logger.error("To fix this:")
            logger.error("1. Enable 2-Step Verification on your Google account")
            logger.error("2. Go to https://myaccount.google.com/apppasswords")
            logger.error("3. Generate an App Password for 'Mail' and use it in your .env file")
            logger.error("=" * 80)
        elif "Authentication" in error_msg:
            logger.error("Authentication failed. Check your email credentials in the .env file.")

        # Always print the verification code in development mode
        if DEV_MODE:
            logger.info(f"DEVELOPMENT MODE: Verification code for {to_email}: {verification_code}")

        return False

def send_password_reset_email(to_email, reset_token):
    """
    Send password reset email with a reset link

    Args:
        to_email (str): Recipient email address
        reset_token (str): Password reset token

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if not email_configured:
        logger.warning("Email credentials not configured. Printing reset token instead.")
        logger.info(f"Password reset token for {to_email}: {reset_token}")
        return False

    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f"{APP_NAME} <{EMAIL_FROM}>"
        msg['To'] = to_email
        msg['Subject'] = f"{APP_NAME} - Reset Your Password"

        # Reset link
        reset_link = f"http://localhost:8000/reset-password?token={reset_token}&email={to_email}"

        # Email body
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                <h2 style="color: #3498db;">Password Reset</h2>
                <p>You requested to reset your password for {APP_NAME}.</p>
                <p>Click the button below to reset your password:</p>
                <div style="text-align: center; margin: 25px 0;">
                    <a href="{reset_link}" style="background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">Reset Password</a>
                </div>
                <p>Or copy and paste this link in your browser:</p>
                <p style="word-break: break-all; background-color: #f8f9fa; padding: 10px; font-size: 14px;">{reset_link}</p>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't request a password reset, please ignore this email.</p>
                <p>Best regards,<br>The {APP_NAME} Team</p>
            </div>
        </body>
        </html>
        """

        # Attach HTML content
        msg.attach(MIMEText(body, 'html'))

        # Connect to SMTP server
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure the connection
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(msg)

        logger.info(f"Password reset email sent to {to_email}")
        return True

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to send password reset email: {error_msg}")

        # Print helpful guidance for common errors
        if "535" in error_msg and "5.7.8" in error_msg and "BadCredentials" in error_msg:
            logger.error("=" * 80)
            logger.error("Gmail authentication failed. This is likely because:")
            logger.error("1. Your email or password is incorrect")
            logger.error("2. You're using your Google account password instead of an App Password")
            logger.error("3. Less secure app access is disabled (Google now requires App Passwords)")
            logger.error("")
            logger.error("To fix this:")
            logger.error("1. Enable 2-Step Verification on your Google account")
            logger.error("2. Go to https://myaccount.google.com/apppasswords")
            logger.error("3. Generate an App Password for 'Mail' and use it in your .env file")
            logger.error("=" * 80)
        elif "Authentication" in error_msg:
            logger.error("Authentication failed. Check your email credentials in the .env file.")

        # Always print the reset token in development mode
        if DEV_MODE:
            logger.info(f"DEVELOPMENT MODE: Password reset token for {to_email}: {reset_token}")

        return False

def test_email_configuration():
    """
    Test the email configuration by attempting to connect to the SMTP server

    Returns:
        dict: A dictionary with status and message
    """
    result = {
        "configured": email_configured,
        "status": "unknown",
        "message": "",
        "details": {}
    }

    if not email_configured:
        result["status"] = "not_configured"
        result["message"] = "Email credentials not configured"
        result["details"] = {
            "smtp_server": SMTP_SERVER,
            "smtp_port": SMTP_PORT,
            "username_set": bool(EMAIL_USERNAME),
            "password_set": bool(EMAIL_PASSWORD)
        }
        return result

    try:
        # Try to connect to the SMTP server
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=5) as server:
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)

            result["status"] = "success"
            result["message"] = "Successfully connected to SMTP server"
            result["details"] = {
                "smtp_server": SMTP_SERVER,
                "smtp_port": SMTP_PORT,
                "username": EMAIL_USERNAME,
                "from_address": EMAIL_FROM
            }
    except Exception as e:
        error_msg = str(e)
        result["status"] = "error"
        result["message"] = f"Failed to connect to SMTP server: {error_msg}"

        if "535" in error_msg and "5.7.8" in error_msg and "BadCredentials" in error_msg:
            result["error_type"] = "bad_credentials"
            result["help"] = "You need to use an App Password for Gmail. Enable 2-Step Verification and generate an App Password."
        elif "Authentication" in error_msg:
            result["error_type"] = "authentication"
            result["help"] = "Authentication failed. Check your email and password."
        elif "timed out" in error_msg:
            result["error_type"] = "timeout"
            result["help"] = "Connection timed out. Check your SMTP server and port settings."
        else:
            result["error_type"] = "unknown"

        result["details"] = {
            "smtp_server": SMTP_SERVER,
            "smtp_port": SMTP_PORT,
            "username": EMAIL_USERNAME,
            "error": error_msg
        }

    return result