import smtplib
import json
import logging
import datetime


class EmailAlerts:
    def __init__(self):
        self.refresh_data()
        try:
            self.sender = self.config_data["network_config"]["sender_email"]
            self.target = self.config_data["network_config"]["target_email"]
            self.password = self.config_data["network_config"]["password_email"]
            self.alert_counter = self.config_data["alert_counters"]
            self.high_temp_threshold = self.data["Setting Data"]["Temperature Alerts"]["High Temp"]
        except Exception as e:
            logging.exception(e)

        self.load()
        self.email_msg = None
        self.cur_datetime = datetime.datetime.utcnow().strftime('%m-%d-%Y - %H:%M:%S')

        self.templates = EmailTemplates()

    def refresh_data(self):
        try:
            with open('config.json', 'r') as json_data_file:
                self.config_data = json.load(json_data_file)
            logging.info("Config data loaded from 'config.json'")
        except Exception as e:
            logging.exception(e)
        try:
            with open('data.txt', 'r') as txt_data_file:
                self.data = json.load(txt_data_file)
            logging.info("Server data loaded from 'data.txt'")
        except Exception as e:
            logging.exception(e)

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
        self.refresh_data()
        print("=" * 125)
        logging.info("Email Builder Function".center(125))
        print("=" * 125)
        to = self.target
        subject = f"AquaPi {alert_type}"
        gmail_sender = self.sender
        gmail_passwd = self.password
        print(f"Email Built: \n"
              f"To:{to}\n"
              f"From: {gmail_sender}\n"
              f"Subject: {subject}\n"
              f"{self.email_msg}")

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_sender, gmail_passwd)

        body = '\r\n'.join(['To: %s' % to,
                            'From: %s' % gmail_sender,
                            'Subject: %s' % subject,
                            '', self.email_msg])

        try:
            # server.sendmail(gmail_sender, [to], body)
            self.alert_email_counter(alert_type)
            sent = self.alert_counter[f"{alert_type}"]
            prev_datetime = self.config_data["alert_counters"][f"{alert_type} Last on"]
            cur_datetime = datetime.datetime.utcnow().strftime('%m-%d-%Y - %H:%M:%S')
            prev_date = prev_datetime[:10]
            cur_date = cur_datetime[:10]
            prev_time = prev_datetime[13:]
            cur_time = cur_datetime[13:]

            if alert_type in self.alert_counter.keys():
                if sent > 5:
                    print(f"Too many {alert_type} Alerts Called\n"
                          f"{alert_type} Alert Last Sent: {prev_datetime}\n"
                          f"      Comparing current date: {cur_date}     current time:{cur_time}\n"
                          f"             Last Alert date: {prev_date} Last Alert time:{prev_time}")
                    if cur_date > prev_date:
                        print("Today is a New Day")
                    elif cur_date == prev_date:
                        print("its the same day")

                else:
                    print("Sending Email Alert")
                    print(f"{alert_type} Alerts Sent: {sent}")
                    print(f"{alert_type} Alert Last Sent: {prev_datetime}")
        except Exception as e:
            logging.exception("error sending mail")
            logging.exception(e)
        server.quit()
        print("=" * 125)
        return self.alert_counter

    def alert_email_counter(self, alert_type):
        print("=" * 125)
        logging.info("Alert Counter Function".center(125))
        print("=" * 125)
        print(f"Alert Type: {alert_type}")
        print(f"config before counter: {self.alert_counter}")
        cur_datetime = datetime.datetime.utcnow().strftime('%m-%d-%Y - %H:%M:%S')
        try:
            if alert_type in self.alert_counter.keys():
                print(f"Updating {alert_type} Counter")
                self.alert_counter[f"{alert_type}"] += 1
                self.alert_counter[f"{alert_type} Last on"] = cur_datetime
            else:
                print(f"{alert_type} not in dict")
                self.alert_counter[f"{alert_type}"] = 1
        except Exception as e:
            logging.exception(e)
            print("Ooops")
        print(f"config after counter: {self.alert_counter}")
        print("=" * 125)
        return self.alert_counter

    def msg_format(self, alert_type, variable_data, custom_msg):
        self.email_msg = '\r\n'.join([' %s Alert' % alert_type,
                                      'Data: %s' % variable_data,
                                      'Message: %s' % custom_msg,
                                      ''])
        self.email_send(alert_type)
        # return self.email_send(alert_type)
        return self.alert_counter

    def load(self):
        print("=" * 125)
        logging.info("Loading 'config.json'")
        print("=" * 125)
        logging.info("Loading 'data.txt'")
        print("=" * 125)
        print(f"self.config_data: {self.config_data}")
        print("=" * 125)
        print(f"Server data: {self.data}")
        print("=" * 125)
        print(f"Sender: {self.sender}")
        print(f"Target: {self.target}")
        print(f"Password: {self.password}")
        print(f"High Temp Threshold: {self.high_temp_threshold}")
        print("=" * 125)


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
