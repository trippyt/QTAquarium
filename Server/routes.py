import threading
from loguru import logger
from quart import Quart, request, websocket
from quart.json import jsonify
import asyncio
from utils import AquariumController
from email_alert import EmailAlerts

from time import sleep
app = Quart(__name__)

controller = AquariumController()
#emailer = EmailAlerts()

@app.route('/setTemperatureAlert', methods=['GET', 'POST'])
async def set_temperature_alert():
    ht = request.args.get('ht')
    lt = request.args.get('lt')
    ht_enabled = request.args.get('ht_enabled')
    lt_enabled = request.args.get('lt_enabled')
    print(f"ht returns: {ht_enabled}")
    print(f"lt returns: {lt_enabled}")
    print(type(ht_enabled))
    if ht_enabled == '2':
        print(f"ht is: TRUE")
    else:
        print(f"ht is: FALSE")
    if lt_enabled == '2':
        print(f"lt is: TRUE")
    else:
        print(f"lt is: FALSE")


    print(f"Receiving Temperature Alert Data H:{ht} L:{lt}")
    controller.alert_data(ht, lt, ht_enabled, lt_enabled)
    return f"Temperature Alerts H:{ht} L:{lt}"


@app.route('/getServerData', methods=['GET'])
async def get_server_data():
    print("Sending Data to Client")
    data = controller.load_data()
    return jsonify(data)


@app.route('/getConfig', methods=['GET'])
async def load_config():
    print("Sending Config to Client")
    config_data = controller.load_config()
    print(f"Return Config: {config_data}")
    return jsonify(config_data)


@app.route('/update', methods=['GET'])
async def update():
    data = controller.update()
    return jsonify(data)

@app.route('/getUpdates', methods=['GET'])
async def get_updates():
    pass


@app.route('/setRatios', methods=['GET', 'POST'])
async def ratios():
    ratio_results = [float(request.args.get(ratio)) for ratio in
                     ('Tank', 'Co2_ratio', 'Co2_water', 'Fertilizer_ratio', 'Fertilizer_water', 'WaterConditioner_ratio',
                      'WaterConditioner_water')]
    print(type(ratio_results))
    controller.ratios(ratio_results)
    return f"New ratios: {ratio_results}"


@app.route('/calibrationModeOn', methods=['GET', 'POST'])
async def run_calibration():
    pump_type = request.args.get('type')
    print(pump_type)
    if pump_type in ['Conditioner', 'Co2', 'Fertilizer']:
        #cal_thread = threading.Thread(target=controller.start_calibration, args=(pump_type,))
        #cal_thread.start()
        #await controller.start_calibration(pump_type)
        asyncio.create_task(controller.start_calibration(pump_type))
        return f"Calibrating {pump_type} pump."
    else:
        return "Invalid pump specified"


@app.route('/calibrationModeOff', methods=['GET', 'POST'])
async def stop_calibration():
    pump_type = request.args.get('type')
    print(pump_type)
    resp = {}
    if pump_type in ['conditioner', 'co2', 'fertilizer']:
        controller.stop_cal()
        if controller.cal_time:
            resp['cal_time'] = controller.cal_time
        else:
            resp['error'] = 'Calibration was cancelled'
    else:
        resp['error'] = 'Invalid pump type'
    return jsonify(resp)


@app.route('/calibrationStatus', methods=['GET', 'POST'])
async def calibration_status():
    pump_type = request.args.get('type')
    if pump_type in ['conditioner', 'co2', 'fertilizer']:
        controller.cal_status()


@app.route('/saveEmail', methods=['GET', 'POST'])
async def save_email():
    email_user = request.args.get('email_user')
    service_email = request.args.get('service_email')
    password_email = request.args.get('password_email')
    #alert_limit = request.args.get('alert_limit')
    controller.save_email(email_user, service_email, password_email)
    resp = "Success"
    return f"{resp}"


@app.route('/saveEmail_limit', methods=['GET', 'POST'])
async def saveEmail_limit():
    alert_limit = request.args.get('alert_limit')
    controller.saveEmail_limit(alert_limit)
    print(f"Server Received New Alert Limit: {alert_limit}")
    resp = "Success"
    return f"{resp}"


@app.route('/alertTest', methods=['GET', 'POST'])
async def alert_test():
    controller.email_ht_alert()
    resp = "Success"
    return f"{resp}"


@app.route('/emailTest', methods=['GET', 'POST'])
async def email_test():
    logger.info("Client Request send test email")
    controller.email_test()
    resp = "Success"
    return f"{resp}"


@app.route('/')
def hello_world():
    return 'Server Online :-)'


@app.websocket('/csv')
async def csv():
    while True:
        csv_data = controller.json_to_csv()
        await websocket.send(jsonify(csv_data))

@app.websocket('/temp')
async def temp():
    while True:
        display_temp = controller.tank_temperature()
        await asyncio.sleep(2)
        await websocket.send(str(display_temp))


if __name__ == '__main__':
    app.run("0.0.0.0")
