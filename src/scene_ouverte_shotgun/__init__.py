import logging
import os
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from bs4 import BeautifulSoup

KNOWN_DATES = ["12 juin 2024", "23 octobre 2024"]
FROM = os.getenv("FROM")
RECIPIENTS = os.getenv("RECIPIENTS").split(",")
ICLOUD_APP_PASSWORD = os.getenv("ICLOUD_APP_PASSWORD")

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def main() -> int:
    res = requests.get("https://www.le-brise-glace.com/programmation/a-venir/")
    if not res.ok:
        logging.info("Could not fetch HTML page")
        return 1

    soup = BeautifulSoup(res.text, "html.parser")

    events = soup.find_all("article", role="event")
    for event in events:
        if "ouverte" in event.text and not any(
            date in event.text for date in KNOWN_DATES
        ):
            logging.info("New scène ouverte detected")
            url = event.find("a")["href"]
            send_email(
                subject="Nouvelle scène ouverte détectée!",
                body=url,
                recipient_emails=RECIPIENTS,
            )
            return 0

    logging.info("No new scène ouverte")
    return 0


def send_email(subject, body, recipient_emails):
    # iCloud SMTP server settings
    smtp_server = "smtp.mail.me.com"
    smtp_port = 587
    from_email = FROM
    app_password = ICLOUD_APP_PASSWORD

    # Create the email headers and content
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = ", ".join(recipient_emails)
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:
        # Set up the SMTP server and start TLS
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()

        # Log in to the iCloud account
        server.login(from_email, app_password)

        # Send the email
        server.sendmail(from_email, recipient_emails, msg.as_string())

        # Close the server connection
        server.quit()

        logging.info("Email sent successfully!")
    except Exception as e:
        logging.error(f"Failed to send email. Error: {e}")
