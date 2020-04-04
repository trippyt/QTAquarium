import os
import pandas
from AquariumHardware2 import Hardware
import requests.exceptions
from loguru import logger
import datetime
import schedule
import time
import subprocess
import psutil

hardware = Hardware()


class OfflineFunctions:
    def __init__(self):
        self.__sysStat = None
        self.utc_now = pandas.Timestamp.utcnow()
        self.temp_c = hardware.read_temperature("temp_tank")[0]
        self.csv = RotatingCsvData(columns=['timestamp', 'temp'])
        self.server_boot_time = datetime.datetime.utcnow()

    def start_server(self):
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cmdline']):
            if 'server.py' in ''.join(proc.info['cmdline']):
                logger.warning("Killing Server Process")
                proc.kill()
        subprocess.Popen(['python3', 'server.py'])
        logger.success("Server Started")
        logger.debug(f"Server Process Started at {self.server_boot_time}")

    def check_server(self):
        try:
            r = requests.get('http://0.0.0.0:5000')
            r.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
            server_runtime = datetime.datetime.utcnow() - self.server_boot_time
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            logger.critical("Down")
            self.start_server()
        except requests.exceptions.HTTPError:
            logger.warning("4xx, 5xx")
        else:
            # logger.info("All good!")  # Proceed to do stuff with `r`
            logger.success(f"Server Runtime: {server_runtime}")
            logger.debug(r.text)

    def getSysStat(self):
        """

        # Get system statistics. This function will always get the latest system stats.
        # Returns:
        #     sysStat (SysStat): System statistics.

        sysStat = self.__sysStat
        sysStat.upTime = time.time() - psutil.boot_time()
        sysStat.cpuStat = self.__queryCPUStat()
        sysStat.memoryStat = self.__queryMemoryStat()
        sysStat.gpuStats = self.__queryGPUStats()
        sysStat.gpuCount = len(sysStat.gpuStats)
        sysStat.processStat, sysStat.processStats = self.__queryProcessStats()
        sysStat.processCount = len(sysStat.processStats)
        sysStat.gpuProcessStats = self.__queryGPUProcessStats()
        sysStat.gpuProcessCount = len(sysStat.gpuProcessStats)
        sysStat.networkStats = self.__queryNetworkStats()
        sysStat.networkCount = len(sysStat.networkStats)
        return self.__sysStat
    """

    def monitor_temperature(self):
        temp = hardware.read_temperature("temp_tank")[0]
        # logger.debug(f"Current Offline Temperature: {temp}")
        self.csv.append_row(timestamp=pandas.Timestamp.utcnow(), temp=temp)


class RotatingCsvData:
    def __init__(self, file_name='graph_data.csv', columns=None):
        self.columns = columns
        self.file_name = file_name
        self.df = None
        self.last_df_save = datetime.datetime.utcnow()
        self.load_graph_data()
        self.save_interval = datetime.timedelta(seconds=10)
        self.line_limit = 300
        self.line_count = None

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
        self.line_count = len(self.df)
        elapsed_time = datetime.datetime.utcnow() - self.last_df_save
        if self.line_count > self.line_limit:
            self.data_rotation()
            """
            logger.success("Rotating CSV data")
            logger.debug(f"CSV Line Count: {self.line_count}")
            """
        else:
            logger.warning("CSV Data not Rotated")
            logger.debug(f"CSV Line Count: {self.line_count}")
        if elapsed_time > self.save_interval:
            self.save_graph_data()
            """
            logger.success("CSV Updated")
            logger.debug(f"Time Elapsed: {elapsed_time}")
            logger.debug(f"CSV Line Count: {self.line_count}")
        else:
            logger.warning("Not enough time passed")
            logger.debug(f"Time Elapsed: {elapsed_time}")
            """

    def data_rotation(self):
        row_remove = len(self.df) - self.line_limit
        self.df.drop(range(0, row_remove), inplace=True)
        self.df.reset_index(drop=True)
        self.line_count = len(self.df)


offline_funcs = OfflineFunctions()
schedule.every(2).minutes.do(offline_funcs.check_server)
schedule.every().second.do(offline_funcs.monitor_temperature)
while True:
    schedule.run_pending()
