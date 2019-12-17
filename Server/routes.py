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


@app.route('/setRatios', methods=['GET', 'POST'])
async def ratios():
    ratio_results = [request.args.get('ratio') for ratio in
                     Tank, Co2_ratio, Co2_water, Fertilizer_ratio, Fertilizer_water, WaterConditioner_ratio, WaterConditioner_water]
    tank = request.args.get('tank')
    co2_ml = request.args.get('co2_ml')
    co2_water = request.args.get('co2_water')
    co2_split_dose = request.args.get('co2_split_dose')
    fertz_ml = request.args.get('fertz_ml')
    fertz_water = request.args.get('fertz_water')
    conditioner_ml = request.args.get('conditioner_ml')
    conditioner_water = request.args.get('conditioner_water')


@app.websocket('/temp')
async def temp():
    while True:
        temp = utils.tank_temperature()
        print(temp)
        await asyncio.sleep(2)
        await websocket.send(str(temp))


if __name__ == '__main__':
    app.run("0.0.0.0")
