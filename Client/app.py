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
        self.app = QtWidgets.QApplication(sys.argv)
        self.central = QtWidgets.QWidget()
        self.window = QtWidgets.QMainWindow()
        self.form = Ui_Form()
        self.window.setCentralWidget(self.central)
        self.form.setupUi(self.central)
        self.ratio_displays = [self.form.Tank_doubleSpinBox, self.form.Co2_ml_doubleSpinBox,
                               self.form.Co2_water_doubleSpinBox, self.form.Fertilizer_ml_doubleSpinBox,
                               self.form.Fertilizer_water_doubleSpinBox, self.form.WaterConditioner_ml_doubleSpinBox,
                               self.form.WaterConditioner_water_doubleSpinBox, self.form.Co2_dosage_ml_lineEdit,
                               self.form.Fertilizer_dosage_ml_lineEdit, self.form.WaterConditioner_dosage_ml_lineEdit]
        logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
        self.log = logging.getLogger('AquariumQT')
        self.log.handlers = [InfoHandler(self.form.textBrowser)]

        self.client = QtWebSockets.QWebSocket("", QtWebSockets.QWebSocketProtocol.Version13, None)
        self.client.error.connect(self.on_error)
        self.client.open(QUrl(f"ws://{ip_address}:5000/temp"))
        self.client.pong.connect(self.ws_receive)
        self.client.textMessageReceived.connect(self.ws_receive)

        self.form.save_ratios_pushButton.clicked.connect(self.save_ratios)
        self.form.ht_alert_doubleSpinBox.valueChanged.connect(self.set_temp_alert)
        self.load_server()

    def load_server(self):
        url = f"http://192.168.1.33:5000/getServerData"
        request = QtNetwork.QNetworkRequest(QUrl(url))
        loop = QEventLoop()  # Do you intend to start a new loop instance here?
        # If not: I don't use pyQT but I would expect there to be a function like QEventLoop.get_running_loop()
        # which would give you reference rather than starting a new instance
        resp = self.nam.get(request)
        resp.finished.connect(loop.quit)
        logging.info("=" * 125)
        logging.info('Loading Data From the Server'.center(125))
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
            # x = [self.form.display.blockSignals(True) for display in self.ratio_displays]


            # We need to use getattr because in the above statement, display is its own variable. You can't access
            # an attribute with the variable name like that. Because you don't use the variable `display`,
            # the above code is equivalent to the following:
            # x = [self.form.display.blockSignals(True) for _ in self.ratio_displays]

            # since there is no .display attribute for self.form, this would cause an attribute error normally.
            # However, since you call a method on the object, the first error raised is a TypeError which tells you it
            # cannot find the function reference for this object, which is a symptom of the same problem.

            # The correct way to get those attributes is as follows:

            for display in self.ratio_displays:
                display.blockSignals(True)

            try:
                # y = [self.form.display.setValue(value) for display in self.ratio_displays for value in self.ratio_data]
                # To iterate over pairs of values, you should zip them as shown below
                # Nesting loops as you did initially creates a loop per variable value, which isn't what you want here.
                # Generally you should avoid nesting loops in one line, but sometimes it is ok for simple tasks.
                # We also use getattr here as we did before.
                for key in self.ratio_data:
                    getattr(self.form, key).setValue(self.ratio_data[key])

            except KeyError as e:
                logging.info("No Ratio Values From The Server to Load".center(125))
                logging.info(e)

        except TypeError as e:
            logging.info("Couldn't Load Data from the Server".center(125))
            logging.exception(e)

        except UnboundLocalError as e:
            logging.info("Couldn't Load Data".center(125))
            logging.exception(e)
        logging.info("=" * 125)
    '''
    def load_server(self):
        url = f"http://{ip_address}:5000/getServerData"
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
            x = [display.blockSignals(True) for display in self.ratio_displays]
            try:
                y = [display.setValue(value) for display in self.ratio_displays for value in self.ratio_data]
            except KeyError:
                logging.info("No Ratio Values From JSON".center(125))

        except TypeError as e:
            logging.info("Couldn't Load data from the Server: {}".format(e).center(125))

        except UnboundLocalError:
            logging.info("Couldn't Load Data".center(125))
        logging.info("=" * 125)'''

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
