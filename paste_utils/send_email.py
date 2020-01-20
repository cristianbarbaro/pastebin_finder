from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from paste_utils import config
import os


def get_contacts(filename):
    emails = []
    with open(filename, mode='r', encoding='utf-8') as contacts_file:
        for a_contact in contacts_file:
            emails.append(a_contact)
    return emails


def send_email(message, subject):

    s = smtplib.SMTP(host=config.SMTP_HOST, port=config.SMTP_PORT)
    s.starttls()
    s.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)

    dirname = os.path.dirname(__file__)
    emails = get_contacts(os.path.join(dirname, 'recipients.txt'))
    
    for email in emails:
        msg = MIMEMultipart() 

        msg['From'] = config.EMAIL_ADDRESS
        msg['To'] = email
        msg['Subject'] = subject

        msg.attach(MIMEText(message, 'plain'))

        s.send_message(msg)

        del msg

