import server
from AquariumHardware2 import Hardware
import requests.exceptions
from loguru import logger
import asyncio

hardware = Hardware()


def check_server():
    try:
        r = requests.get('http://example.com')
        r.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        logger.exception("Down")
    except requests.exceptions.HTTPError:
        logger.exception("4xx, 5xx")
    else:
        logger.info("All good!")  # Proceed to do stuff with `r`


async def monitor_temperature():
    temp_c = hardware.read_temperature("temp_tank")
    logger.debug(f"Current Offline Temperature: {temp_c}")
    await asyncio.sleep(2)


def monitor_loop():
    while True:
        await monitor_temperature()


server.start()
check_server()
monitor_loop()
