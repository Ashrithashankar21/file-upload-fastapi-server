import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.load_env import get_env_variable

smtp_server = get_env_variable("SMTP_SERVER")
smtp_port = get_env_variable("SMTP_PORT")
smtp_user = get_env_variable("SMTP_USER")
smtp_password = get_env_variable("SMTP_PASSWORD")
sender_email = get_env_variable("SENDER_EMAIL")
receiver_email = get_env_variable("RECEIVER_EMAIL")


def send_email(event_type, file_path):
    """Send an email notification."""
    subject = f"File System Event: {event_type}"
    time_stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    body = f"Event Type: {event_type}\nFile Path:\
 {file_path}\nTimestamp: {time_stamp}"

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            send_mail(server, msg)

    except Exception as e:
        print(f"Failed to send email: {e}")


def send_mail(server, msg):
    server.starttls()
    server.login(smtp_user, smtp_password)
    text = msg.as_string()
    server.sendmail(sender_email, receiver_email, text)