import asyncio
import logging
import loguru as logger
#  import dht11
import threading
from time import sleep
from pigpio_dht import DHT22

try:
    from w1thermsensor import W1ThermSensor, core
except Exception:
    print("No w1thermsensor Kernel Found")
try:
    import RPi.GPIO as GPIO
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

    dht_pin = 22  # DHT22 Sensor pin
    sensor_dht = DHT22.DHT22(dht_pin)

    GPIO.setup(Button, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Setup Button
    GPIO.setup(led_pin, GPIO.OUT)  # Notification LED pin
    pwm = GPIO.PWM(led_pin, 100)  # Created a PWM object
    pwm.start(0)  # Started PWM at 0% duty cycle
except ModuleNotFoundError:
    print("No Rpi Module Found")


class CalibrationCancelled (Exception):
    pass


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
        self.cal_status = ["Success", "Failed", "In Progress", "None"]

    def room_temperature(self):
        try:
            result = sensor_dht.sample(samples=1)
            return result
        except TimeoutError as error:
            logger.warning(error.args[0])


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

    def email_setup(self):
        pass

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
        self.led(FLASH)
        self.led_task = asyncio.run_coroutine_threadsafe(self.led(FLASH), self.event_loop)
        #self.led_task = asyncio.create_task(self.led(FLASH))

    async def notification_led_pulse(self):
        self.notification_led_stop()
        logging.info("Starting Notification LED: Pulse")
        self.led(PULSE)
        self.led_task = asyncio.run_coroutine_threadsafe(self.led(PULSE), self.event_loop)
        #self.led_task = asyncio.create_task(self.led(PULSE))

    def notification_led_stop(self):
        if self.led_task:
            logging.info("Stopping Notification LED")
            self.led_loop = False
            self.led_task.result()
            self.led_task = None
