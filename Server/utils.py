import asyncio
import time
import logging
from BaseFunctions import AquariumController
ac = AquariumController
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s,%(msecs)d %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)


def start_calibration(pump_type: str):
    try:
        cal_time = None
        ac.notification_led_pulse()
        ac.button_state()
        logging.log(f"Running {pump_type}")
        logging.log(f"{pump_type}                      Calibration started.")
        ac.notification_led_flash()
        start = time.time()
        ac.pump_on(pump_type)
        ac.button_state()
        logging.log(f"Stopping {pump_type}")
        logging.log(f"{pump_type}                      Calibration finished.")
        end = time.time()
        ac.pump_off()
        cal_time = round(end - start, 2)
        co2_per_ml = round(cal_time/10, 2)
        logging.log(cal_time)
        ac.notification_led_stop()
    except:
        pass


async def stop_pump(pump_type: str):
    logging.log(f"Stopping {pump_type} Pump")
    ac.pump_off(pump_type)
