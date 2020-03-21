import smtplib
import json
import datetime
from loguru import logger


class EmailAlerts:
    def __init__(self):
        self.sender = None
        self.target = None
        self.password = None
        self.alert_counter = None
        self.high_temp_threshold = None
        self.alert_limit = None
        self.refresh_data()
        self.email_msg = None
        self.cur_date = datetime.datetime.utcnow().strftime('%d-%m-%Y')
        self.cur_time = datetime.datetime.utcnow().strftime('%H:%M:%S')
        self.prev_date = {}
        self.prev_time = {}
        self.alerts_sent = None
        self.send = None

        self.templates = EmailTemplates()

    def refresh_data(self):
        logger.info("=" * 125)
        logger.info("Refreshing Email Data".center(125))
        logger.info("=" * 125)
        try:
            logger.info("Loading Email Data from 'config.json'")
            with open('config.json', 'r+') as json_data_file:
                self.config_data = json.load(json_data_file)
                self.sender = self.config_data["network_config"]["sender_email"]
                self.target = self.config_data["network_config"]["target_email"]
                self.password = self.config_data["network_config"]["password_email"]
                self.alert_counter = self.config_data["alert_counters"]
                self.alert_limit = int(self.config_data["network_config"]["alert_limit"])
            logger.success("Email Data Loaded from 'config.json'")
            logger.debug(f"Sender: {self.sender}")
            logger.debug(f"Target: {self.target}")
            logger.debug(f"Password: {self.password}")
            logger.debug(f"Max Daily Alert Limit: {self.alert_limit}")
        except (KeyError, ValueError, TypeError):
            logger.warning("Couldn't Load Email Data from 'config.json'")
        try:
            logger.info("Loading Alert Values from 'data.txt'")
            with open('data.txt', 'r') as txt_data_file:
                self.data = json.load(txt_data_file)
                self.high_temp_threshold = self.data["Setting Data"]["Temperature Alerts"]["High Temp"]
            logger.success("Alert Values Loaded from 'data.txt'")
            logger.debug(f"High Temp Threshold: {self.high_temp_threshold}")
        except (KeyError, ValueError, TypeError):
            logger.warning("Couldn't Load Email Data from 'config.json'")
        logger.info("=" * 125)

    def refresh_time_var(self, alert_type):
        try:
            self.prev_date = self.alert_counter[f"{alert_type} Last Date Called"]
            self.prev_time = self.alert_counter[f"{alert_type} Last Time Called"]
            self.alerts_sent = self.alert_counter[f"{alert_type}"]
        except KeyError:
            self.prev_date = self.cur_date
            self.prev_time = self.cur_time
            self.alerts_sent = 0

    def low_temp_alert(self):
        self

    def aqua_pi_status_report(self):
        self.msg = self.templates.status_report()
        self.email_send(alert_type='Status Report')

    def high_temp_alert(self, cur_temp, high_temp_threshold):
        self.msg = self.templates.high_temp().format(cur_temp=cur_temp, high_temp_threshold=high_temp_threshold)
        self.email_send(alert_type='High Temperature Alert!')

    def email_test(self):
        self.email_send(alert_type='TEST Alert!')

    def email_send(self, alert_type):
        logger.info(f"Config counters before refresh: {self.alert_counter}")
        self.refresh_data()
        self.refresh_time_var(alert_type)
        logger.info(f"Config counters after refresh: {self.alert_counter}")
        logger.info("=" * 125)
        logger.info("Email Builder Function".center(125))
        logger.info("=" * 125)
        to = self.target
        subject = f"AquaPi {alert_type}"
        gmail_sender = self.sender
        gmail_passwd = self.password
        logger.debug(f"Email Built: \n"
                     F"\n"
                     f"To:{to}\n"
                     f"From: {gmail_sender}\n"
                     f"Subject: {subject}\n"
                     F"\n"
                     f"{self.email_msg}")

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_sender, gmail_passwd)

        body = '\r\n'.join(['To: %s' % to,
                            'From: %s' % gmail_sender,
                            'Subject: %s' % subject,
                            '', self.email_msg])
        self.send = server.sendmail(gmail_sender, [to], body)

        try:
            if alert_type in self.alert_counter.keys():
                logger.info(f"Alerts Limited to: {self.alert_limit} per Day\n"
                            f"Alert :'{alert_type}'\n"
                            f" Last Sent date: {self.prev_date}  Last Sent Time: {self.prev_time}\n"
                            f"   Current date: {self.cur_date}     current time: {self.cur_time}\n"
                            f"Config counters: {self.alert_counter}")
                logger.info("_" * 125)
                logger.info(f"alerts_sent: {self.alerts_sent} >= alert_limit: {self.alert_limit}")
                if self.alerts_sent >= self.alert_limit:
                    logger.info(f"Email Alert Limit Reached!")
                    if self.cur_date > self.prev_date:
                        logger.info("Today is a New Day")
                        self.alert_counter[f"{alert_type}"] = 0
                        logger.info(f"{alert_type} Alert counter Reset!!\n"
                                    f"Sending Email Alert")
                        # self.send()
                        logger.info(f"{alert_type} Alert counter: {self.alerts_sent}")
                        self.alert_email_counter(alert_type)
                    elif self.cur_date == self.prev_date:
                        logger.info("its the same day")
                    else:
                        logger.info(f"Too Many {alert_type} Alerts Today\n"
                              f"Already Sent: {self.alerts_sent} The Limit is: {self.alert_limit}\n"
                              f"Email Alert NOT Sent!")
                elif self.alerts_sent < self.alert_limit:
                    self.alert_email_counter(alert_type)
                    self.refresh_time_var(alert_type)
                    logger.info(f"Alerts under the Limit")
                    logger.info(f"Last Date Sent: {self.prev_date}\n"
                                f"Last Time Sent: {self.prev_time}\n"
                                f"Times Sent Today: {self.alerts_sent}")
                else:
                    self.refresh_time_var(alert_type)
                    logger.error(f"{alert_type} Alert)".center(125))
                    logger.info(f"Last Date Sent: {self.prev_date}\n"
                          f"Last Time Sent: {self.prev_time}\n"
                          f"Times Sent Today: {self.alerts_sent}")
            else:
                logger.warning(f"Alert Type: {alert_type}\n"
                               f"Counter Not Found, Creating Counter")
                #self.alert_counter["alert_counters"].update(
                self.alert_counter.update(
                    {
                        f"{alert_type}": 0,
                        f"{alert_type} Last Date Called": "Never",
                        f"{alert_type} Last Time Called": "None"
                    }
                )
                logger.info(f"{alert_type} Counter Created")

        except Exception as e:
            logger.exception("With Building Email")
            logger.exception(e)
        server.quit()
        logger.info("=" * 125)
        return self.alert_counter

    def alert_email_counter(self, alert_type):
        logger.info("=" * 125)
        logger.info("Alert Counter Function".center(125))
        logger.info("=" * 125)
        logger.info(f"Alert Type: {alert_type}")
        logger.info(f"config before counter: {self.alert_counter}")
        # cur_datetime = datetime.datetime.utcnow().strftime('%m-%d-%Y - %H:%M:%S')
        try:
            if alert_type in self.alert_counter.keys():
                self.refresh_time_var(alert_type)
                logger.info(f"Updating {alert_type} Counter")
                self.alert_counter[f"{alert_type}"] += 1
                self.alert_counter[f"{alert_type} Last Date Called"] = self.cur_date
                self.alert_counter[f"{alert_type} Last Time Called"] = self.cur_time
            else:
                logger.info(f"{alert_type} not in dict")
                self.alert_counter[f"{alert_type}"] = 1
        except Exception as e:
            logger.exception(e)
            logger.info("Ooops")
        logger.info(f"config after counter: {self.alert_counter}")
        logger.info("=" * 125)
        return self.alert_counter

    def msg_format(self, alert_type, variable_data, custom_msg):
        self.email_msg = '\r\n'.join([' %s Alert' % alert_type,
                                      'Data: %s' % variable_data,
                                      'Message:',
                                      '%s' % custom_msg,
                                      ''])
        self.email_send(alert_type)
        return self.alert_counter


class EmailTemplates:
    def __init__(self):
        pass

    def test_msg(self):
        m = """This is a Test!
- Sent from AquaPi"""
        return m

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
