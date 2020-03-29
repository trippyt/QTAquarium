import os
import pandas
from AquariumHardware2 import Hardware
import requests.exceptions
from loguru import logger
import datetime
import asyncio
import time

hardware = Hardware()


class OfflineFunctions:
    def __init__(self):
        self.utc_now = pandas.Timestamp.utcnow()
        self.temp_c = hardware.read_temperature("temp_tank")[0]
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
            temp = hardware.read_temperature("temp_tank")[0]
            logger.debug(f"Current Offline Temperature: {temp}")
            self.csv.append_row(timestamp=pandas.Timestamp.utcnow(), temp=temp)


class RotatingCsvData:
    def __init__(self, file_name='graph_data.csv', columns=None):
        self.columns = columns
        self.file_name = file_name
        self.df = None
        self.last_df_save = None
        self.load_graph_data()

    def save_graph_data(self):
        self.last_df_save = datetime.datetime.utcnow()
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
        self.df = self.df.append(kwargs, ignore_index=True)
        if self.last_df_save is None:
            self.last_df_save = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
        elapsed_time = datetime.datetime.utcnow() - self.last_df_save
        if elapsed_time > datetime.timedelta(minutes=5):
            self.save_graph_data()
            logger.success("CSV Updated")
            logger.debug(f"Time Elapsed: {elapsed_time}")
        else:
            logger.warning("Not enough time passed")
            logger.debug(f"Time Elapsed: {elapsed_time}")
        if self.df.index.min():
            self.data_rotation()
            logger.debug("Rotating CSV data")
            logger.debug(self.df.index.min())
        else:
            logger.warning("CSV Data not Rotated")
            logger.debug(self.df.index.min())
        # check if data should be rotated
        #    self.data_rotation()

    def data_rotation(self):
        if self.df.index.min():
            self.df.drop(0)
            self.df.reset_index(drop=True)
            self.save_graph_data()


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