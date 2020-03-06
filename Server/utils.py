import asyncio
import time
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

        async def start_calibration(self, pump_type: str):
            try:
                await self.hw_controller.notification_led_pulse()
                self.hw_controller.button_state()
                await self.hw_controller.notification_led_flash()
                self.calibrate_pump(pump_type)
                await self.hw_controller.notification_led_stop()
            except CalibrationCancelled:
                print("!Calibration was Cancelled!")

        def calibrate_pump(self, pump_type):
            logging.info(f"Running {pump_type} Pump")
            logging.info(f"{pump_type}                      Calibration started.")
            self.calibration_status(pump_type, self.cal_status[2])
            start = time.time()
            self.pump_on(pump_type)
            self.button_state()
            logging.info(f"Stopping {pump_type}")
            logging.info(f"{pump_type}                      Calibration finished.")
            self.calibration_status(pump_type, self.cal_status[0])
            end = time.time()
            self.pump_off(pump_type)
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

        def alert_data(self,ht, lt):
            self.hw_controller.alert_data(ht, lt)

        def email_alert(self):
            pass

        def newRatios(self,ratio_results: str):
            self.hw_controller.ratios(ratio_results)

    def load(self):
        if os.path.isfile('data.txt'):
            with open('data.txt', 'r') as json_file:
                data = json.loads(json_file.read())
                print("Loading Saved Data")
                print(f"Loading Data...{data}")
                self.ratio_data = data["Ratio Data"]
                # temperature_data = data["Temperature Data"]
                # conversion_values
                # schedule_data
                # calibration_data = data["Calibration Data"]
                # light_hour_data
                # dosage_data = data["Dosage Data"]
                return data
