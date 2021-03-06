import asyncio
import time
import os
import json
import csv
import git
from loguru import logger
import pandas
from filelock import Timeout, FileLock


from time import gmtime, strftime
from AquariumHardware2 import Hardware
from email_alert import EmailAlerts

import sqlite3
from sqlite3 import Error


class CalibrationCancelled (Exception):
    pass


class AquariumController:

    def __init__(self):
        logger.info("=" * 125)
        logger.info("Initializing".center(125))
        logger.info("=" * 125)
        self.load_data()
        self.load_config()
        self.hw_controller = Hardware()
        self.email = EmailAlerts()
        self.temp_c, self.temp_f = self.hw_controller.read_temperature("temp_tank")
        self.file_name = 'graph_data.csv'
        lock_path = self.file_name+".lock"
        self.lock = FileLock(lock_path)

        self.con = self.sql_connection()
        self.cursorObj = self.con.cursor()

        self.calibration_data = {
                "Co2 Calibration Data": {},
                "Fertilizer Calibration Data": {},
                "Water Conditioner Calibration Data": {},
            }
        self.ratio_data = {
            "Tank Size": {},
            "Co2 Ratio": {},
            "Fertilizer Ratio": {},
            "Water Conditioner Ratio": {},
        }
        self.setting_data = {
            "Network": {},
            "Temperature Alerts": {},
            "Email Alert": {}
        }

        self.cal_status = ["Success", "Failed", "In Progress", "None"]

        self.network_config = {
            "sender_email": {},
            "target_email": {},
            "password_email": {},
            "service_email": {},
            "alert_limit": {}
        }
        self.alert_counter = {}

    async def start_calibration(self, pump_type: str):
        try:
            '''asyncio.create_task(self.hw_controller.notification_led_pulse())
            self.hw_controller.button_state()
            asyncio.create_task(self.hw_controller.notification_led_flash())
            self.calibrate_pump(pump_type)
            self.hw_controller.notification_led_stop()
            '''
            await self.hw_controller.notification_led_pulse()
            self.hw_controller.button_state()
            await self.hw_controller.notification_led_flash()
            self.calibrate_pump(pump_type)
            self.hw_controller.notification_led_stop()
        except CalibrationCancelled:
            logger.info("!Calibration was Cancelled!")

    def calibrate_pump(self, pump_type):
        logger.info(f"Running {pump_type} Pump\n"
                    f"{pump_type}", "Calibration started".center(125))
        self.calibration_status(pump_type, self.cal_status[2])
        start = time.time()
        self.hw_controller.pump_on(pump_type)
        self.hw_controller.button_state()
        logger.info(f"Stopping {pump_type}\n"
                    f"{pump_type}", "Calibration finished.".center(125))
        self.calibration_status(pump_type, self.cal_status[0])
        end = time.time()
        self.hw_controller.pump_off(pump_type)
        cal_time = round(end - start, 2)
        per_ml = round(cal_time / 10, 2)
        logger.info(type(cal_time))
        logger.info(f"{pump_type} Runtime: {cal_time}")
        self.calibration_data[f"{pump_type} Calibration Data"].update(
            {
                "Time per 10mL": cal_time,
                "Time per 1mL": per_ml
            }
        )
        self.save()

    def stop_calibration(self, pump_type: str):
        self.hw_controller.stop_calibration()

    def cal_status(self, pump_type: str):
        self.hw_controller.calibration_status()

    def tank_temperature(self):
        temp_c, temp_f = self.hw_controller.read_temperature("temp_tank")
        try:
            ht = self.setting_data["Temperature Alerts"]["High Temp"]
            lt = self.setting_data["Temperature Alerts"]["Low Temp"]
            ht_checked = self.setting_data["Temperature Alerts"]["High Enabled"]
            lt_checked = self.setting_data["Temperature Alerts"]["Low Enabled"]
            if ht_checked == '2':
                if temp_c > float(ht):
                    logger.critical("HIGH TEMP ALERT!!!".center(125))
                    cur_temp = temp_c
                    high_temp_threshold = ht
                    self.email.high_temp_alert_example(cur_temp, high_temp_threshold)
            if lt_checked == '2':
                if temp_c < float(lt):
                    logger.critical("LOW TEMP ALERT!!!".center(125))
        except KeyError:
            logger.warning("No Temperature Alert Data")
        return round(temp_c, 2)

    def email_test(self):
        logger.info("=" * 125)
        self.email.msg_format(alert_type='EMAIL TEST', variable_data=None, custom_msg=self.email.templates.test_msg())

        logger.info("=" * 125)

    def email_ht_alert(self):
        logger.info("=" * 125)
        logger.info("HT Alert Email Function".center(125))
        logger.info("=" * 125)
        data = {
            "Current Temperature": self.temp_c,
            "Current Threshold": self.setting_data["Temperature Alerts"]["High Temp"]
        }
        send = self.email.email_builder(alert_type='High Temperature', alert_data=data)
        logger.info("=" * 125)
    """
    def alert_counters(self, alert_type):
        name = f"{alert_type}" + " counter"
        #dict = self.alert_counter[""]
        if name in self.alert_counter.keys():
            for value in name:
                self.alert_counter[(alert_type + " counter")].update(
                    {
                        f"{name}": int(value)+1,
                    }
                )
            self.save_config()
    """

    def calibration_status(self, pump_type, cal_status):
        logger.info(f"pump: {pump_type}, status: {cal_status}")
        return pump_type, cal_status

    def ratioequals(self, ratio_results):
        logger.info("ratio equals function")
        logger.info(f"values {ratio_results}")
        new_ratio = ('Tank', 'Co2_ratio', 'Co2_water', 'Fertilizer_ratio', 'Fertilizer_water', 'WaterConditioner_ratio'\
                                        , 'WaterConditioner_water')

        zipratio = zip(new_ratio, ratio_results)
        ratiodict = dict(zipratio)
        for value in ['Co2', 'Fertilizer', 'WaterConditioner']:
            logger.info(type(value))
            ratio = float(ratiodict[value + '_ratio'])
            water = float(ratiodict[value + '_water'])
            tank = float(ratiodict['Tank'])
            try:
                dosage = ratio * tank / water
            except ZeroDivisionError:
                dosage = 0
            ratiodict[value + '_dosage'] =  "{:.2f}".format(float(dosage))
            #if dosage != 0 else 0
            self.ratio_data = ratiodict
        logger.info(f"Dict Data: {ratiodict}")
        self.save()


    def ratios(self, ratio_results):
        logger.info(f"Ratio: {ratio_results}")
        logger.info('Tank Size: {} Litres,\n'
         'Co2 Concentrate: {} mL, Co2 to Water: {} Litres,\n'
         'Fertilizer Concentrate: {} mL, Fertilizer to Water: {} Litres,\n'
         'WaterConditioner Concentrate: {} mL, WaterConditioner to Water: {} Litres'.format(
            *ratio_results))
        self.ratioequals(ratio_results)

    def alert_data(self, ht: int, lt: int, ht_enabled, lt_enabled):
        logger.info("New Alert Set")
        logger.info(f"High Temperature: {ht} Enabled:{ht_enabled}")
        logger.info(f"Low Temperature: {lt} Enabled:{lt_enabled}")
        self.setting_data["Temperature Alerts"].update(
            {
                "High Temp": ht,
                "High Enabled": ht_enabled,
                "Low Temp": lt,
                "Low Enabled": lt_enabled
            }
        )
        self.save()

    def save(self):
        data = {
            "Setting Data": self.setting_data,
            "Ratio Data": self.ratio_data,
            "Calibration Data": self.calibration_data,
            # "Schedule Data": schedule_data,
            # "Dosage Data": dosage_data,
            # "Light Hour Data": light_hour_data
        }
        with open('data.txt', 'w') as json_file:
            json_file.write(json.dumps(data, indent=4))
        logger.info("Settings Updated")

    def save_config(self):
        logger.info(f"Before updating config: {self.network_config}")
        config_data = {
            "network_config": self.network_config,
            "alert_counters": self.alert_counter,
        }
        try:
            with open('config.json', 'w') as json_data_file:
                json_data_file.write(json.dumps(config_data, indent=4))
            logger.info(f"Email Details Saved")
        except:
            logger.exception(f" Email Details not Saved")
        logger.info(f"After updating config_data: {config_data}")
        logger.info(f"After updating config: {self.network_config}")

    def save_email(self, email_user: str, service_email: str, password_email):
        logger.info("=" * 125)
        logger.info(f"Email Address Updated".center(125))
        logger.info("=" * 125)
        if "@" not in email_user:
            logger.info(f"adding {service_email} to {email_user}")
            email_user = email_user.strip() + service_email.strip()
        else:
            logger.info(f"Email already has '@' ")
        self.network_config.update(
            {
                "sender_email": "aquariumcontrollerpi@gmail.com",
                "target_email": email_user.strip(),
                "password_email": password_email,
                "service_email": service_email.strip(),
                #"alert_limit": alert_limit,
            }
        )

        logger.info(f"{email_user}")
        logger.info(f"Email Pass: {password_email}")
        #logger.info(f"Alert Limit: {alert_limit} Per Day")
        self.save_config()
        logger.info("=" * 125)

    def saveEmail_limit(self, alert_limit: int):
        logger.info("=" * 125)
        logger.info(f"Email Alert Limit Updated".center(125))
        logger.info("=" * 125)
        self.network_config.update(
            {
                "alert_limit": alert_limit,
            }
        )
        logger.info(f"Alert Limit: {alert_limit} Per Day")
        self.save_config()
        logger.info("=" * 125)

    def load_data(self):
        logger.info("=" * 125)
        logger.info("Loading 'data.txt' From Local Path")
        try:
            if os.path.isfile('data.txt'):
                with open('data.txt', 'r') as json_file:
                    data = json.loads(json_file.read())
                    logger.success("'data.txt' Loaded")
                    logger.debug(f"'data.txt' contents: {data}")
                    logger.debug("Assigning Data Values from 'data.txt")
                    self.ratio_data = data["Ratio Data"]
                    self.calibration_data = data["Calibration Data"]
                    self.setting_data = data["Setting Data"]
                    #self.setting_data = data["Temperature Alerts"]
                    # conversion_values
                    # schedule_data
                    # light_hour_data
                    # dosage_data = data["Dosage Data"]
                    logger.success("Data Values Updated")
                    return data
        except (KeyError, ValueError, TypeError):
            logger.critical("Couldn't Load 'data.txt'")
            logger.exception("Traceback")
        logger.info("=" * 125)

    def load_config(self):
        try:
            logger.info("=" * 125)
            logger.info("Loading config_data")
            if os.path.isfile('config.json'):
                with open('config.json', 'r') as json_data_file:
                    config_data = json.loads(json_data_file.read())
                    logger.success("'config.json' Loaded")
                    logger.debug(f"'config.json' contents: {config_data}")
                    try:
                        logger.info("Assigning Config Values from 'config.json'")
                        self.network_config = config_data["network_config"]
                        self.alert_counter = config_data["alert_counters"]
                        logger.success("Config Values Updated")
                    except (KeyError, ValueError, TypeError):
                        logger.warning("Couldn't Assign Values from 'config.json")
        except json.JSONDecodeError.with_traceback():
            logger.critical("Couldn't Load 'config_data")
        logger.info("=" * 125)
        return config_data

    def get_csv(self):
        try:
            with self.lock.acquire(timeout=1):
                with open('graph_data.csv', 'r') as csv_file:
                    return csv_file.read()
        except Timeout:
            logger.warning("Another instance of this application currently holds the lock.")

    def get_db(self):
        db = self.cursorObj.execute("SELECT * FROM tank_temperature")
        return db

    def sql_connection(self):
        try:
            con = sqlite3.connect('AquaPiDB.db')
            logger.debug("Connection is established to Database")
            return con
        except Error:
            logger.exception(Error)

    def update(self):
        g = git.cmd.Git("/home/pi/QTAquarium/")
        msg = g.pull()
        logger.info(f"Repo Status: {msg}")



