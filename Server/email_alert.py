import smtplib
import json


class EmailAlerts:
    def __init__(self):
        msg = None

    def aqua_pi_status(self):
        pass

    with open('config.json', 'r') as json_data_file:
        data = json.load(json_data_file)

    sender = data["network_config"]["sender_email"]
    target = data["network_config"]["target_email"]
    password = data["network_config"]["password_email"]
    msg = data["email_msg"]

    TO = target
    SUBJECT = 'AquaPi Alert!'
    TEXT = msg

    gmail_sender = sender
    gmail_passwd = password

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login(gmail_sender, gmail_passwd)

    BODY = '\r\n'.join(['To: %s' % TO,
                        'From: %s' % gmail_sender,
                        'Subject: %s' % SUBJECT,
                        '', TEXT])

    try:
        server.sendmail(gmail_sender, [TO], BODY)
        print('email sent')
    except Exeption as e:
        print('error sending mail')
        print(e)

    server.quit()
