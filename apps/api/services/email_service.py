import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.hostinger.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "465"))
        self.smtp_user = os.getenv("SMTP_USER", "legacy2lake@over55it.com")
        self.smtp_pass = os.getenv("SMTP_PASS")
        self.sender_email = os.getenv("SENDER_EMAIL", self.smtp_user)
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")

    def send_email(self, recipient_email: str, subject: str, body: str, is_html: bool = False) -> bool:
        """Sends an email using configured SMTP settings."""
        if not self.smtp_pass:
            print("[EMAIL] Error: SMTP_PASS not configured in environment")
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = recipient_email
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "html" if is_html else "plain"))

            # Use SSL for port 465
            if self.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls() # For 587

            server.login(self.smtp_user, self.smtp_pass)
            server.send_message(msg)
            server.quit()
            
            print(f"[EMAIL] Successfully sent email to {recipient_email}")
            return True
        except Exception as e:
            print(f"[EMAIL] Failed to send email: {e}")
            return False

    def send_invitation(self, username: str, email: str, password: str):
        """Sends an invitation email with login credentials."""
        subject = "Your access to Legacy2Lake: Enterprise Modernization Platform"
        
        body = f"""
        <html>
        <body style="font-family: sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; rounded: 8px;">
                <h2 style="color: #0891b2;">Welcome to Legacy2Lake</h2>
                <p>Hello <strong>{username}</strong>,</p>
                <p>An administrator has created an account for you in the Legacy2Lake platform. You can now access the system using the following temporary credentials:</p>
                
                <div style="background: #f4f4f4; padding: 15px; border-radius: 4px; border-left: 4px solid #0891b2; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Username:</strong> {username}</p>
                    <p style="margin: 5px 0;"><strong>Temporary Password:</strong> <code style="background: #e5e7eb; padding: 2px 4px; border-radius: 3px;">{password}</code></p>
                </div>
                
                <p>Please log in and <strong>change your password immediately</strong> from your profile settings.</p>
                
                <p style="margin-top: 30px;">
                    <a href="{self.frontend_url}/login" style="background: #0891b2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">Log in to Legacy2Lake</a>
                </p>
                
                <hr style="border: 0; border-top: 1px solid #eee; margin-top: 40px;">
                <p style="font-size: 11px; color: #999;">This is an automated message. Please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """
        return self.send_email(email, subject, body, is_html=True)

    def send_password_reset(self, username: str, email: str, password: str):
        """Sends a password reset email with new temporary credentials."""
        subject = "Legacy2Lake: Password Reset Notification"
        
        body = f"""
        <html>
        <body style="font-family: sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; rounded: 8px;">
                <h2 style="color: #0891b2;">Password Reset Successful</h2>
                <p>Hello <strong>{username}</strong>,</p>
                <p>An administrator has reset your password for the Legacy2Lake platform. Your new temporary credentials are:</p>
                
                <div style="background: #f4f4f4; padding: 15px; border-radius: 4px; border-left: 4px solid #0891b2; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Username:</strong> {username}</p>
                    <p style="margin: 5px 0;"><strong>Temporary Password:</strong> <code style="background: #e5e7eb; padding: 2px 4px; border-radius: 3px;">{password}</code></p>
                </div>
                
                <p>Please log in and <strong>change your password immediately</strong> from your profile settings.</p>
                
                <p style="margin-top: 30px;">
                    <a href="{self.frontend_url}/login" style="background: #0891b2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">Log in to Legacy2Lake</a>
                </p>
                
                <hr style="border: 0; border-top: 1px solid #eee; margin-top: 40px;">
                <p style="font-size: 11px; color: #999;">If you did not request this reset, please contact your administrator.</p>
            </div>
        </body>
        </html>
        """
        return self.send_email(email, subject, body, is_html=True)
