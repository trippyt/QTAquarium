import os
import pandas
from AquariumHardware2 import Hardware
import requests.exceptions
from loguru import logger
import datetime
import schedule
import functools
import time
import subprocess
import psutil
from filelock import Timeout, FileLock
from hurry.filesize import size
import w1thermsensor
import psycopg2
from psycopg2 import Error

hardware = Hardware()


def alerts(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            import traceback
            logger.debug('LOG: Running function "%s"' % func.__name__)
            logger.exception(traceback.format_exc())

    return wrapper

def job_log(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug('LOG: Running job "%s"' % func.__name__)
        result = func(*args, **kwargs)
        logger.debug('LOG: Job "%s" completed' % func.__name__)
        return result

    return wrapper


"""def catch_exceptions(cancel_on_failure=False):
    def catch_exceptions_decorator(job_func):
        @functools.wraps(job_func)
        def wrapper(*args, **kwargs):
            try:
                return job_func(*args, **kwargs)
            except:
                import traceback
                logger.exception(traceback.format_exc())
                if cancel_on_failure:
                    return schedule.CancelJob
        return wrapper
    return catch_exceptions_decorator"""

class OfflineFunctions:
    def __init__(self):
        self.__sysStat = None
        self.utc_now = pandas.Timestamp.utcnow()
        self.tank_temp_c = 0
        self.tank_temp_f = 0
        self.tank_read_count = 0
        self.tank_read_success = 0
        self.room_read_success = 0
        self.room_read_count = 0
        self.room_temp_c = 0
        self.room_temp_f = 0
        self.room_humidity = 0
        self.ds18b20_reading = False
        self.dht22_reading = False
        self.csv = RotatingCsvData(columns=['timestamp', 'temp'])
        self.server_boot_time = datetime.datetime.utcnow()
        self.datetimenow = datetime.datetime.utcnow()
        self.con = self.sql_connection()

    def start_server(self):
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cmdline']):
            if 'server.py' in ''.join(proc.info['cmdline']):
                logger.warning("Killing Server Process")
                proc.kill()
        subprocess.Popen(['python3', 'server.py'])
        logger.success("Server Started")
        logger.debug(f"Server Process Started at {self.server_boot_time}")

    @job_log
    #@catch_exceptions(cancel_on_failure=True)
    def check_server(self):
        logger.info("Checking Server Status:")
        try:
            r = requests.get('http://localhost:5000')
            r.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
            server_uptime = datetime.datetime.utcnow() - self.server_boot_time
            # raspberry_pi_runtime = datetime.datetime.utcnow() - psutil.boot_time()
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            logger.critical("Server is Down")
            self.start_server()
        except requests.exceptions.HTTPError:
            logger.warning("4xx, 5xx")
        else:
            logger.success("Server Running")
            logger.info(f"Server Up-time: {server_uptime}")
            # logger.debug(f"Raspberry Pi Runtime: {raspberry_pi_runtime}")
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

    def sql_connection(self):
        try:
            con = psycopg2.connect(host="192.168.1.33", database="AquaPiDB", user="postgres", password="aquaPi")
            logger.debug("Connection is established: Database has been created ")
            return con
        except Error:
            logger.exception(Error)

    def sql_tank_table(self, con):
        cursorObj = con.cursor()
        cursorObj.execute("CREATE TABLE tank_temperature(date datetime, time datetime, temperature_c float,"
                          " temperature_f float)")
        con.commit()

    def sql_tank_insert(self, con, entities):
        cursorObj = con.cursor()
        cursorObj.execute(
            '''INSERT INTO tank_temperature (date, temperature_c, temperature_f) VALUES(%s, %s, %s)''',
            entities)
        con.commit()

    def sql_room_insert(selfself, con, entities):
        cursorObj = con.cursor()
        cursorObj.execute(
            '''INSERT INTO room_temperature (date, temperature_c, temperature_f, humidity) VALUES(%s, %s, %s, %s)''',
            entities)
        con.commit()

    def sql_tank_filtered_insert(self, con, entities):
        cursorObj = con.cursor()
        cursorObj.execute(
            '''INSERT INTO filtered_tank_temperature (date, temperature_c, temperature_f) VALUES(%s, %s, %s)''',
            entities)
        con.commit()

    def sql_room_filtered_insert(selfself, con, entities):
        cursorObj = con.cursor()
        cursorObj.execute(
            '''INSERT INTO filtered_room_temperature (date, temperature_c, temperature_f, humidity) VALUES(%s, %s, %s, %s)''',
            entities)
        con.commit()

    """@job_log
    #@catch_exceptions(cancel_on_failure=True)
    def monitor_temperature(self):
        try:
            if not self.ds18b20_reading:
                self.tank_temperature()
            else:
                logger.warning("DS18b20 Already in Use")
        except Exception as error:
            logger.warning(error.args[0])
        try:
            if not self.dht22_reading:
                self.room_temperature()
            else:
                logger.warning("DHT22 Already in Use")
        except Exception as error:
            logger.warning(error.args[0])"""

    @job_log
    def monitor_tank(self):
        try:
            if not self.ds18b20_reading:
                self.tank_temperature()
            else:
                logger.warning("DS18b20 Already in Use")
        except Exception as error:
            logger.warning(error.args[0])

    @job_log
    def monitor_room(self):
        try:
            if not self.dht22_reading:
                self.room_temperature()
            else:
                logger.warning("DHT22 Already in Use")
        except Exception as error:
            logger.warning(error.args[0])

    @alerts
    def tank_temperature(self):
        self.ds18b20_reading = True
        self.datetimenow = datetime.datetime.utcnow()
        count = self.tank_read_count + 1
        self.tank_read_count = count
        logger.info(f"Sensor Read Count - Tank: {self.tank_read_count}")
        try:
            tank_data = hardware.read_temperature("temp_tank")
            self.tank_temp_c = round(tank_data[0], 2)
            self.tank_temp_f = round(tank_data[1], 2)
            tank_entities = (self.datetimenow, self.tank_temp_c, self.tank_temp_f)
            logger.debug(f"Current Tank Reading: {self.tank_temp_c}°C/{self.tank_temp_f}°F")
            self.sql_tank_insert(con=self.con, entities=tank_entities)
            count_success = self.tank_read_success + 1
            self.tank_read_success = count_success
            read_failures = self.tank_read_count - self.tank_read_success
            logger.debug(f"Failed Tank Reads: {read_failures}")
        except w1thermsensor.errors.SensorNotReadyError as error:
            logger.critical(f"Sensor Not Ready: {error.args[0]}")
        except Error:
            logger.exception("Temperature Monitoring Failed")
        finally:
            self.ds18b20_reading = False

    @alerts
    def room_temperature(self):
        try:
            self.dht22_reading = True
            room = hardware.room_temperature()
            count = self.room_read_count + 1
            self.room_read_count = count
            count_success = self.room_read_success + 1
            self.room_read_success = count_success
            read_failures = self.room_read_count - self.room_read_success
            logger.info(f"Sensor Read Count - Room: {self.room_read_count}")
            logger.debug(f"Failed Room Read: {read_failures}")
            if room is not None:
                self.datetimenow = datetime.datetime.utcnow()
                self.room_temp_c = room['temp_c']
                self.room_temp_f = room['temp_f']
                self.room_humidity = room['humidity']
                room_entities = (self.datetimenow, self.room_temp_c, self.room_temp_f, self.room_humidity)
                logger.debug(f"Current Room Reading: {self.room_temp_c}°C/{self.room_temp_f}°F - Humidity: "
                             f"{self.room_humidity}%")
                self.sql_room_insert(con=self.con, entities=room_entities)
        except TypeError as error:
            logger.exception(error.args[0])
        finally:
            self.dht22_reading = False


class RotatingDataBase:
    def __init__(self, database='AquaPiDB'):
        self.database = database
        self.df = None


class RotatingCsvData:
    def __init__(self, file_name='graph_data.csv', columns=None):
        self.columns = columns
        self.file_name = file_name
        self.df = None
        self.last_df_save = datetime.datetime.utcnow()
        # self.load_graph_data()
        self.save_interval = datetime.timedelta(seconds=10)
        self.line_limit = 36000
        self.line_count = None
        lock_path = self.file_name + ".lock"
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
#schedule.every(2).seconds.do(offline_funcs.monitor_temperature)
schedule.every(2).seconds.do(offline_funcs.monitor_tank)
schedule.every(3).seconds.do(offline_funcs.monitor_room)

# con = offline_funcs.sql_connection()
# offline_funcs.sql_table(con=con)
try:
    while True:
        schedule.run_pending()
except:
    logger.exception("Schedule error")
