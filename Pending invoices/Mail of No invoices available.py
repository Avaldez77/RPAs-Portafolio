import os
import sys
import ssl
import smtplib
import urllib3

from email.message import EmailMessage

urllib3.disable_warnings()
context = ssl.create_default_context()

# --------------------------------------------------------------------------------------------
# CONFIG (SANITIZED) - Ajusta en tu ambiente real
# --------------------------------------------------------------------------------------------

CREDENTIALS_FILE = r"\\FILESERVER\Shared\RPA\secrets\smtp_password.txt"

SMTP_HOST = "smtp.company.internal"
SMTP_PORT = 25
SMTP_USERNAME = "service.account"

FROM_ADDR = "service.account@company.com"
TO_ADDRS = [
    "recipient1@company.com",
    "recipient2@company.com",
    "recipient3@company.com",
]

print("NEW EMAIL MODULE --------------------------------------------------------------------------------------------")

# --------------------------------------------------------------------------------------------
# READ PASSWORD (SANITIZED)
# --------------------------------------------------------------------------------------------
try:
    with open(CREDENTIALS_FILE, encoding="utf-8") as f:
        SMTP_PASSWORD = f.read().strip()
except FileNotFoundError:
    print("Error: Credentials file not found. Update CREDENTIALS_FILE.")
    sys.exit(1)

# --------------------------------------------------------------------------------------------
# EMAIL BUILD (GENERIC TEXT, NO INTERNAL NAMES)
# --------------------------------------------------------------------------------------------
msg = EmailMessage()
msg["Subject"] = "Notification - No shipping documents available (Excel)"
msg["From"] = FROM_ADDR
msg["To"] = TO_ADDRS

msg.set_content(
"""
Dear Customer,

This is to inform you that there are currently no shipping documents available.

Reference IDs:
N/A
"""
)

msg.add_alternative(
"""\
<html>
  <body>
    <p>Dear Customer,</p>
    <p>We would like to inform you that there are currently no shipping documents available at this time.</p>
    <p>If you have any questions or concerns, please let us know.</p>
    <hr />
  </body>
</html>
""",
subtype="html"
)

# --------------------------------------------------------------------------------------------
# SEND EMAIL (SANITIZED)
# --------------------------------------------------------------------------------------------
try:
    s = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    s.login(SMTP_USERNAME, SMTP_PASSWORD)
    print("Sending email...")
    s.send_message(msg)
    print("EMAIL SENT SUCCESSFULLY!")
    s.quit()
except smtplib.SMTPException as e:
    print(f"SMTP Error: {e}")