#!/usr/bin/env python3
"""
Script to check email configuration and test SMTP connection.
This helps diagnose issues with email sending functionality.
"""

import os
import sys
import json
from dotenv import load_dotenv
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_email_config(send_test=False, recipient=None):
    """Check email configuration and test SMTP connection"""
    # Load environment variables
    load_dotenv()
    
    # Import after loading environment variables
    from backend.email_service import test_email_configuration, send_verification_email
    
    # Test email configuration
    print("\n🔍 Checking email configuration...")
    result = test_email_configuration()
    
    # Print results
    if result["status"] == "success":
        print("\n✅ SUCCESS: Email configuration is valid!")
        print(f"SMTP Server: {result['details']['smtp_server']}:{result['details']['smtp_port']}")
        print(f"Username: {result['details']['username']}")
        print(f"From Address: {result['details']['from_address']}")
    elif result["status"] == "not_configured":
        print("\n⚠️ WARNING: Email is not configured")
        print("To configure email, update your .env file with the following:")
        print("EMAIL_USERNAME=your-email@gmail.com")
        print("EMAIL_PASSWORD=your-app-password")
        print("\nFor Gmail, you need to use an App Password:")
        print("1. Enable 2-Step Verification on your Google account")
        print("2. Go to https://myaccount.google.com/apppasswords")
        print("3. Generate an App Password for 'Mail' and use it in EMAIL_PASSWORD")
    elif result["status"] == "error":
        print(f"\n❌ ERROR: {result['message']}")
        if "error_type" in result and "help" in result:
            print(f"\nHelp: {result['help']}")
        
        if "535" in result["message"] and "BadCredentials" in result["message"]:
            print("\nFor Gmail, you need to use an App Password:")
            print("1. Enable 2-Step Verification on your Google account")
            print("2. Go to https://myaccount.google.com/apppasswords")
            print("3. Generate an App Password for 'Mail' and use it in EMAIL_PASSWORD")
    
    # Send test email if requested
    if send_test and result["status"] == "success" and recipient:
        print(f"\n🔍 Sending test verification email to {recipient}...")
        test_code = "123456"
        success = send_verification_email(recipient, test_code)
        
        if success:
            print(f"\n✅ SUCCESS: Test email sent to {recipient}")
            print(f"Verification code: {test_code}")
        else:
            print(f"\n❌ ERROR: Failed to send test email to {recipient}")
    
    return result["status"] == "success"

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Check email configuration and test SMTP connection")
    parser.add_argument("--send-test", action="store_true", help="Send a test email")
    parser.add_argument("--recipient", type=str, help="Email recipient for test email")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Email Configuration Checker")
    print("=" * 60)
    
    if args.send_test and not args.recipient:
        print("Error: --recipient is required when using --send-test")
        return 1
    
    success = check_email_config(args.send_test, args.recipient)
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Your email configuration is valid!")
        print("Email verification should work correctly.")
    else:
        print("❌ There are issues with your email configuration.")
        print("Please fix the issues mentioned above to enable email sending.")
        print("\nIn development mode, verification codes will be printed to the console.")
    print("=" * 60)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
