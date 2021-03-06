import asyncio
import json
import logging
import os
#  import dht11
import threading
import time
from time import sleep

import RPi.GPIO as GPIO
from w1thermsensor import W1ThermSensor


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
pumps = {            # Initializing the GPIO pins 17,27,22 for Dosage pumps
    'Co2': 17,
    'Fertilizer': 27,
    'Water Conditioner': 22
}

for (p_type, pin) in pumps.items():
    GPIO.setup(pin, GPIO.OUT)

Button = 16  # Initializing the GPIO pin 16 for Button
led_pin = 12  # Initializing the GPIO pin 12 for LED

FLASH = 0  # Initializing LED States
PULSE = 1  # Initializing LED States

GPIO.setup(Button, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Setup Button
GPIO.setup(led_pin, GPIO.OUT)  # Notification LED pin
pwm = GPIO.PWM(led_pin, 100)  # Created a PWM object
pwm.start(0)  # Started PWM at 0% duty cycle


class CalibrationCancelled (Exception):
    pass


class Calcs:
    def __init__(self):
        pass

    def ratioequals(self, ratio_results):
        print("ratio equals function")
        print(f"values {ratio_results}")
        new_ratio = ('Tank', 'Co2_ratio', 'Co2_water', 'Fertilizer_ratio', 'Fertilizer_water', 'WaterConditioner_ratio'\
                                        , 'WaterConditioner_water')
        zipratio = zip(new_ratio, ratio_results)
        ratiodict = dict(zipratio)
        for value in ['Co2', 'Fertilizer', 'WaterConditioner']:
            ratio = int(ratiodict[value + '_ratio'])
            water = int(ratiodict[value + '_water'])
            tank = int(ratiodict['Tank'])
            try:
                dosage = ratio * tank / water
                ratiodict[value + '_dosage'] = dosage
            except ZeroDivisionError:
                dosage = 0
            #if dosage != 0 else 0
        logging.info(f"Dict Data: {ratiodict}")


class Hardware:

    def __init__(self):
        self.sensors = {
            'temp_tank': W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, "011447ba3caa"),
            #'temp_room': dht11.DHT11(pin=14)
        }
        self.led_loop = True
        self.cCancelled = False
        self.led_task = None
        self.event_loop = asyncio.new_event_loop ()
        if not self.event_loop.is_running():
            t = threading.Thread(target=lambda: self.event_loop.run_forever())
            t.start()

        self.ratio_data = {
            "Tank Size": {},
            "Co2 Ratio": {},
            "Fertilizer Ratio": {},
            "Water Conditioner Ratio": {},
        }
        self.calibration_data = {
            "Co2 Calibration Data": {},
            "Fertilizer Calibration Data": {},
            "Water Conditioner Calibration Data": {},
        }
        self.setting_data = {
            "Network": {},
            "Temperature Alerts": {},
            "Email Alert": {}
        }

        self.cal_status = ["Success", "Failed", "In Progress", "None"]

    def pump_on(self, pump_type):
        pin = pumps.get(pump_type, None)
        if pin is None:
            raise Exception('Invalid Pump Type!')
        GPIO.output(pumps[pump_type], 1)

    def pump_off(self, pump_type):
        pin = pumps.get(pump_type, None)
        if pin is None:
            raise Exception('Invalid Pump Type!')
        GPIO.output(pumps[pump_type], 0)

    def load(self):
        if os.path.isfile('data.txt'):
            with open('data.txt', 'r') as json_file:
                data = json.loads(json_file.read())
                print("Loading Saved Data")
                print(f"Loading Data...{data}")
                self.ratio_data = data["Ratio Data"]
                # temperature_data = data["Temperature Data"]
                # conversion_values
                # schedule_data
                # calibration_data = data["Calibration Data"]
                # light_hour_data
                # dosage_data = data["Dosage Data"]
                return data

    def save(self):
        data = {
            "Setting Data": self.setting_data,
            "Ratio Data": self.ratio_data,
            "Calibration Data": self.calibration_data,
            # "Schedule Data": schedule_data,
            # "Temperature Data": temperature_data,
            # "Dosage Data": dosage_data,
            # "Light Hour Data": light_hour_data
        }
        with open('data.txt', 'w') as json_file:
            json_file.write(json.dumps(data, indent=4))
        logging.info("Settings Updated")

    def email_setup(self):
        pass

    def ratioequals(self, ratio_results):
        print("ratio equals function")
        print(f"values {ratio_results}")
        new_ratio = ('Tank', 'Co2_ratio', 'Co2_water', 'Fertilizer_ratio', 'Fertilizer_water', 'WaterConditioner_ratio'\
                                        , 'WaterConditioner_water')

        zipratio = zip(new_ratio, ratio_results)
        ratiodict = dict(zipratio)
        for value in ['Co2', 'Fertilizer', 'WaterConditioner']:
            print(type(value))
            ratio = float(ratiodict[value + '_ratio'])
            water = float(ratiodict[value + '_water'])
            tank = float(ratiodict['Tank'])
            try:
                dosage = ratio * tank / water
            except ZeroDivisionError:
                dosage = 0
            ratiodict[value + '_dosage'] =  "{:.2f}".format(float(dosage))

            #if dosage != 0 else 0
            self.ratio_data = ratiodict
        print(f"Dict Data: {ratiodict}")
        self.save()
        #for key in ratiodict:
        #    ratio_data["Ratio Data"].update(
        #        f"{key}"
        #    )

    def ratios(self, ratio_results):
        logging.info(f"Ratio: {ratio_results}")
        logging.info('Tank Size: {} Litres,\n'
         'Co2 Concentrate: {} mL, Co2 to Water: {} Litres,\n'
         'Fertilizer Concentrate: {} mL, Fertilizer to Water: {} Litres,\n'
         'WaterConditioner Concentrate: {} mL, WaterConditioner to Water: {} Litres'.format(
            *ratio_results))
        self.ratioequals(ratio_results)

    def calibrate_pump(self, pump_type):
        logging.info(f"Running {pump_type} Pump")
        logging.info(f"{pump_type}                      Calibration started.")
        self.calibration_status(pump_type, self.cal_status[2])
        start = time.time()
        self.pump_on(pump_type)
        self.button_state()
        logging.info(f"Stopping {pump_type}")
        logging.info(f"{pump_type}                      Calibration finished.")
        self.calibration_status(pump_type, self.cal_status[0])
        end = time.time()
        self.pump_off(pump_type)
        cal_time = round(end - start, 2)
        per_ml = round(cal_time / 10, 2)
        print(type(cal_time))
        logging.info(f"{pump_type} Runtime: {cal_time}")
        self.calibration_data[f"{pump_type} Calibration Data"].update(
            {
                "Time per 10mL": cal_time,
                "Time per 1mL": per_ml
            }
        )
        self.save()

    def calibration_status(self, pump_type, stat):
        print(f"pump: {pump_type}, status: {stat}")
        return stat


    def alert_data(self, ht: int, lt: int):
        logging.info("New Alert Set")
        logging.info(f"High Temperature: {ht}")
        logging.info(f"Low Temperature: {lt}")
        self.setting_data["Temperature Alerts"].update(
            {
                "High Temp": ht,
                "Low Temp": lt
            }
        )
        self.save()

    def read_temperature(self, temp_sensor_type):
        sensor = self.sensors.get(temp_sensor_type, None)
        if sensor is None:
            raise Exception('Invalid Sensor Type!')
        if isinstance(sensor, W1ThermSensor):
            temperature_in_all_units = sensor.get_temperatures([W1ThermSensor.DEGREES_C, W1ThermSensor.DEGREES_F])
            return temperature_in_all_units

        #elif isinstance(sensor, dht11.DHT11):
        #    result = sensor.read()
        #    temp_c = result.temperature
        #    return temp_c

    def water_level(self):
        pass

    def button_state(self):
        while GPIO.input(Button):
            #print(f"{GPIO.input(Button)}: Button Idle")
            sleep(0.1)
            if self.cCancelled:
                raise CalibrationCancelled()

        while not GPIO.input(Button):
            #print(f"{GPIO.input(Button)}: Button Pushed")
            sleep(0.1)
            if self.cCancelled:
                raise CalibrationCancelled()

    async def led(self, option):
        if option == FLASH:
            sleep_time = 0.001
        else:  # PULSE
            sleep_time = 0.01

        while self.led_loop:
            for x in range(100):  # This Loop will run 100; times 0 to 100
                pwm.ChangeDutyCycle(x)  # Change duty cycle
                await asyncio.sleep(sleep_time)  # Delay of 10mS
            for x in range(100, 0, -1):  # Loop will run 100 times; 100 to 0
                pwm.ChangeDutyCycle(x)
                await asyncio.sleep(sleep_time)

        pwm.ChangeDutyCycle(0)
        # once signal to stop is received, reset flag to True
        self.led_loop = True

    async def notification_led_flash(self):
        self.notification_led_stop()
        logging.info("Starting Notification LED: Flash")
        await self.led(FLASH)
        self.led_task = asyncio.run_coroutine_threadsafe(self.led(FLASH), self.event_loop)

    async def notification_led_pulse(self):
        self.notification_led_stop()
        logging.info("Starting Notification LED: Pulse")
        await self.led(PULSE)
        self.led_task = asyncio.run_coroutine_threadsafe(self.led(PULSE), self.event_loop)

    def notification_led_stop(self):
        if self.led_task:
            logging.info("Stopping Notification LED")
            self.led_loop = False
            self.led_task.result()
            self.led_task = None
