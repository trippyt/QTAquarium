from routes import app
from loguru import logger
import requests.exceptions


def server_check():
    try:
        r = requests.get('http://192.168.1.33:5000')
        r.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        logger.exception("Down")
    except requests.exceptions.HTTPError:
        logger.exception("4xx, 5xx")
    else:
        logger.debug("All good!")  # Proceed to do stuff with `r`
    return r.raise_for_status()


def start_server():
    if __name__ == '__main__':
        app.run("0.0.0.0")


start_server()
print(server_check())
