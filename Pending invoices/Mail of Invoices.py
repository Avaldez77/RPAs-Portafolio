import os
import re
import sys
import ssl
import smtplib
import urllib3
import pandas as pd
import xlwings as xw

from datetime import datetime
from email.message import EmailMessage

urllib3.disable_warnings()
context = ssl.create_default_context()

# --------------------------------------------------------------------------------------------
# CONFIG (SANITIZED)
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

ATTACHMENTS_DIR = r"C:\Temp"
FILE_PREFIX_TO_REMOVE = "C810_SR_"
FILE_EXT = ".XLS"

EXCEL_PATH = r"C:\Path\To\Your\Project\SR.xlsx"
EXCEL_SHEET = "Sheet1"

REQUIRED_COLUMNS = ["sr no.", "created date"]

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
# FILE DISCOVERY
# --------------------------------------------------------------------------------------------
today = datetime.now().strftime("%Y-%m-%d")

files = [
    f for f in os.listdir(ATTACHMENTS_DIR)
    if f.endswith(FILE_EXT)
    and datetime.fromtimestamp(os.path.getctime(os.path.join(ATTACHMENTS_DIR, f))).strftime("%Y-%m-%d") == today
]

file_contents = files
filenames_wo_ext = [os.path.splitext(f)[0] for f in files]
clean_names = [re.sub(FILE_PREFIX_TO_REMOVE, "", name) for name in filenames_wo_ext]
print("Files without extension:", clean_names)

# --------------------------------------------------------------------------------------------
# READ EXCEL DATES (xlwings)
# --------------------------------------------------------------------------------------------
app = None
wb = None
try:
    app = xw.App(visible=False)
    wb = app.books.open(EXCEL_PATH)
    sheet = wb.sheets[EXCEL_SHEET]

    df = sheet.used_range.options(pd.DataFrame, header=1, index=False).value
    df.columns = [str(col).replace("\n", "").lower().strip() for col in df.columns]

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        print(f"Error: Missing required columns: {missing}")
        sys.exit(1)

    df_unique_dates = df[["created date"]].drop_duplicates()
    dates = df_unique_dates["created date"].tolist()

    fixed_dates = []
    for d in dates:
        if isinstance(d, datetime):
            fixed_dates.append(d)
        else:
            try:
                fixed_dates.append(pd.to_datetime(d).to_pydatetime())
            except Exception:
                pass

    dates_str = ", ".join([d.strftime("%Y-%m-%d") for d in fixed_dates]) if fixed_dates else "N/A"
    print(f"Dates: {dates_str}")

finally:
    if wb is not None:
        wb.close()
    if app is not None:
        app.quit()

print("NEW EMAIL MODULE --------------------------------------------------------------------------------------------")

# --------------------------------------------------------------------------------------------
# EMAIL BUILD (NO 'SEM' ANYWHERE)
# --------------------------------------------------------------------------------------------
msg = EmailMessage()

msg["Subject"] = f"SR Notification - Excel Invoices {dates_str}"  # <- sin SEM
msg["From"] = FROM_ADDR
msg["To"] = TO_ADDRS

msg.set_content(
f"""
Dear Customer,

This is to inform you that the shipping document is attached in Excel format.
Please review the details and let us know if you have any issue.

SR number:
{", ".join(clean_names) if clean_names else "N/A"}
"""
)

msg.add_alternative(
f"""\
<html>
  <body>
    <p>Dear Customer,</p>
    <p>This is to inform you that the shipping document is attached in Excel format.</p>
    <p>Please review the details and let us know if you have any issue.</p>
    <p><b>SR number:</b></p>
    <p>{", ".join(clean_names) if clean_names else "N/A"}</p>
    <hr>
  </body>
</html>
""",
subtype="html"
)

# --------------------------------------------------------------------------------------------
# ATTACHMENTS
# --------------------------------------------------------------------------------------------
if file_contents:
    for file_name in file_contents:
        full_path = os.path.join(ATTACHMENTS_DIR, file_name)
        with open(full_path, "rb") as f:
            file_data = f.read()

        msg.add_attachment(
            file_data,
            maintype="application",
            subtype="octet-stream",
            filename=file_name
        )
else:
    print("No files to attach.")

# --------------------------------------------------------------------------------------------
# SEND EMAIL
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