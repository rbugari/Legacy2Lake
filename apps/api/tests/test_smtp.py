import smtplib
import os
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

def test_smtp():
    host = os.getenv("SMTP_HOST", "smtp.hostinger.com")
    port = int(os.getenv("SMTP_PORT", "465"))
    user = os.getenv("SMTP_USER", "legacy2lake@over55it.com")
    password = os.getenv("SMTP_PASS")
    sender = os.getenv("SENDER_EMAIL", user)
    
    print(f"--- SMTP Diagnostic ---")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"User: {user}")
    print(f"Has Password: {'Yes' if password else 'No'}")
    
    if not password or password == "[YOUR_PASSWORD_HERE]":
        print("ERROR: SMTP_PASS is missing or still set to placeholder.")
        return

    try:
        print("\nAttempting connection...")
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            server = smtplib.SMTP(host, port, timeout=10)
            server.starttls()
            
        print("Connected. Attempting login...")
        server.login(user, password)
        print("Login successful.")
        
        print("Attempting to send test message...")
        msg = MIMEText("This is a diagnostic test from Legacy2Lake.")
        msg["Subject"] = "SMTP Diagnostic Test"
        msg["From"] = sender
        msg["To"] = user
        
        server.send_message(msg)
        server.quit()
        print("Test email sent successfully to yourself!")
        
    except Exception as e:
        print(f"\nFAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_smtp()
