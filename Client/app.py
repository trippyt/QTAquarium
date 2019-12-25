from time import gmtime, strftime
from PyQt5 import QtWidgets, QtWebSockets
from PyQt5 import QtCore, QtNetwork
from PyQt5.QtCore import QTime, QUrl, QEventLoop
from form import Ui_Form
import logging
import sys
import json


class InfoHandler(logging.Handler):  # inherit from Handler class
    def __init__(self, textBrowser):
        super().__init__()
        self.textBrowser = textBrowser

    def emit(self, record):  # override Handler's `emit` method
        self.textBrowser.append(self.format(record))


class RatioDisplays(displaytype):
    form = Ui_Form()
    Tank = form.Tank_doubleSpinBox
    Co2_ml = form.Co2_ml_doubleSpinBox
    Co2_water = form.Co2_water_doubleSpinBox
    Fertilizer_ml = form.Fertilizer_ml_doubleSpinBox
    Fertilizer_water = form.Fertilizer_water_doubleSpinBox
    WaterConditioner_ml = form.WaterConditioner_ml_doubleSpinBox
    WaterConditioner_water = form.WaterConditioner_water_doubleSpinBox


class App(object):
    def __init__(self):
        ipaddress = "192.168.1.33"
        self.nam = QtNetwork.QNetworkAccessManager()
        self.ratio_displays = ('Tank_doubleSpinBox', 'Co2_ml_doubleSpinBox',
                          'Co2_water_doubleSpinBox', 'Fertilizer_ml_doubleSpinBox',
                          'Fertilizer_water_doubleSpinBox', 'WaterConditioner_ml_doubleSpinBox',
                          'WaterConditioner_water_doubleSpinBox')
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
        self.app = QtWidgets.QApplication(sys.argv)
        self.central = QtWidgets.QWidget()
        self.window = QtWidgets.QMainWindow()
        self.form = Ui_Form()
        self.window.setCentralWidget(self.central)
        self.form.setupUi(self.central)
        logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
        self.log = logging.getLogger('AquariumQT')
        self.log.handlers = [InfoHandler(self.form.textBrowser)]

        self.client = QtWebSockets.QWebSocket("", QtWebSockets.QWebSocketProtocol.Version13, None)
        self.client.error.connect(self.on_error)
        self.client.open(QUrl(f"ws://{ipaddress}:5000/temp"))
        self.client.pong.connect(self.ws_receive)
        self.client.textMessageReceived.connect(self.ws_receive)

        self.form.save_ratios_pushButton.clicked.connect(self.save_ratios)
        self.form.ht_alert_doubleSpinBox.valueChanged.connect(self.set_temp_alert)
        self.load_server()

    def load_server(self):
        url = f"http://192.168.1.35:5000/getServerData"
        request = QtNetwork.QNetworkRequest(QUrl(url))
        loop = QEventLoop()
        resp = self.nam.get(request)
        resp.finished.connect(loop.quit)
        logging.info("=" * 125)
        logging.info('Loading Data From the Server'.center(125))
        loop.exec_()
        data = resp.readAll()
        byte_array = data
        try:
            new_data = json.loads(byte_array.data())
            logging.info("JSON Data Loaded".center(125))
        except json.decoder.JSONDecodeError:
            logging.info("Couldn't Load JSON From Server".center(125))
        try:
            self.ratio_data = new_data["Ratio Data"]
            logging.info("=" * 125)
            x = [self.form.display.blockSignals(True) for display in self.ratio_displays]
            try:
                y = [self.form.display.setValue(value) for display in self.ratio_displays for value in self.ratio_data]
            except KeyError:
                logging.info("No Ratio Data From The Server to Load".center(125))

        except UnboundLocalError:
            logging.info("Couldn't Load Data".center(125))
            logging.info("=" * 125)

    def save_ratios(self):
        self.log.info("Sending New Ratio Data to Server")
        ratio_results = [int(ratio.value()) for ratio in
                         (self.form.Tank_doubleSpinBox, self.form.Co2_ml_doubleSpinBox,
                          self.form.Co2_water_doubleSpinBox, self.form.Fertilizer_ml_doubleSpinBox,
                          self.form.Fertilizer_water_doubleSpinBox, self.form.WaterConditioner_ml_doubleSpinBox,
                          self.form.WaterConditioner_water_doubleSpinBox)]
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
        # self.load_server()

    def set_temp_alert(self):
        ht = self.form.ht_alert_doubleSpinBox.value()
        lt = self.form.lt_alert_doubleSpinBox.value()
        print(f"Sending Alert Changes to Network")
        print(f"High Temperature: {ht}")
        print(f"Low Temperature: {lt}")
        url = f"http://192.168.1.33:5000/setTemperatureAlert?ht={ht}&lt={lt}"
        request = QtNetwork.QNetworkRequest(QUrl(url))
        self.nam.get(request)

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
