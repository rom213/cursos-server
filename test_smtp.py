import smtplib
import socket


def check_gmail_user(email):
    try:
        domain = email.split('@')[1]
        # Since I don't have dns.resolver (likely), I might fail here if I rely on it.
        # But wait, looking at pip list, dnspython is NOT installed.
        # So I have to use nslookup or hardcode gmail MX servers for gmail.com
        
        mx_host = 'gmail-smtp-in.l.google.com' 
        # For non-gmail domains (workspaces), this won't work without MX lookup.
        
        if domain != 'gmail.com':
            print("Skipping non-gmail domain for hardcoded test")
            return
            
        server = smtplib.SMTP(mx_host, 25, timeout=5)
        server.set_debuglevel(1)
        server.helo('test.com')
        server.mail('test@test.com')
        code, message = server.rcpt(email)
        server.quit()
        
        print(f"Code: {code}")
        print(f"Message: {message}")
        
    except Exception as e:
        print(f"Error: {e}")

check_gmail_user("yverano248@gmail.com")
