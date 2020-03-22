import smtplib
import json
import datetime
from loguru import logger


class EmailAlerts:
    def __init__(self):
        self.target = None
        self.sender = None
        self.password = None
        self.cur_date = datetime.datetime.utcnow().strftime('%d-%m-%Y')
        self.cur_time = datetime.datetime.utcnow().strftime('%H:%M:%S')
        self.alert_counters = {}
        self.network_data = {}
        self.message = EmailData()

    def email_builder(self, alert_type, alert_data):
        self._load_variable_data(alert_type)
        #variable_data =

        custom_msg = self.message.custom_msg_builder(alert_type)
        email_msg = '\r\n'.join([' %s Alert' % alert_type,
                                 'Data: %s' % alert_data,
                                 'Message:',
                                 '%s' % custom_msg,
                                 ''])
        self._email_sender(alert_type, email_msg)

    def _load_variable_data(self, alert_type):
        try:
            with open('config.json', 'r') as json_data_file:
                data = json.load(json_data_file)
                self.alert_counters = data["Alert Counters"]
                self.network_data = data["network_config"]
                self.target = self.network_data["target_email"]
                self.sender = self.network_data["sender_email"]
                self.password = self.network_data["password_email"]

                if alert_type not in self.alert_counters.keys():
                    self.alert_counters[f"{alert_type}"] = {
                        f"Alert Count": 0,
                        f"Last Date Called": "Never",
                        f"Last Time Called": "Never"
                    }

                logger.debug(f"{data}")
        except:
            logger.exception(f"Couldn't Load Variable data from 'config.json'")
            return self.alert_counters

    def _update_counter(self, alert_type):
        data = {
            "network_config": self.network_data,
            "Alert Counters": self.alert_counters
        }
        logger.info(f"Updating {alert_type} Counter")
        self.alert_counters[f"{alert_type}"]["Alert Count"] += 1
        self.alert_counters[f"{alert_type}"]["Last Date Called"] = self.cur_date
        self.alert_counters[f"{alert_type}"]["Last Time Called"] = self.cur_time
        counters = self.alert_counters[f"{alert_type}"]
        logger.debug(f"{counters}")
        with open('config.json', 'w') as json_data_file:
            json_data_file.write(json.dumps(data, indent=4))

    def _email_sender(self, alert_type, email_msg):
        alert_limit = self.network_data["alert_limit"]
        prev_date = self.alert_counters[f"{alert_type}"]["Last Date Called"]
        to = self.target
        subject = f"AquaPi {alert_type}"
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(self.sender, self.password)
        body = '\r\n'.join(['To: %s' % to,
                            'From: %s' % self.sender,
                            'Subject: %s' % subject,
                            '', email_msg])
        logger.debug(f"Email Built:\n"
                     f"{body}")
        if alert_type in self.alert_counters.keys():
            alerts_sent = self.alert_counters[f"{alert_type}"]["Alert Count"]
            if alerts_sent >= alert_limit:
                logger.warning(F"{alert_type} Email Limit Reached")
                logger.debug(f"Limit: {alert_limit} Sent: {alerts_sent}")
                if self.cur_date > prev_date:
                    logger.success(f"New day..Resetting {alert_type} Alert Count")
                    self.alert_counters[f"{alert_type}"]["Alert Count"] = 0
                    # server.sendmail(self.sender, [to], body)
                    logger.success(f"{alert_type} Alert Sent")
                    self._update_counter(alert_type)
                elif self.cur_date == prev_date:
                    logger.critical(f"Can't Send anymore '{alert_type}' Alerts Today")
                    now = datetime.datetime.now()
                    midnight = datetime.datetime.strptime(f"{self.cur_date} 00:00:01", "%d-%m-%Y %H:%M:%S") + datetime\
                        .timedelta(days=1)
                    logger.debug(f"now = {now}     reset = {midnight}")
                    tomorrow = str(midnight - now).split('.')[0]
                    logger.debug(f"Time Until Reset: {tomorrow}")
            elif alerts_sent < alert_limit:
                # server.sendmail(self.sender, [to], body)
                logger.success(f"{alert_type} Alert Sent")
                self._update_counter(alert_type)
        else:
            logger.exception(f"Couldn't send {alert_type} Email Alert")
        server.quit()


class EmailData:
    def __init__(self):
        pass

    def custom_msg_builder(self, alert_type):
        a = alert_type
        if a == 'EMAIL TEST':
            return self.test_msg()
        elif a == 'High Temperature':
            return self.temperature_msg()
        elif a == 'Low Temperature':
            return self.temperature_msg()
        elif a == 'Status Report':
            return self.status_report()

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
