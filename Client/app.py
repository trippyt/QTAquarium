from time import gmtime, strftime
from PyQt5 import QtWidgets, QtWebSockets
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
import schedule
from PyQt5.QtCore import QFile, QTextStream
from PyQt5.QtWidgets import QApplication
from BreezeStyleSheets import breeze_resources
from dateaxisitem import DateAxisItem


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
        self.server_ip = "http://" + self.ip_address + ":" + self.ip_port
        self.nam = QtNetwork.QNetworkAccessManager()
        self.df = None
        self.data = None
        self.temp_data = None
        schedule.every().second.do(self.update_plot_data)
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

        self.client = QtWebSockets.QWebSocket("", QtWebSockets.QWebSocketProtocol.Version13, None)
        self.client.error.connect(self.on_error)
        self.client.open(QUrl(f"ws://{self.ip_address}:5000/csv"))
        self.client.pong.connect(self.ws_receive)
        self.client.textMessageReceived.connect(self.ws_receive)

        #self.client.open(QUrl(f"ws://{self.ip_address}:5000/csv"))
        #self.client.pong.connect(self.ws_receive2)
        #self.client.textMessageReceived.connect(self.ws_receive2)

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


        try:
            self.graphWidget = pg.PlotWidget(self.form.temperatureGraph)

            # self.setCentralWidget(self.form.temperatureGraph)

            # self.x = list(range(61))  # 60 time points
            # self.y = [randint(20, 25) for i in range(61)]  # 60 data points
            # self.x = list(range(61))
            # self.y = [2 for i in range(61)]
            graphrange = [0 for i in range(15)]
            self.x = graphrange
            self.y = graphrange

            self.graphWidget.setBackground('k')
            self.graphWidget.setGeometry(QtCore.QRect(0, 0, 731, 361))
            self.graphWidget.setLabel('left', 'Temperature (°C)', color='red', size=30)
            self.graphWidget.setLabel('bottom', 'Seconds (S)', color='red', size=30)
            self.graphWidget.showGrid(x=True, y=True)
            pen = pg.mkPen(color=(0, 0, 255), width=2)
        except:
            logger.exception("Couldn't Draw Graph")

        #self.data_line = self.graphWidget.plot(self.x, self.y, pen=pen, symbol='o', symbolSize=10, symbolBrush='c')
        self.data_line = self.graphWidget.plot(self.x, self.y, pen=pen)

        self.load_config()
        self.load_server()

        # self.timer = QtCore.QTimer()
        # self.timer.setInterval(2000)
        # self.timer.timeout.connect(self.update_plot_data)
        # self.timer.start()

    def update_plot_data(self):
        try:
            if self.data is not None:
                self.df = pandas.read_csv(self.data, parse_dates=['timestamp'])
                logger.debug(f"CSV Line Count: {len(self.df)}\n" 
                             f"First Value Read: {self.df.head(1)}\n"
                             f"Last Value Read: {self.df.tail(1)}")
                self.y = self.df['temp'].to_numpy()
                self.x = pandas.to_datetime(self.df['timestamp'])
                self.x = [t.timestamp() for t in self.x]
                self.data_line.setData(self.x, self.y)
                #axis = DateAxisItem(orientation='bottom')
                #axis.attachToPlotItem(self.graphWidget.getPlotItem())

                self.graphWidget.showGrid(x=False, y=False)
                self.graphWidget.showGrid(x=True, y=True)

                #logger.info("CSV Data Loaded")
                #logger.info(f"{self.df}")
        except:
            logger.exception("Couldn't Update Plot Data")

        #temp_graph_data =
        """
        self.x = self.x[1:]  # Remove the first y element.
        self.x.append(self.x[-1] + 1)  # Add a new value 1 higher than the last.
        self.y = self.y[1:]  # Remove the first
        #self.y.append(randint(0, 100))  # Add a new random value.
        temp = float(self.temp_c)
        self.y.append(temp)

        self.data_line.setData(self.x, self.y)  # Update the data.

        try:
            data = float(self.temp_c)
            curve = pg.PlotDataItem(data)
            data = np.roll(data, 1)  # scroll data
            curve.setData(data)  # re-plot
        except:
            logger.exception("shit")
        """

    def temp_display(self):
        try:
            if self.data is not None:
                self.temp_data = pandas.read_csv(self.data)
                c = self.temp_data['temp'].iat[-1]
                self.form.tank_display_c.display(c)
        except pandas.errors.EmptyDataError:
            logger.warning("No columns to parse from file")



    def load_server(self):
        logger.info("=" * 125)
        resp = requests.get(url=f"{self.server_ip}/getServerData")
        self.new_data = json.loads(resp.content)
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

    def ws_receive(self, csv):
        self.data = io.StringIO(csv)
        logger.debug(len(csv))
        try:
            schedule.run_pending()
        except:
            logger.exception("fucked it")

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


def main():
    App().run()


if __name__ == '__main__':
    main()

