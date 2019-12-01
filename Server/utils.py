import asyncio
from BaseFunctions import AquariumController
ac = AquariumController


def start_calibration(pump_type: str):
    try:
        cal_time = None
        ac.notification_led_pulse()
        ac.button_state()
        if pump_type == 'co2':
            print(f"Running {pump_type}")
            print(f"{pump_type}                      Calibration started.")
            ac.notification_led_flash()
            start = time.time()
            ac.pump_on(pump_type)
            ac.button_state()
            print(f"Stopping {pump_type}")
            print(f"{pump_type}                      Calibration finished.")
            end = time.time()
            ac.pump_off()
            cal_time = round(end - start, 2)
            co2_per_ml = round(cal_time/10, 2)
            print(cal_time)
            ac.notification_led_stop()
    except:
        pass


async def stop_pump(pump_type: str):
    print(f"Stopping {pump_type} Pump")
    ac.pump_off(pump_type)
