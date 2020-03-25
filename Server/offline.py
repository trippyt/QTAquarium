import os
import pandas
from AquariumHardware2 import Hardware
import requests.exceptions
from loguru import logger
import asyncio
import time

hardware = Hardware()


class OfflineFunctions:
    def __init__(self):
        self.utc_now = pandas.Timestamp.utcnow()
        self.temp_c = hardware.read_temperature("temp_tank")
        self.csv = RotatingCsvData(columns=['timestamp', 'temp'])

    def check_server(self):
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

    def monitor_temperature(self):
        while True:
            logger.debug(f"Current Offline Temperature: {self.temp_c}")
            self.csv.append_row(timestamp=pandas.Timestamp.utcnow(), temp=self.temp_c)


class RotatingCsvData:
    def __init__(self, file_name='graph_data.csv', columns=None):
        self.columns = columns
        self.file_name = file_name
        self.df = None
        self.load_graph_data()

    def save_graph_data(self):
        self.df.to_csv(self.file_name, index=False)

    def load_graph_data(self):
        if not os.path.isfile(self.file_name):
            logger.info("File Not Found")
            self.df = pandas.DataFrame(columns=self.columns)
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
                self.df = pandas.DataFrame(columns=self.columns)
                self.save_graph_data()

    def append_row(self, **kwargs):
        self.df = self.df.append(columns=self.columns)
        self.save_graph_data()

        """
        add new data to dataframe here
        example for measuring temp:
          csv = RotatingCsvData(columns=['timestamp', 'temp'])
          temp_c = hardware.read_temperature("temp_tank")[0]
          csv.append_row(timestamp=pandas.Timestamp.utcnow(), temp=temp_c)

        in the above example, kwargs will be a dictionary:
        { 'timestamp': ...,
          'temp': ... }
        """


    def data_rotation(self):
        pass

def server_check_ready(start):
  # determine if server check should be done
  if time.now() - start > some_threshold: # this could be the exponential backoff
    return True
  return False

if __name__ == '__main__':
    offline_funcs = OfflineFunctions()
    start = time.now()
    while True:
        if server_check_ready(start):
            offline_funcs.check_server()
        offline_funcs.monitor_temperature()
        time.sleep(2)