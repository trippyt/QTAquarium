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
        cal_time = None
        controller.notification_led_pulse()
        controller.button_state()
        controller.notification_led_flash()
        controller.calibrate()
        controller.notification_led_stop()
    except CalibrationCancelled:
        print("!Calibration was Cancelled!")


def start_pump(pump_type: str):
    logging.info(f"Starting {pump_type} Pump")
    controller.pump_on(pump_type)


def stop_pump(pump_type: str):
    logging.info(f"Stopping {pump_type} Pump")
    controller.pump_off(pump_type)
