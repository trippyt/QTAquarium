from time import gmtime, strftime
from PyQt5 import QtWidgets, QtWebSockets
from PyQt5 import QtCore, QtNetwork
from PyQt5.QtCore import QTime, QUrl, QEventLoop
from form import Ui_Form
import logging
import sys
import json
import requests


class InfoHandler(logging.Handler):  # inherit from Handler class
    def __init__(self, textBrowser):
        super().__init__()
        self.textBrowser = textBrowser

    def emit(self, record):  # override Handler's `emit` method
        self.textBrowser.append(self.format(record))


class App(object):
    def __init__(self):
        global ip_address
        ip_address = "192.168.1.33"
        self.nam = QtNetwork.QNetworkAccessManager()

        self.calibration_data = {
            "Co2 Calibration Data": {},
            "Fertilizer Calibration Data": {},
            "Water Conditioner Calibration Data": {},
        }
        self.setting_data = {
            "IP Address": {},
            "Temperature Alerts": {},
            "Email Alert": {}
        }
        self.new_data = {
            "Ratio Data": {}
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
        self.client.open(QUrl(f"ws://{ip_address}:5000/temp"))
        self.client.pong.connect(self.ws_receive)
        self.client.textMessageReceived.connect(self.ws_receive)

        self.form.Co2_calibrateButton.clicked.connect(lambda: self.enter_calibrationMode("Co2"))
        self.form.save_ratios_pushButton.clicked.connect(self.save_ratios)
        self.form.ht_alert_doubleSpinBox.valueChanged.connect(self.set_temp_alert)
        self.load_server()

    def load_server(self):
        url = f"http://{ip_address}:5000/getServerData"
        request = QtNetwork.QNetworkRequest(QUrl(url))
        loop = QEventLoop()  # Do you intend to start a new loop instance here?
        # If not: I don't use pyQT but I would expect there to be a function like QEventLoop.get_running_loop()
        # which would give you reference rather than starting a new instance
        resp = self.nam.get(request)
        resp.finished.connect(loop.quit)
        logging.info("=" * 125)
        logging.info('Connecting to the Server'.center(125))
        loop.exec_()
        data = resp.readAll()
        byte_array = data
        try:
            self.new_data = json.loads(byte_array.data())
            logging.info("JSON Data Loaded".center(125))
        except json.decoder.JSONDecodeError:
            logging.info("Couldn't Load JSON From Server".center(125))
        try:
            self.ratio_data = self.new_data["Ratio Data"]
            logging.info("=" * 125)
            for display in self.ratio_displays:
                display.blockSignals(True)
            try:
                #print(self.ratio_data)
                for key in self.ratio_data:
                    ui_obj = getattr(self.form, key)
                    if isinstance(ui_obj, QtWidgets.QDoubleSpinBox):
                        ui_obj.setValue(self.ratio_data[key])
                    else:
                        ui_obj.setText(str(self.ratio_data[key]))

            except KeyError as e:
                logging.info("No Ratio Values From The Server to Load".center(125))
                logging.exception(e)

            for display in self.ratio_displays:
                display.blockSignals(False)

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
                #print(self.calibration_data)
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
            lt = self.setting_data["Temperature Alerts"]["Low Temp"]
            self.form.ht_alert_doubleSpinBox.setValue(float(ht))
            self.form.lt_alert_doubleSpinBox.setValue(float(lt))

        except KeyError as e:
            logging.exception(e)
        logging.info("=" * 125)

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

                requests.get(url=f"http://{ip_address}:5000/calibrationModeOn?type={pump_type}")
                logging.info("Calibration Mode: ON")
            else:
                requests.get(url=f"http://{ip_address}:5000/calibrationModeOff?type={pump_type}")
                logging.info("Calibration Mode: OFF")
                self.load_server()
        except Exception as e:
            logging.exception(e)


    def exit_calibrationMode(self, pump_type):
        requests.get(url=f"http://{ip_address}:5000/calibrationModeOff?type={pump_type}")

    def set_temp_alert(self):
        ht = self.form.ht_alert_doubleSpinBox.value()
        lt = self.form.lt_alert_doubleSpinBox.value()
        logging.info(f"Sending Alert Changes to Network".center(125))
        logging.info(f"High Temperature: {ht}")
        logging.info(f"Low Temperature: {lt}")
        requests.get(url=f"http://{ip_address}:5000/setTemperatureAlert?ht={ht}&lt={lt}")

    def run(self):
        self.window.show()
        self.app.exec()

    def handle_response(self, response):
        print(response.readAll())  # you can change this to show in the log instead if you want to

    def start_timers(self):
        return

    def ws_receive(self, text):
        self.form.tank_display_c.display(text)

    def on_error(self, error_code):
        return


def main():
    App().run()


if __name__ == '__main__':
    main()
