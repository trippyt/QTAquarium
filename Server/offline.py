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
from filelock import Timeout, FileLock
from hurry.filesize import size
import w1thermsensor

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
            r = requests.get('http://localhost:5000')
            r.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
            server_uptime = datetime.datetime.utcnow() - self.server_boot_time
            #raspberry_pi_runtime = datetime.datetime.utcnow() - psutil.boot_time()
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            logger.critical("Server is Down")
            self.start_server()
        except requests.exceptions.HTTPError:
            logger.warning("4xx, 5xx")
        else:
            # logger.info("All good!")  # Proceed to do stuff with `r`
            logger.success(f"Server Up-time: {server_uptime}")
            #logger.debug(f"Raspberry Pi Runtime: {raspberry_pi_runtime}")
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
        try:
            temp = hardware.read_temperature("temp_tank")[0]
            temp_rounded = round(temp, 2)
            path = 'graph_data.csv'
            csv_bytes = os.path.getsize(path)
            csv_size = size(csv_bytes)
            logger.debug(f"Current Offline Temperature: {temp}")
            logger.debug(f"Rounded Temperature: {temp_rounded}")
            logger.debug(f"CSV Data File Size: {csv_size}")
            self.csv.append_row(timestamp=pandas.Timestamp.utcnow(), temp=temp_rounded)
        except w1thermsensor.errors.SensorNotReadyError:
            logger.critical("Sensor Not Ready")
        except:
            logger.exception("Temperature Monitoring Failed")


class RotatingCsvData:
    def __init__(self, file_name='graph_data.csv', columns=None):
        self.columns = columns
        self.file_name = file_name
        self.df = None
        self.last_df_save = datetime.datetime.utcnow()
        self.load_graph_data()
        self.save_interval = datetime.timedelta(seconds=10)
        self.line_limit = 36000
        self.line_count = None
        lock_path = self.file_name+".lock"
        self.lock = FileLock(lock_path)

    def save_graph_data(self):
        try:
            logger.debug(f"Acquiring Lock")
            self.lock.acquire()
            logger.success(f"File: {self.file_name}, Locked")
            self.last_df_save = datetime.datetime.utcnow()
            self.df.to_csv(self.file_name, index=False)
            logger.success("CSV Updated")
        except Timeout:
            logger.warning("Another instance of this application currently holds the lock.")
        finally:
            self.lock.release()
            logger.success(f"File: {self.file_name}, UnLocked")



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
        else:  # if line count is lower than the limit, it wont rotate the data
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
try:
    while True:
        schedule.run_pending()
except:
    logger.exception("Schedule error")
