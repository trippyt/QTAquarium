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
from random import randint
import matplotlib.pyplot as plt
import numpy as np



class InfoHandler(logging.Handler):  # inherit from Handler class
    def __init__(self, textBrowser):
        super().__init__()
        self.textBrowser = textBrowser

    def emit(self, record):  # override Handler's `emit` method
        self.textBrowser.append(self.format(record))


class App(object):
    def __init__(self):
        self.ip_address = "192.168.1.33"
        self.ip_port = "5000"
        self.server_ip = "http://"+self.ip_address+":"+self.ip_port
        self.nam = QtNetwork.QNetworkAccessManager()

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
        self.ratio_displays = [self.form.Tank, self.form.Co2_ratio,
                               self.form.Co2_water, self.form.Fertilizer_ratio,
                               self.form.Fertilizer_water, self.form.WaterConditioner_ratio,
                               self.form.WaterConditioner_water, self.form.Co2_dosage,
                               self.form.Fertilizer_dosage, self.form.WaterConditioner_dosage]
        logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
        self.log = logging.getLogger('AquariumQT')
        self.log.handlers = [InfoHandler(self.form.textBrowser)]

        self.client = QtWebSockets.QWebSocket("", QtWebSockets.QWebSocketProtocol.Version13, None)
        self.client.error.connect(self.on_error)
        self.client.open(QUrl(f"ws://{self.ip_address}:5000/temp"))
        self.client.pong.connect(self.ws_receive)
        self.client.textMessageReceived.connect(self.ws_receive)

        self.form.Co2_calibrateButton.clicked.connect(lambda: self.enter_calibrationMode("Co2"))
        self.form.save_ratios_pushButton.clicked.connect(self.save_ratios)
        self.form.ht_alert_doubleSpinBox.valueChanged.connect(self.set_temp_alert)
        self.form.lt_alert_doubleSpinBox.valueChanged.connect(self.set_temp_alert)
        self.form.ht_checkBox.stateChanged.connect(self.set_temp_alert)
        self.form.lt_checkBox.stateChanged.connect(self.set_temp_alert)
        self.form.view_pass_checkBox.stateChanged.connect(self.view_pass)
        self.form.sys_setting_save_pushButton.clicked.connect(self.save_email)
        self.form.sys_setting_test_pushButton.clicked.connect(self.temp_alert_test)
        #self.form.sys_setting_test_pushButton.clicked.connect(self.email_test)
        self.form.sys_setting_update_pushButton.clicked.connect(self.update)
        self.form.alert_limit_spinBox.valueChanged.connect(self.save_email_alert)

        self.graphWidget = pg.PlotWidget(self.form.temperatureGraph)
        #self.setCentralWidget(self.form.temperatureGraph)

        #self.x = list(range(61))  # 60 time points
        #self.y = [randint(20, 25) for i in range(61)]  # 60 data points
        #self.x = list(range(61))
        #self.y = [2 for i in range(61)]
        graphrange = [0 for i in range(15)]
        self.x = graphrange
        self.y = graphrange

        self.graphWidget.setBackground('w')
        self.graphWidget.setGeometry(QtCore.QRect(0, 0, 731, 361))
        self.graphWidget.setLabel('left', 'Temperature (°C)', color='red', size=30)
        self.graphWidget.setLabel('bottom', 'Seconds (S)', color='red', size=30)
        self.graphWidget.showGrid(x=True, y=True)
        pen = pg.mkPen(color=(0, 0, 255), width=2)

        self.data_line = self.graphWidget.plot(self.x, self.y, pen=pen, symbol='o', symbolSize=10, symbolBrush='c')

        self.load_config()
        self.load_server()

        #elf.timer = QtCore.QTimer()
        #self.timer.setInterval(2000)
        #self.timer.timeout.connect(self.update_plot_data)
        #self.timer.start()

    def update_plot_data(self):
        try:
            print("hi")

        except Exception as e:
            logger.exception(e)
        """
        try:
            self.x = self.x[1:]  # Remove the first y element.
            self.x.append(self.x[-1] + 2)  # Add a new value 1 higher than the last.
            self.y = self.y[1:]  # Remove the first
            #self.y.append(randint(0, 100))  # Add a new random value.
            temp = float(self.temp_c)
            self.y.append(round(temp))

            self.data_line.setData(self.x, self.y)  # Update the data.
        """
    def load_server(self):
        resp = requests.get(url=f"{self.server_ip}/getServerData")
        try:
            logging.info("=" * 125)
            logging.info("Attempting to Load from Data.txt".center(125))
            self.new_data = json.loads(resp.content)
            logging.info("JSON Data Loaded".center(125))
            print(f"New JSON Data = {self.new_data}")
        except json.decoder.JSONDecodeError:
            logging.info("Couldn't Load JSON From Server".center(125))
        try:
            self.ratio_data = self.new_data["Ratio Data"]
            logging.info("=" * 125)
            #for display in self.ratio_displays:
            #    display.blockSignals(True)
            try:
                for key in self.ratio_data:
                    ui_obj = getattr(self.form, key)
                    if isinstance(ui_obj, QtWidgets.QDoubleSpinBox):
                        ui_obj.setValue(self.ratio_data[key])
                    else:
                        ui_obj.setText(str(self.ratio_data[key]))
            except KeyError as e:
                logging.info("No Ratio Values From The Server to Load".center(125))
                logging.exception(e)
            #for display in self.ratio_displays:
            #    display.blockSignals(False)
        except TypeError as e:
            logging.info("Couldn't Load Data from the Server".center(125))
            logging.exception(e)

        except UnboundLocalError as e:
            logging.info("Couldn't Load Data".center(125))
            logging.exception(e)
        try:
            self.form.ht_alert_doubleSpinBox.blockSignals(True)
            self.form.lt_alert_doubleSpinBox.blockSignals(True)
            try:
                self.calibration_data = self.new_data["Calibration Data"]
                # print(self.calibration_data)
                co2_cal = self.calibration_data["Co2 Calibration Data"]["Time per 10mL"]
                self.form.lcd_co2_cal.display(co2_cal)
            except KeyError as e:
                logging.exception(e)
            self.form.ht_alert_doubleSpinBox.blockSignals(False)
            self.form.lt_alert_doubleSpinBox.blockSignals(False)
        except KeyError as e:
            logging.exception(e)
        try:
            self.setting_data = self.new_data["Setting Data"]
            ht = self.setting_data["Temperature Alerts"]["High Temp"]
            ht_enabled = self.setting_data["Temperature Alerts"]["High Enabled"]
            lt = self.setting_data["Temperature Alerts"]["Low Temp"]
            lt_enabled = self.setting_data["Temperature Alerts"]["Low Enabled"]
            self.form.ht_alert_doubleSpinBox.setValue(float(ht))
            self.form.lt_alert_doubleSpinBox.setValue(float(lt))
            self.form.ht_checkBox.setChecked(bool(int(ht_enabled)))
            self.form.lt_checkBox.setChecked(bool(int(lt_enabled)))
            #self.form.alert_limit_spinBox.
        except KeyError as e:
            logging.exception(e)
        logging.info("=" * 125)

    def load_config(self):
        logging.info("=" * 125)
        resp = requests.get(url=f"{self.server_ip}/getConfig")
        print(f"Response:{resp.content}")
        try:
            logging.info("Attempting to Load from Config.json".center(125))
            self.config_data = json.loads(resp.content)
            logging.info(f"Loading Config:{self.config_data}")
        except Exception:
            logging.info(f"Couldn't Load Config from the Server")
        try:
            email_user = self.config_data["network_config"]["target_email"]
            service_email = self.config_data["network_config"]["service_email"]
            alert_limit_email = int(self.config_data["network_config"]["alert_limit"])
            self.form.email_lineEdit.setText(email_user)
            self.form.sys_setting_atemail_comboBox.setCurrentText(service_email)
            self.form.alert_limit_spinBox.setValue(alert_limit_email)
            self.view_pass()
        except Exception:
            logging.exception("Couldn't Load data from 'config.json'")
        logging.info("=" * 125)

    def view_pass(self):
        logger.info("=" * 125)
        logger.info("Attempting to  Load Password")
        if self.config_data["network_config"]["password_email"]:
            pass_email = self.config_data["network_config"]["password_email"]
            logger.info(f"Password found: {pass_email}")
            try:
                pass_chk = self.form.view_pass_checkBox.checkState()
                logger.info(f"Pass Visible Check: {pass_chk}")
                i = len(pass_email)
                if pass_chk == 2:
                    self.form.email_pass_lineEdit.setText(pass_email)
                    logger.info(f"Revealing Pass: {pass_email}")
                else:
                    self.form.email_pass_lineEdit.setText("*"*i)
                    logger.info("Pass Hidden")
            except KeyError:
                logging.exception("Couldn't Email Password to Load")
        else:
            logging.exception("Couldn't Email Password to Load")
            logging.info(f"self.config data: {self.config_data}")
        logging.info("=" * 125)

    def update(self):
        try:
            resp = requests.get(url=f"{self.server_ip}/update")
            logging.info("Checking for Updates...")
            logging.info(f"Response: {resp}")

        except:
            logging.exception("Couldn't Update")

    def temp_alert_test(self):
        resp = requests.get(url=f"{self.server_ip}/alertTest")
        logging.info(f"Response: {resp}")
        logging.info(f"Sending Alert Test")

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
                      'WaterConditioner Concentrate: {} mL, WaterConditioner to Water: {} Litres'.format(
            *ratio_results))
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
                logging.info("Calibration Mode: ON")
            else:
                requests.get(url=f"{self.server_ip}/calibrationModeOff?type={pump_type}")
                logging.info("Calibration Mode: OFF")
                self.load_server()
        except Exception as e:
            logging.exception(e)

    def exit_calibrationMode(self, pump_type):
        requests.get(url=f"{self.server_ip}/calibrationModeOff?type={pump_type}")

    def set_temp_alert(self):
        ht = self.form.ht_alert_doubleSpinBox.value()
        ht_enabled = self.form.ht_checkBox.checkState()
        lt = self.form.lt_alert_doubleSpinBox.value()
        lt_enabled = self.form.lt_checkBox.checkState()
        logging.info(f"Sending Alert Changes to Network".center(125))
        logging.info(f"High Temperature: {ht}")
        logging.info(f"Low Temperature: {lt}")
        requests.get(url=f"{self.server_ip}/setTemperatureAlert?ht={ht}&lt={lt}&ht_enabled={ht_enabled}"
                         f"&lt_enabled={lt_enabled}")
        self.load_server()

    def ip_update(self):
        LAN_host = self.form.ip_spinBox.value()
        LAN_id = "192.168.1."
        print(f"Ip Address Updated")

    def save_email(self):
        logging.info("=" * 125)
        logging.info(f"config start of email function: {self.config_data}")
        email_user = self.form.email_lineEdit.text()
        password_email = self.form.email_pass_lineEdit.text()
        if password_email != 0:
            password_email = self.form.email_pass_lineEdit.text()
        else:
            pass
        if "*" in password_email:
            password_email = self.config_data["network_config"]["password_email"]
        logging.info(f"config middle of email function: {self.config_data}")
        logging.info(f"config password_email: {password_email}")
        service_email_drop = self.form.sys_setting_atemail_comboBox.currentText()
        service_email = service_email_drop.strip()
        #alert_limit = self.form.alert_limit_spinBox.value()
        requests.get(url=f"{self.server_ip}/saveEmail?email_user={email_user}&service_email={service_email}\
                        &password_email={password_email}")
        logging.info(f"config end of email function: {self.config_data}")
        self.load_config()
        logging.info(f"config after reloading email function: {self.config_data}")

    def save_email_alert(self):
        print("=" * 125)
        logging.info(f"Email Alert Limit Updated".center(125))
        print("=" * 125)
        alert_limit = self.form.alert_limit_spinBox.value()
        print(f"Type:{type(alert_limit)} Value: {alert_limit}")
        requests.get(url=f"{self.server_ip}/saveEmail_limit?alert_limit={alert_limit}")
        print("=" * 125)

    def email_test(self):
        try:
            logging.info("Asking Server to Test Email")
            requests.get(url=f"{self.server_ip}/emailTest")
        except:
            logging.exception("ERROR: Couldn't Send Test Email")

    def run(self):
        self.window.show()
        self.app.exec()

    def handle_response(self, response):
        print(response.readAll())  # you can change this to show in the log instead if you want to

    def start_timers(self):
        return

    def set_temp_display_color(self, color):
        return self.form.tank_display_c.setStyleSheet(f"QLCDNumber {{background-color: {color}}}")

    def graph_test(self):
        pass

    def ws_receive(self, text):
        self.temp_c = text
        self.update_plot_data()
        self.form.tank_display_c.display(text)
        ht_chk = self.setting_data["Temperature Alerts"]["High Enabled"]
        lt_chk = self.setting_data["Temperature Alerts"]["Low Enabled"]
        ht_thr = self.setting_data["Temperature Alerts"]["High Temp"]
        lt_thr = self.setting_data["Temperature Alerts"]["Low Temp"]
        #try:
        #    self.graphTest()
        #except Exception as e:
        #    logging.exception(e)
        try:
            #print(f"ht_chk: {ht_chk}")
            #print(f"lt_chk: {lt_chk}")
            #print(f"ht_thr: {ht_thr}")
            #print(f"lt_thr: {lt_thr}")
            if ht_thr < lt_thr:
                logging.warning("High Temp Cannot Be Lower Than low Temp")
                return
            if ht_chk == '2':
                if float(text) > float(ht_thr):
                    print("High Temp Alert!!!")
                    self.set_temp_display_color("red")
            else:
                self.set_temp_display_color("white")
            if lt_chk == '2':
                if float(text) < float(lt_thr):
                    print("Low Temp Alert!!!")
                    self.set_temp_display_color("cyan")
            else:
                self.set_temp_display_color("white")
            #print(f"ws_receive: {text}")
        except:
            logging.exception("Alert :ERROR")

    def on_error(self, error_code):
        return


def main():
    App().run()


if __name__ == '__main__':
    main()
