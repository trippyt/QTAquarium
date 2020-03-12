import asyncio
import time
import os
import json
import logging
from AquariumHardware2 import Hardware
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s,%(msecs)d %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)


class CalibrationCancelled (Exception):
    pass


class AquariumController:

    def __init__(self):
        self.hw_controller = Hardware()
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

        self.email_data = {
            "Email User": {},
            "Email Service": {}
        }

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
            print("!Calibration was Cancelled!")

    def calibrate_pump(self, pump_type):
        logging.info(f"Running {pump_type} Pump")
        logging.info(f"{pump_type}                      Calibration started.")
        self.calibration_status(pump_type, self.cal_status[2])
        start = time.time()
        self.hw_controller.pump_on(pump_type)
        self.hw_controller.button_state()
        logging.info(f"Stopping {pump_type}")
        logging.info(f"{pump_type}                      Calibration finished.")
        self.calibration_status(pump_type, self.cal_status[0])
        end = time.time()
        self.hw_controller.pump_off(pump_type)
        cal_time = round(end - start, 2)
        per_ml = round(cal_time / 10, 2)
        print(type(cal_time))
        logging.info(f"{pump_type} Runtime: {cal_time}")
        self.calibration_data[f"{pump_type} Calibration Data"].update(
            {
                "Time per 10mL": cal_time,
                "Time per 1mL": per_ml
            }
        )
        self.save()

    def stop_calibration(self, pump_type: str):
        self.hw_controller.stop_calibration()

    def cal_status(self,pump_type: str):
        self.hw_controller.calibration_status()

    def tank_temperature(self):
        temp_c, temp_f = self.hw_controller.read_temperature("temp_tank")
        return round(temp_c, 2)

    def email_alert(self):
        pass

    def calibration_status(self, pump_type, cal_status):
        logging.info(f"pump: {pump_type}, status: {cal_status}")
        return pump_type, cal_status

    def ratioequals(self, ratio_results):
        print("ratio equals function")
        print(f"values {ratio_results}")
        new_ratio = ('Tank', 'Co2_ratio', 'Co2_water', 'Fertilizer_ratio', 'Fertilizer_water', 'WaterConditioner_ratio'\
                                        , 'WaterConditioner_water')

        zipratio = zip(new_ratio, ratio_results)
        ratiodict = dict(zipratio)
        for value in ['Co2', 'Fertilizer', 'WaterConditioner']:
            print(type(value))
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
        print(f"Dict Data: {ratiodict}")
        self.save()
        #for key in ratiodict:
        #    ratio_data["Ratio Data"].update(
        #        f"{key}"
        #    )

    def ratios(self, ratio_results):
        logging.info(f"Ratio: {ratio_results}")
        logging.info('Tank Size: {} Litres,\n'
         'Co2 Concentrate: {} mL, Co2 to Water: {} Litres,\n'
         'Fertilizer Concentrate: {} mL, Fertilizer to Water: {} Litres,\n'
         'WaterConditioner Concentrate: {} mL, WaterConditioner to Water: {} Litres'.format(
            *ratio_results))
        self.ratioequals(ratio_results)

    def alert_data(self, ht: int, lt: int):
        logging.info("New Alert Set")
        logging.info(f"High Temperature: {ht}")
        logging.info(f"Low Temperature: {lt}")
        self.setting_data["Temperature Alerts"].update(
            {
                "High Temp": ht,
                "Low Temp": lt
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
        logging.info("Settings Updated")

    def save_email(self, email_user: str, email_service: str):
        email_data = {
            "Email Data": {
                "Email User": email_user,
                "Email Service": email_service
            }
        }
        logging.info(f"Email Address Updated")
        logging.info(f"{email_user}{email_service}")
        try:
            with open('config.json', 'w') as json_data_file:
                json_data_file.write(json.dumps(email_data, indent=4))
            logging.info(f"Email Details Saved")
        except:
            logging.exception(f" Email Details not Saved")

    def load(self):
        try:
            if os.path.isfile('data.txt'):
                with open('data.txt', 'r') as json_file:
                    data = json.loads(json_file.read())
                    print("Loading Saved Data")
                    self.ratio_data = data["Ratio Data"]
                    self.calibration_data = data["Calibration Data"]
                    # temperature_data = data["Temperature Data"]
                    # conversion_values
                    # schedule_data
                    # light_hour_data
                    # dosage_data = data["Dosage Data"]
        except:
            logging.exception("Couldn't Load Data.txt")
        try:
            if os.path.isfile('config.json'):
                with open('config.json', 'r') as json_data_file:
                    email_data = json.loads(json_data_file.read())
                    print("Loading Email Data")
                    self.email_data = email_data["network_config"]
            return data, email_data
        except:
            logging.exception("Couldn't Load config.json")
