# import server
# from routes import app
import os
import pandas
from AquariumHardware2 import Hardware
import requests.exceptions
from loguru import logger
import asyncio

hardware = Hardware()


class OfflineFunctions:
    def __init__(self):
        self.utc_now = pandas.Timestamp.utcnow()
        self.temp_c = hardware.read_temperature("temp_tank")
        self.csv = RotatingCsvData
        self.csv = RotatingCsvData(columns=['timestamp', 'temp'])
        pass

    async def check_server(self):
        while True:
            try:
                r = requests.get('http://192.168.1.33:5000')
                r.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                logger.exception("Down")
            except requests.exceptions.HTTPError:
                logger.exception("4xx, 5xx")
            else:
                # logger.info("All good!")  # Proceed to do stuff with `r`
                logger.debug(r.text)
                # await asyncio.sleep(3)

    async def monitor_temperature(self):
        while True:
            logger.debug(f"Current Offline Temperature: {self.temp_c}")
            self.csv = RotatingCsvData(columns=self.columns)
            await asyncio.sleep(2)

    async def monitor_loop(self):
        await asyncio.gather(self.monitor_temperature())

    if __name__ == '__main__':
        asyncio.run(monitor_loop())
        # loop = asyncio.get_event_loop()
        # loop.run_until_complete(monitor_loop())
        # loop.close()


class RotatingCsvData:
    def __init__(self, file_name='graph_data.csv', columns=None):
        self.columns = None
        self.file_name = file_name
        self.df = None
        self.load_graph_data()

    def save_graph_data(self):
        self.df.to_csv(self.file_name, index=False)

    def load_graph_data(self):
        if not os.path.isfile(self.file_name):
            logger.info("File Not Found")
            self.df = pandas.DataFrame(columns=['timestamp', 'temp'])
            self.save_graph_data()
            logger.info("File Created")
        else:
            logger.info("File Found")
            try:
                self.df = pandas.read_csv(self.file_name)
                logger.info("CSV Data Loaded")
                logger.info(f"{self.df}")
            except pandas.errors.EmptyDataError:
                logger.info("CSV has been populated")
                self.df = pandas.DataFrame(columns=['timestamp', 'temp'])
                self.save_graph_data()

    def data_rotation(self):
        pass
