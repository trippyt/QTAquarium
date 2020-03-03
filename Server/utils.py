import asyncio
import time
import logging
from AquariumHardware import Hardware as Ac
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s,%(msecs)d %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)


class CalibrationCancelled (Exception):
    pass


controller = Ac()


async def start_calibration(pump_type: str):
    try:
        await controller.notification_led_pulse()
        controller.button_state()
        await controller.notification_led_flash()
        controller.calibrate_pump(pump_type)
        await controller.notification_led_stop()
    except CalibrationCancelled:
        print("!Calibration was Cancelled!")

def stop_calibration(pump_type: str):
    controller.stop_calibration()


def cal_status(pump_type: str):
    controller.calibration_status()



def tank_temperature():
    temp_c, temp_f = controller.read_temperature("temp_tank")
    return round(temp_c, 2)


def alert_data(ht, lt):
    controller.alert_data(ht, lt)


def email_alert():
    pass


def newRatios(ratio_results: str):
    controller.ratios(ratio_results)


def load():
    return controller.load()
