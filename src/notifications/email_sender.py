import os
import resend
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY")
        if self.api_key:
            resend.api_key = self.api_key
        else:
            logger.warning("RESEND_API_KEY not found. Email notifications disabled.")

    def send_alert_email(self, to_email: str, company: str, keyword: str, pressure_score: float):
        if not self.api_key: return
        
        try:
            params = {
                "from": "AI Intel Engine <alerts@re-sent.com>", # Use Resend's default or verified domain
                "to": [to_email],
                "subject": f"🚨 CRITICAL ALERT: {company} - {keyword.upper()} Surge",
                "html": f"""
                <h2>Critical Issue Detected</h2>
                <p>Our Pressure Radar has detected a significant surge in negative feedback for <strong>{company}</strong>.</p>
                <ul>
                    <li><strong>Keyword:</strong> {keyword}</li>
                    <li><strong>Pressure Score:</strong> {pressure_score:.2f}x normal baseline</li>
                </ul>
                <p>Immediate investigation is recommended.</p>
                <br/>
                <a href="https://your-app-url.com" style="background: #e74c3c; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Dashboard</a>
                """
            }
            resend.Emails.send(params)
            logger.info(f"Alert email sent to {to_email}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
