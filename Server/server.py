from routes import app
from loguru import logger
import requests.exceptions

def is_production():
    """ Determines if app is running on the production server or not.
    Get Current URI.
    Extract root location.
    Compare root location against developer server value 127.0.0.1:5000.
    :return: (bool) True if code is running on the production server, and False otherwise.
    """
    try:


        try:
            r = requests.get('http://example.com')
            r.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            logger.debug("Down")
        except requests.exceptions.HTTPError:
            logger.debug("4xx, 5xx")
        else:
            logger.debug("All good!")  # Proceed to do stuff with `r`
    except RuntimeError:
        logger.exception(f"ooops2")


print(is_production())
if __name__ == '__main__':
    app.run("0.0.0.0")
