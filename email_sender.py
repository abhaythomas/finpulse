"""
email_sender.py — Email Delivery

Sends the HTML report via Gmail SMTP.
Uses App Passwords (not your regular Gmail password) for security.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()


def send_report(html_content: str, subject: str) -> bool:
    """
    Send an HTML email via Gmail SMTP.

    Requires:
    - EMAIL_SENDER: your Gmail address
    - EMAIL_PASSWORD: a Gmail App Password (NOT your regular password)
    - EMAIL_RECEIVER: where to send the report (can be same as sender)
    """
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    receiver = os.getenv("EMAIL_RECEIVER")

    if not all([sender, password, receiver]):
        print("❌ Email credentials not configured. Set EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER in .env")
        # Save report locally as fallback
        with open("latest_report.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("📄 Report saved to latest_report.html instead")
        return False

    # Build email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"FinPulse Agent <{sender}>"
    msg["To"] = receiver

    # Attach HTML content
    msg.attach(MIMEText(html_content, "html"))

    try:
        # Connect to Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())

        print(f"✅ Report sent to {receiver}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("❌ Gmail authentication failed. Make sure you're using an App Password, not your regular password.")
        print("   Go to myaccount.google.com/apppasswords to generate one.")
        return False

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        # Save report locally as fallback
        with open("latest_report.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("📄 Report saved to latest_report.html instead")
        return False
