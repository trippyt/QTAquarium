import threading

from quart import Quart, request, websocket
from quart.json import jsonify
import asyncio
import utils
from time import sleep
app = Quart(__name__)


@app.route('/setTemperatureAlert', methods=['GET', 'POST'])
async def set_temperature_alert():
    ht = request.args.get('ht')
    lt = request.args.get('lt')
    print(f"Receiving Temperature Alert Data H:{ht} L:{lt}")
    utils.alert_data(ht, lt)
    return f"Temperature Alerts H:{ht} L:{lt}"


@app.route('/getServerData', methods=['GET'])
async def get_server_data():
    print("Sending Data to Client")
    data = utils.load()
    print(f'Return data: {data}')
    return jsonify(data)


@app.route('/setRatios', methods=['GET', 'POST'])
async def ratios():
    ratio_results = [float(request.args.get(ratio)) for ratio in
                     ('Tank', 'Co2_ratio', 'Co2_water', 'Fertilizer_ratio', 'Fertilizer_water', 'WaterConditioner_ratio',
                      'WaterConditioner_water')]
    print(type(ratio_results))
    utils.newRatios(ratio_results)
    return f"New ratios: {ratio_results}"


@app.route('/calibrationModeOn', methods=['GET', 'POST'])
async def run_calibration():
    pump_type = request.args.get('type')
    print(pump_type)
    if pump_type in ['Conditioner', 'Co2', 'Fertilizer']:
        cal_thread = threading.Thread(target=utils.start_calibration, args=(pump_type,))
        cal_thread.start()
        return f"Calibrating {pump_type} pump."
    else:
        return "Invalid pump specified"


@app.websocket('/temp')
async def temp():
    while True:
        temp = utils.tank_temperature()
        print(temp)
        await asyncio.sleep(2)
        await websocket.send(str(temp))


if __name__ == '__main__':
    app.run("0.0.0.0")
