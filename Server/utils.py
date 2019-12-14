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


def start_calibration(pump_type: str):
    try:
        cal_time = None
        Ac.notification_led_pulse()
        Ac.button_state()
        logging.log(f"Running {pump_type}")
        logging.log(f"{pump_type}                      Calibration started.")
        Ac.notification_led_flash()
        start = time.time()
        Ac.pump_on(pump_type)
        Ac.button_state()
        logging.log(f"Stopping {pump_type}")
        logging.log(f"{pump_type}                      Calibration finished.")
        end = time.time()
        Ac.pump_off()
        cal_time = round(end - start, 2)
        co2_per_ml = round(cal_time/10, 2)
        logging.log(cal_time)
        Ac.notification_led_stop()
    except CalibrationCancelled:
        print("!Calibration was Cancelled!")


async def stop_pump(pump_type: str):
    logging.log(f"Stopping {pump_type} Pump")
    Ac.pump_off(pump_type)
