#import server
#from routes import app
from AquariumHardware2 import Hardware
import requests.exceptions
from loguru import logger
import asyncio

hardware = Hardware()


async def check_server():
    while True:
        try:
            r = requests.get('http://192.168.1.33:5000')
            r.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            logger.exception("Down")
        except requests.exceptions.HTTPError:
            logger.exception("4xx, 5xx")
        else:
            logger.info("All good!")  # Proceed to do stuff with `r`
            logger.debug(r.text)
            #await asyncio.sleep(3)


async def monitor_temperature():
    while True:
        temp_c = hardware.read_temperature("temp_tank")
        logger.debug(f"Current Offline Temperature: {temp_c}")
        await asyncio.sleep(2)


async def monitor_loop():
    await asyncio.gather(monitor_temperature())


if __name__ == '__main__':
    asyncio.run(monitor_loop())
    #loop = asyncio.get_event_loop()
    #loop.run_until_complete(monitor_loop())
    #loop.close()


#server.start()
#check_server()
#monitor_loop()
