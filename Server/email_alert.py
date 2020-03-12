import smtplib
import json


class EmailAlerts:
    def __init__(self):
        with open('config.json', 'r') as json_data_file:
            data = json.load(json_data_file)

        self.sender = data["network_config"]["sender_email"]
        self.target = data["network_config"]["target_email"]
        self.password = data["network_config"]["password_email"]
        self.msg = data["email_msg"]

    def aqua_pi_status_report(self, data):
        self.msg = data["email_msg"]["status"]
        self.email_send()

    def email_send(self):
        to = self.target
        subject = 'AquaPi Alert!'
        text = self.msg

        gmail_sender = self.sender
        gmail_passwd = self.password

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_sender, gmail_passwd)

        body = '\r\n'.join(['To: %s' % to,
                            'From: %s' % gmail_sender,
                            'Subject: %s' % subject,
                            '', text])

        try:
            server.sendmail(gmail_sender, [to], body)
            print('email sent')
        except Exeption as e:
            print('error sending mail')
            print(e)

        server.quit()
