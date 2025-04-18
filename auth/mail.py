import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def send_email(to_email, student_name, class_name, month=None):
    sender_email = "codeinlastbench@gmail.com"
    sender_password = "atco gdkd whky ezfz"  # App password

    # 🗓️ Use current month if not passed
    month = month or datetime.now().strftime("%B")

    subject = f"📬 School Fee Reminder for {month}"

    # ✅ Plain text fallback
    plain_text = f"""
    Dear {student_name},

    This is a gentle reminder to complete your school fee payment for Class {class_name} for the month of {month}.

    Please pay your Tuition, Exam, Library, and Transport fees at the earliest.

    Thank you,
    School Management
    """

    # ✅ HTML email content
    html_content = f"""
    <html>
    <head>
        <style>
            .email-container {{
                font-family: Arial, sans-serif;
                background-color: #f7f7f7;
                padding: 20px;
            }}
            .email-box {{
                background-color: #ffffff;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
                max-width: 600px;
                margin: auto;
            }}
            .header {{
                font-size: 20px;
                font-weight: bold;
                color: #333;
                margin-bottom: 20px;
            }}
            .body {{
                font-size: 16px;
                color: #444;
                line-height: 1.5;
            }}
            .footer {{
                margin-top: 30px;
                font-size: 14px;
                color: #777;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="email-box">
                <div class="header">Dear {student_name},</div>
                <div class="body">
                    This is a gentle reminder to complete your <strong>school fee payment</strong> for <strong>Class {class_name}</strong> for the month of <strong>{month}</strong>.<br><br>
                    Please pay your <strong>Tuition, Exam, Library</strong>, and <strong>Transport fees</strong> at the earliest to avoid any late charges.
                </div>
                <div class="footer">
                    <br>Thank you,<br>
                    <strong>School Management</strong>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject

    # Attach plain text and HTML
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")
        return False
