from time import gmtime, strftime
from PyQt5 import QtWidgets, QtWebSockets
from PyQt5.QtWidgets import QWidget, QGridLayout
from PyQt5 import QtCore, QtNetwork
from PyQt5.QtCore import QTime, QUrl, QEventLoop
from form import Ui_Form
import logging
from loguru import logger
import sys
import json
import requests
import pyqtgraph as pg
import pandas
from pandas import errors
import io
# import schedule
import datetime
from PyQt5.QtCore import QFile, QTextStream
import datetime
import time
import numpy as np
from PyQt5.QtWidgets import QApplication
from BreezeStyleSheets import breeze_resources
from dateaxisitem import DateAxisItem
import psycopg2
from psycopg2 import Error
import asyncio
import asyncpgsa
import aioschedule as schedule

"""
class InfoHandler(logging.Handler):  # inherit from Handler class
    def __init__(self, textBrowser):
        super().__init__()
        self.textBrowser = textBrowser

    def emit(self, record):  # override Handler's `emit` method
        self.textBrowser.append(self.format(record))
"""


class PropagateHandler(logging.Handler):
    def __init__(self, textBrowser):
        super().__init__()
        self.textBrowser = textBrowser

    def emit(self, record):
        logging.getLogger(record.name).handle(record)
        self.textBrowser.append(record.name).handle(record)


class App(object):
    def __init__(self):
        self.ip_address = "192.168.1.33"
        self.ip_port = "5000"
        self.db_user = "postgres"
        self.db_pass = "aquaPi"
        self.server_ip = f"http://{self.ip_address}:{self.ip_port}"
        self.nam = QtNetwork.QNetworkAccessManager()
        self.df = None
        self.data = None
        self.temp_data = None
        # schedule.every().second.do(self.update_plot_data)
        schedule.every().second.do(self.graph_display)  ###
        schedule.every().second.do(self.temp_display)

        self.calibration_data = {
            "Co2 Calibration Data": {},
            "Fertilizer Calibration Data": {},
            "Water Conditioner Calibration Data": {},
        }
        self.ratio_data = {
            "Tank": {},
            "Co2_ratio": {},
            "Co2_Water": {},
            "Fertilizer_ratio": {},
            "Fertilizer_water": {},
            "WaterConditioner_ratio": {},
            "WaterConditioner_water": {},
            "Co2_dosage": {},
            "Fertilizer_dosage": {},
            "WaterConditioner_dosage": {},
        }
        self.setting_data = {
            "IP Address": {},
            "Temperature Alerts": {},
            "Email Alert": {}
        }
        self.new_data = {
            "Ratio Data": {}
        }
        self.config_data = {
            "network_data": {},

        }
        self.calibration_mode_on = True
        self.app = QtWidgets.QApplication(sys.argv)
        self.central = QtWidgets.QWidget()
        self.window = QtWidgets.QMainWindow()
        self.form = Ui_Form()
        self.window.setCentralWidget(self.central)
        self.form.setupUi(self.central)
        try:
            file = QFile(":/dark.qss")
            file.open(QFile.ReadOnly | QFile.Text)
            stream = QTextStream(file)
            self.app.setStyleSheet(stream.readAll())
        except:
            logger.exception("Couldn't Load Style Sheet")

        self.ratio_displays = [self.form.Tank, self.form.Co2_ratio,
                               self.form.Co2_water, self.form.Fertilizer_ratio,
                               self.form.Fertilizer_water, self.form.WaterConditioner_ratio,
                               self.form.WaterConditioner_water, self.form.Co2_dosage,
                               self.form.Fertilizer_dosage, self.form.WaterConditioner_dosage]
        # logger.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
        self.log = logging.getLogger('AquariumQT')
        # self.log.handlers = [InfoHandler(self.form.textBrowser)]
        # logger. = [PropagateHandler(self.form.textBrowser)]
        # logger.add(PropagateHandler(), format="{message}")
        # logger.add(sys.stdout, colorize=True, format="<green>{time}</green> <level>{message}</level>")
        # log_decorate = logger.level("Decorator", no=38, color="<yellow>", icon="🐍")

        # self.client = QtWebSockets.QWebSocket("", QtWebSockets.QWebSocketProtocol.Version13, None)
        # self.client.error.connect(self.on_error)
        # self.client.open(QUrl(f"ws://{self.ip_address}:5000/csv"))
        # self.client.pong.connect(self.ws_receive)
        # self.client.textMessageReceived.connect(self.ws_receive)

        # self.client.open(QUrl(f"ws://{self.ip_address}:5000/csv"))
        # self.client.pong.connect(self.ws_receive2)
        # self.client.textMessageReceived.connect(self.ws_receive2)

        self.form.Co2_calibrateButton.clicked.connect(lambda: self.enter_calibrationMode("Co2"))
        self.form.save_ratios_pushButton.clicked.connect(self.save_ratios)
        self.form.ht_alert_doubleSpinBox.valueChanged.connect(self.set_temp_alert)
        self.form.lt_alert_doubleSpinBox.valueChanged.connect(self.set_temp_alert)
        self.form.ht_checkBox.stateChanged.connect(self.set_temp_alert)
        self.form.lt_checkBox.stateChanged.connect(self.set_temp_alert)
        self.form.view_pass_checkBox.stateChanged.connect(self.view_pass)
        self.form.sys_setting_save_pushButton.clicked.connect(self.save_email)
        self.form.sys_setting_test_pushButton.clicked.connect(self.email_test)
        self.form.sys_setting_update_pushButton.clicked.connect(self.update)
        self.form.alert_limit_spinBox.valueChanged.connect(self.save_email_alert)
        # self.form.aquaPi_calendarWidget.selectionChanged.connect(self.aquaPi_schedules)
        # self.temperature_graph = TemperatureWidget()
        # self.plot = pg.PlotWidget(self.form.temperatureGraph)
        self.aquaPi_schedules = {}
        self.aquaPi_hours_list = [self.form.hours_0, self.form.hours_1, self.form.hours_2, self.form.hours_3,
                                  self.form.hours_4, self.form.hours_5, self.form.hours_6, self.form.hours_7,
                                  self.form.hours_8, self.form.hours_9, self.form.hours_10, self.form.hours_11,
                                  self.form.hours_12, self.form.hours_13, self.form.hours_14, self.form.hours_15,
                                  self.form.hours_16, self.form.hours_17, self.form.hours_18, self.form.hours_19,
                                  self.form.hours_20, self.form.hours_21, self.form.hours_22, self.form.hours_23]
        self.form.hour_save_button.clicked.connect(self.save_aquaPi_schedules)

        parent = self.form.temperatureGraph.parent()
        geom_object = self.form.temperatureGraph.frameGeometry()
        geometry = QtCore.QRect(geom_object.left(), geom_object.top(), geom_object.width(), geom_object.height())
        object_name = self.form.temperatureGraph.objectName()

        del self.form.temperatureGraph

        self.plot = pg.PlotWidget(
            parent,
            title="Aquarium Temperature",
            labels={'left': 'Temperature / °C'},
            axisItems={'bottom': TimeAxisItem(orientation='bottom')}
        )
        self.plot.setGeometry(geometry)
        self.plot.setObjectName(object_name)

        self.plot.showGrid(x=True, y=True)

        self.plotCurve = self.plot.plot(pen='y')
        self.plotData = {'x': [], 'y': []}

        self.load_config()
        self.load_server()

        #self.timer = QtCore.QTimer()
        #self.timer.setInterval(10)
        #self.timer.timeout.connect(self.sch_run)
        #self.timer.start()

        self.pool = None

        #asyncio.run(self.sch_run())
        #asyncio.get_event_loop().run_until_complete(self.sch_run())

        #asyncio.get_event_loop().run_until_complete(
        #    self.sch_run()
        #)
        #asyncio.get_event_loop().run_forever(self.tank_db())
        asyncio.get_event_loop().create_task(self.sch_run())


    def save_aquaPi_schedules(self):
        logger.info("=" * 125)
        hour_results = [hour.isChecked() for hour in self.aquaPi_hours_list]
        hour_0, hour_1, hour_2, hour_3, hour_4, hour_5, hour_6, hour_7, hour_8, hour_9, hour_10, hour_11, \
        hour_12, hour_13, hour_14, hour_15, hour_16, hour_17, hour_18, hour_19, hour_20, hour_21, hour_22, \
        hour_23 = hour_results
        a = [index for index, val in enumerate(hour_results) if val]
        print(f"Selected Hours = {a}")
        """
        date = self.form.aquaPi_calendarWidget.selectedDate().toString("dd-MM-yyyy")
        does_operation = self.form.hour_comboBox.currentText()
        run_operation_on = for True in hour_results
        print(f"On {date}, {does_operation} Will run at {run_operation_on}")
        print(hour_results)
        print(hour_10)"""

        # a = self.form.hours_0.isChecked()
        # print(a)
        # hours =

    async def sql_connection(self):
        logger.info("=" * 125)
        logger.info("sql_connection: Entered".center(125))
        try:
            pool = await asyncpgsa.create_pool(
                host=self.ip_address,
                database="AquaPiDB",
                user=self.db_user,
                password=self.db_pass
            )
            logger.debug("Connection is established: Database has been created ")
            return pool
        except Error:
            logger.exception(Error)
        finally:
            logger.info("sql_connection: Exited".center(125))
            logger.info("=" * 125)

    async def tank_db(self):
        logger.info("=" * 125)
        logger.info("tank_db: Entered".center(125))
        while True:
            try:
                if not self.pool:
                    self.pool = await self.sql_connection()
                async with self.pool.transaction() as conn:
                    rows = await conn.fetch('SELECT * FROM tank_temperature')
                    df = pandas.DataFrame(rows, columns=list(rows[0].keys()))
                    logger.success(df)
                return df
            except:
                logger.exception("tank_db Error")
            finally:
                logger.info("tank_db: Exited".center(125))
                logger.info("=" * 125)

    async def graph_display(self):
        logger.info("=" * 125)
        logger.info("graph_display: Entered".center(125))
        try:
            if not self.pool:
                self.pool = await self.sql_connection()

            t = time.time()
            async with self.pool.transaction() as conn:
                rows = await conn.fetch('SELECT * FROM tank_temperature')
                # logger.debug(f"Con: {conn}")
            logger.critical('Async')
            logger.critical(time.time() - t)

            t = time.time()
            self.df = pandas.DataFrame(rows, columns=list(rows[0].keys()))
            logger.critical('DF')
            logger.critical(time.time() - t)

            # logger.debug(f"Values: {self.df.dtypes}")
            t = time.time()
            if self.df is not None:
                self.y = self.df['temperature_c'].to_numpy(dtype=float)
                self.x = self.df['date']
                self.x = [t.timestamp() for t in self.x]
                self.x = [round(t) for t in self.x]
                self.plotData['x'] = self.x
                self.plotData['y'] = self.y
                self.plotCurve.setData(self.plotData['x'], self.plotData['y'])
            logger.critical('Plotting')
            logger.critical(time.time() - t)
        except:
            logger.exception("oops")
        finally:
            logger.info("graph_display: Exited".center(125))
            logger.info("=" * 125)

    async def temp_display(self):
        logger.info("=" * 125)
        logger.info("temp_display: Entered".center(125))
        if self.df is not None:
            c = self.df['temperature_c'].iat[-1]
            f = self.df['temperature_f'].iat[-1]
            self.form.tank_display_c.display(c)
            self.form.tank_display_f.display(f)
            logger.debug(f"°C: {c}")
            logger.debug(f"°F: {f}")
        logger.info("temp_display: Exited".center(125))
        logger.info("=" * 125)

    def load_server(self):
        logger.info("=" * 125)
        resp = requests.get(url=f"{self.server_ip}/getServerData")
        self.new_data = json.loads(resp.content)
        """try:
            resp = requests.get(url=f"{self.server_ip}/getServerData")
            self.new_data = json.loads(resp.content)
            return schedule.cancel_job(self.load_server())
        except requests.exceptions.ConnectionError:
            logger.critical("Server Not Responding")
            schedule.every().minute.do(self.load_server())"""
        try:
            logger.debug("Loading 'data.txt' From Server")
            if resp.json() is None:
                logger.warning("No 'data.txt' Found on Server")
            else:
                logger.success("'data.txt' Loaded from Server")
                logger.debug(f"Response:{self.new_data}")
                logger.info("Assigning Data Values from 'self.new_data'")
                self.calibration_data = self.new_data["Calibration Data"]
                self.ratio_data = self.new_data["Ratio Data"]
                co2_cal = self.calibration_data["Co2 Calibration Data"]["Time per 10mL"]
                self.setting_data = self.new_data["Setting Data"]
                ht = self.setting_data["Temperature Alerts"]["High Temp"]
                ht_enabled = self.setting_data["Temperature Alerts"]["High Enabled"]
                lt = self.setting_data["Temperature Alerts"]["Low Temp"]
                lt_enabled = self.setting_data["Temperature Alerts"]["Low Enabled"]
                try:
                    self.form.ht_alert_doubleSpinBox.blockSignals(True)
                    self.form.lt_alert_doubleSpinBox.blockSignals(True)
                    self.form.ht_checkBox.blockSignals(True)
                    self.form.lt_checkBox.blockSignals(True)
                    for key in self.ratio_data:
                        ui_obj = getattr(self.form, key)
                        if isinstance(ui_obj, QtWidgets.QDoubleSpinBox):
                            ui_obj.setValue(self.ratio_data[key])
                        else:
                            ui_obj.setText(str(self.ratio_data[key]))
                    self.form.lcd_co2_cal.display(co2_cal)
                    self.form.ht_alert_doubleSpinBox.setValue(float(ht))
                    self.form.lt_alert_doubleSpinBox.setValue(float(lt))
                    self.form.ht_checkBox.setChecked(bool(int(ht_enabled)))
                    self.form.lt_checkBox.setChecked(bool(int(lt_enabled)))
                    self.form.ht_alert_doubleSpinBox.blockSignals(False)
                    self.form.lt_alert_doubleSpinBox.blockSignals(False)
                    logger.success("Data Display Values Updated")
                except(KeyError, ValueError, TypeError):
                    logger.warning("Couldn't Assign Values from 'data.txt'")
        except (UnboundLocalError, json.decoder.JSONDecodeError):
            logger.warning("Couldn't Load Data")
        logger.info("=" * 125)

    def load_config(self):
        logger.info("=" * 125)
        logger.info("Connecting To Server".center(125))
        logger.info("=" * 125)
        resp = requests.get(url=f"{self.server_ip}/getConfig")
        self.config_data = json.loads(resp.content)
        try:
            logger.debug("Loading 'config.json' From Server")
            if resp.json() is None:
                logger.warning("No 'config.json' Found on Server")
            else:
                logger.success("'config.json' Loaded from Server")
                logger.debug(f"Response:{self.config_data}")
                logger.info("Assigning Config Values from Config.json")
                try:
                    email_user = self.config_data["network_config"]["target_email"]
                    service_email = self.config_data["network_config"]["service_email"]
                    alert_limit_email = int(self.config_data["network_config"]["alert_limit"])
                    self.form.email_lineEdit.setText(email_user)
                    self.form.sys_setting_atemail_comboBox.setCurrentText(service_email)
                    self.form.alert_limit_spinBox.blockSignals(True)
                    self.form.alert_limit_spinBox.setValue(alert_limit_email)
                    self.form.alert_limit_spinBox.blockSignals(False)
                    logger.success("Config Values Updated")
                    self.view_pass()
                except (KeyError, ValueError, TypeError):
                    logger.warning("Couldn't Assign Values from 'config.json")
        except requests.exceptions.ConnectionError:
            logger.critical("Couldn't Connect To Server".center(125))
        logger.info("=" * 125)

    def view_pass(self):
        logger.info("=" * 125)
        pass_chk = self.form.view_pass_checkBox.checkState()
        logger.info("Loading Saved Password")
        if self.config_data["network_config"]["password_email"]:
            logger.success("Password Found")
            pass_email = self.config_data["network_config"]["password_email"]
            logger.debug(f"Password: {pass_email}")
            try:
                logger.debug(f"Pass Reveal State: {pass_chk}")
                i = len(pass_email)
                if pass_chk == 2:
                    self.form.email_pass_lineEdit.setText(pass_email)
                    logger.debug(f"Revealing Pass: {pass_email}")
                else:
                    self.form.email_pass_lineEdit.setText("*" * i)
                    logger.info("Pass Hidden")
            except KeyError:
                logger.warning("Couldn't Email Password to Load")
        else:
            logger.warning("Couldn't Email Password to Load")
            logger.info(f"self.config data: {self.config_data}")
        logger.info("=" * 125)

    def update(self):
        try:
            resp = requests.get(url=f"{self.server_ip}/update")
            logger.info("Checking for Updates...")
            logger.info(f"Response: {resp}")

        except:
            logger.exception("Couldn't Update")

    def temp_alert_test(self):
        resp = requests.get(url=f"{self.server_ip}/alertTest")
        logger.info(f"Response: {resp}")
        logger.info(f"Sending Alert Test")

    def save_ratios(self):
        self.log.info("Sending New Ratio Data to Server")
        ratio_results = [int(ratio.value()) for ratio in
                         (self.form.Tank, self.form.Co2_ratio,
                          self.form.Co2_water, self.form.Fertilizer_ratio,
                          self.form.Fertilizer_water, self.form.WaterConditioner_ratio,
                          self.form.WaterConditioner_water)]
        Tank, Co2_ratio, Co2_water, Fertilizer_ratio, Fertilizer_water, WaterConditioner_ratio, WaterConditioner_water \
            = ratio_results
        self.log.info('Tank Size: {} Litres,\n'
                      'Co2 Concentrate: {} mL, Co2 to Water: {} Litres,\n'
                      'Fertilizer Concentrate: {} mL, Fertilizer to Water: {} Litres,\n'
                      'WaterConditioner Concentrate: {} mL, WaterConditioner to Water: {} Litres'
                      .format(*ratio_results))
        url = f"http://192.168.1.33:5000/setRatios?Tank={Tank}&Co2_ratio={Co2_ratio}&Co2_water={Co2_water}" \
              f"&Fertilizer_ratio={Fertilizer_ratio}&Fertilizer_water={Fertilizer_water}" \
              f"&WaterConditioner_ratio={WaterConditioner_ratio}&WaterConditioner_water={WaterConditioner_water}"
        request = QtNetwork.QNetworkRequest(QUrl(url))
        self.nam.get(request)
        self.load_server()

    def enter_calibrationMode(self, pump_type):
        try:
            self.calibration_mode_on = not self.calibration_mode_on
            if not self.calibration_mode_on:

                requests.get(url=f"{self.server_ip}/calibrationModeOn?type={pump_type}")
                logger.info("Calibration Mode: ON")
            else:
                requests.get(url=f"{self.server_ip}/calibrationModeOff?type={pump_type}")
                logger.info("Calibration Mode: OFF")
                self.load_server()
        except Exception as e:
            logger.exception(e)

    def exit_calibrationMode(self, pump_type):
        requests.get(url=f"{self.server_ip}/calibrationModeOff?type={pump_type}")

    def set_temp_alert(self):
        ht = self.form.ht_alert_doubleSpinBox.value()
        ht_enabled = self.form.ht_checkBox.checkState()
        lt = self.form.lt_alert_doubleSpinBox.value()
        lt_enabled = self.form.lt_checkBox.checkState()
        logger.info(f"Sending Alert Changes to Network".center(125))
        logger.info(f"High Temperature: {ht}")
        logger.info(f"Low Temperature: {lt}")
        requests.get(url=f"{self.server_ip}/setTemperatureAlert?ht={ht}&lt={lt}&ht_enabled={ht_enabled}"
                         f"&lt_enabled={lt_enabled}")
        self.load_server()

    def ip_update(self):
        LAN_host = self.form.ip_spinBox.value()
        LAN_id = "192.168.1."
        logger.info(f"Ip Address Updated")

    def save_email(self):
        logger.debug("=" * 125)
        logger.info(f"config start of email function: {self.config_data}")
        email_user = self.form.email_lineEdit.text()
        password_email = self.form.email_pass_lineEdit.text()
        if password_email != 0:
            password_email = self.form.email_pass_lineEdit.text()
        else:
            pass
        if "*" in password_email:
            password_email = self.config_data["network_config"]["password_email"]
        logger.info(f"config middle of email function: {self.config_data}")
        logger.info(f"config password_email: {password_email}")
        service_email_drop = self.form.sys_setting_atemail_comboBox.currentText()
        service_email = service_email_drop.strip()
        # alert_limit = self.form.alert_limit_spinBox.value()
        requests.get(url=f"{self.server_ip}/saveEmail?email_user={email_user}&service_email={service_email}\
                        &password_email={password_email}")
        logger.info(f"config end of email function: {self.config_data}")
        self.load_config()
        logger.info(f"config after reloading email function: {self.config_data}")

    def save_email_alert(self):
        logger.debug("=" * 125)
        logger.info(f"Email Alert Limit Updated".center(125))
        logger.debug("=" * 125)
        alert_limit = self.form.alert_limit_spinBox.value()
        logger.info(f"Type:{type(alert_limit)} Value: {alert_limit}")
        requests.get(url=f"{self.server_ip}/saveEmail_limit?alert_limit={alert_limit}")
        logger.debug("=" * 125)

    def email_test(self):
        logger.info("Asking Server to Test Email")
        requests.get(url=f"{self.server_ip}/emailTest")

    def run(self):
        self.window.show()
        self.app.exec()

    def handle_response(self, response):
        logger.info(response.readAll())  # you can change this to show in the log instead if you want to

    def start_timers(self):
        return

    def set_temp_display_color(self, color):
        return self.form.tank_display_c.setStyleSheet(f"QLCDNumber {{background-color: {color}}}")

    def graph_test(self):
        pass

    async def sch_run(self):
        try:
            #asyncio.get_event_loop().run_until_complete(schedule.run_pending())
            #asyncio.run(schedule.run_pending())
            while True:
                await schedule.run_pending()
        except:
            logger.exception("schedule run error")
        #while True:
        #  await schedule.run_pending()
        #  await asyncio.sleep(0.1)

    def ws_receive(self, csv):
        try:
            self.data = io.StringIO(csv)
        # logger.debug(len(csv))
        except:
            logger.debug("stringio error")

    """
    def ws_receive(self, text):
        self.temp_c = text
        self.update_plot_data()
        self.form.tank_display_c.display(text)
        ht_chk = self.setting_data["Temperature Alerts"]["High Enabled"]
        lt_chk = self.setting_data["Temperature Alerts"]["Low Enabled"]
        ht_thr = self.setting_data["Temperature Alerts"]["High Temp"]
        lt_thr = self.setting_data["Temperature Alerts"]["Low Temp"]
        # try:
        #    self.graphTest()
        # except Exception as e:
        #    logger.exception(e)
        try:
            # print(f"ht_chk: {ht_chk}")
            # print(f"lt_chk: {lt_chk}")
            # print(f"ht_thr: {ht_thr}")
            # print(f"lt_thr: {lt_thr}")
            if ht_thr < lt_thr:
                logger.warning("High Temp Cannot Be Lower Than low Temp")
                return
            if ht_chk == '2':
                if float(text) > float(ht_thr):
                    logger.warning("High Temp Alert!!!")
                    self.set_temp_display_color("red")
            else:
                self.set_temp_display_color("white")
            if lt_chk == '2':
                if float(text) < float(lt_thr):
                    logger.warning("Low Temp Alert!!!")
                    self.set_temp_display_color("cyan")
            else:
                self.set_temp_display_color("white")
            # print(f"ws_receive: {text}")
        except:
            logger.exception("Alert :ERROR")
    """

    def on_error(self, error_code):
        return


class TimeAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLabel(text='Time', units=None)
        self.enableAutoSIPrefix(False)

    def tickStrings(self, values, scale, spacing):
        try:
            # print(list(datetime.datetime.fromtimestamp(value).strftime("%d-%m-%y %H:%M") for value in values))
            for value in values:
                a = datetime.datetime.fromtimestamp(value).strftime("%d-%m-%y %H:%M")
                # print(a)
            return [datetime.datetime.fromtimestamp(value).strftime("%d-%m-%Y %H:%M") for value in values]
        except:
            logger.exception("tickStrings")


def main():
    App().run()


if __name__ == '__main__':
    main()
