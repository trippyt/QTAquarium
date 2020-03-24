from routes import app
from quart import Quart, request
from loguru import logger


def is_production():
    """ Determines if app is running on the production server or not.
    Get Current URI.
    Extract root location.
    Compare root location against developer server value 127.0.0.1:5000.
    :return: (bool) True if code is running on the production server, and False otherwise.
    """
    try:
        root_url = request.url_root
        developer_url = 'http://0.0.0.0:5000/'
        return root_url != developer_url
    except RuntimeError:
        logger.exception(f"ooops2")


print(is_production())
if __name__ == '__main__':
    app.run("0.0.0.0")
