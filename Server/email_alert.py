import smtplib
import json
import logging as l


class EmailAlerts:
    def __init__(self):
        self.network_config = {}
        self.email_msg = None
        with open('config.json', 'r') as json_data_file:
            self.config = json.load(json_data_file)
        with open('data.txt', 'r') as txt_data_file:
            data = json.load(txt_data_file)
        try:
            self.sender = self.config["network_config"]["sender_email"]
            self.target = self.config["network_config"]["target_email"]
            self.password = self.config["network_config"]["password_email"]
            self.high_temp_threshold = data["Setting Data"]["Temperature Alerts"]["High Temp"]
        except:
            print("oops")
        # self.msg = config["email_msg"]
        # self.alert_type = ["Test", ""]
        self.templates = EmailTemplates()

    def low_temp_alert(self):
        self

    def aqua_pi_status_report(self):
        self.msg = self.templates.status_report()
        self.email_send(alert_type='Status Report')

    def high_temp_alert(self, cur_temp, high_temp_threshold):
        self.msg = self.templates.high_temp().format(cur_temp=cur_temp, high_temp_threshold=high_temp_threshold)
        self.email_send(alert_type='High Temperature Alert!')

    def email_test(self):
        self.msg = self.templates.email_test()
        self.email_send(alert_type='TEST Alert!')

    def email_send(self, alert_type):
        print(f"Email Built: \n"
              f"{self.email_msg}")
        to = self.target
        subject = f"AquaPi {alert_type}"

        gmail_sender = self.sender
        gmail_passwd = self.password

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_sender, gmail_passwd)

        body = '\r\n'.join(['To: %s' % to,
                            'From: %s' % gmail_sender,
                            'Subject: %s' % subject,
                            '', self.email_msg])

        try:
            server.sendmail(gmail_sender, [to], body)
            print('email sent')
            self.alert_email_counter(alert_type)
        except Exception as e:
            l.exception("error sending mail")
            l.exception(e)
            l.info(type(self.config))
            l.info(f"Config: {self.config}")
        server.quit()

    def alert_email_counter(self, alert_type):
        if (alert_type + " counter") in self.network_config:
            self.network_config[(alert_type + "counter")] += 1
        else:
            self.network_config[(alert_type + "counter")] = 1

        self.save_config()

    def save_config(self):
        email_data = {
            "network_config": self.network_config,
        }
        try:
            with open('config.json', 'w') as json_data_file:
                json_data_file.write(json.dumps(email_data, indent=4))
            l.info(f"Email Details Saved")
        except:
            l.exception(f" Email Details not Saved")

    def msg_format(self, alert_type, variable_data, custom_msg):
        self.email_msg = '\r\n'.join([' %s Alert' % alert_type,
                                      'Data: %s' % variable_data,
                                      'Message: %s' % custom_msg,
                                      ''])
        self.email_send(alert_type)


class EmailTemplates:
    def __init__(self):
        pass

    def temperature_msg(self):
        m = """please do the following checks:
- check temperature probe is in tank water
- check temperature probe cable
- check temperature probe connection
- check heater power"""
        return m

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

    def status_report(self):
        m = """
==================================================
            AquaPi Status Report:
==================================================
Current Temperature: {},
Current Low Threshold: {},
Current High Threshold: {},
Email High Temp Alert Enabled: {},
Email Low Temp Alert Disabled: {},
Calibration Data: {},
last calibration run: {},
last does run: {},
last feed run: {},
last cycle: {},
last reboot: {},
current uptime: {},
last reboot cause? ie error, forced, or user requested: {}, 
Ratio Data: {},
temperature graphs: {},
doses graphs: {},
feed graphs: {},
water change graphs: {},
up time graphs: {},
connectivity graphs: {},
=================================================="""


"""
==================================================
Warning Low Temperature                                         # Alert title
==================================================
Current Temperature: {},                                        # Variable Data
Current Low Threshold: {}

please do the following checks:                                 # Custom message defined by alert
- check temperature probe is in tank water
- check temperature probe cable
- check temperature probe connection
- check heater power
=================================================="""


def email_test(self):
    m = """==================================================
Email Test
==================================================
Hi from Test
=================================================="""
    return m
