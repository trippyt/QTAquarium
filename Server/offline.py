import server
import requests.exceptions
from loguru import logger


def check_server():
    try:
        r = requests.get('http://example.com')
        r.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        logger.exception("Down")
    except requests.exceptions.HTTPError:
        logger.exception("4xx, 5xx")
    else:
        logger.exception("All good!")  # Proceed to do stuff with `r`


server.start()
check_server()