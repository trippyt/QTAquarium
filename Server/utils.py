import asyncio
import time
import logging
from BaseFunctions import AquariumController as Ac
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s,%(msecs)d %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)


class CalibrationCancelled (Exception):
    pass


controller = Ac()


def start_calibration(pump_type: str):
    try:
        controller.notification_led_pulse()
        controller.button_state()
        controller.notification_led_flash()
        controller.calibrate_pump(pump_type)
        controller.notification_led_stop()
    except CalibrationCancelled:
        print("!Calibration was Cancelled!")


def tank_temperature():
    temp_c, temp_f = controller.read_temperature("temp_tank")
    return round(temp_c, 2)


def alert_data(ht, lt):
    controller.alert_data(ht, lt)


def email_alert():
    pass
