import smtplib
import json


class EmailAlerts:
    def __init__(self):
        with open('config.json', 'r') as json_data_file:
            config = json.load(json_data_file)
        with open('data.txt', 'r') as txt_data_file:
            data = json.load(txt_data_file)
        try:
            self.sender = config["network_config"]["sender_email"]
            self.target = config["network_config"]["target_email"]
            self.password = config["network_config"]["password_email"]
            self.high_temp_threshold = data["Setting Data"]["Temperature Alerts"]["High Temp"]
        except:
            print("oops")
        #self.msg = config["email_msg"]

        self.templates = EmailTemplates()

    def aqua_pi_status_report(self, config):
        self.msg = config["email_msg"]["Status Report"]
        self.email_send()

    def aqua_pi_alert(self, config, alert_type):
        print("Building Email")
        self.msg = config["email_msg"]["alerts"][alert_type]
        self.email_send()

    def high_temp_alert_example(self, cur_temp, high_temp_threshold):
        self.msg = self.templates.high_temp().format(cur_temp=cur_temp, high_temp_threshold=high_temp_threshold)
        self.email_send()

    def email_test(self):
        self.msg = self.templates.email_test()

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
        except:
            print('error sending mail')
        server.quit()

class EmailTemplates:
    def __init__(self):
        pass

    def high_temp(self):
        m = """==================================================
Warning High Temperature
==================================================
Current Temperature: {cur_temp},
Current High Threshold: {high_temp_threshold}

please do the following checks:
- check temperature probe is in tank water
- check temperature probe cable
- check temperature probe connection
- check heater power
=================================================="""
        return m

    def low_temp(self):
        m = """==================================================
Warning Low Temperature
==================================================
Current Temperature: {},
Current Low Threshold: {}

please do the following checks:
- check temperature probe is in tank water
- check temperature probe cable
- check temperature probe connection
- check heater power
=================================================="""
        return m

    def email_test(self):
        m = """==================================================
Email Test
==================================================
Hi from Test
=================================================="""
        return m