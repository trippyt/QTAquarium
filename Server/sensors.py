# https://forum.dexterindustries.com/t/solved-dht-sensor-occasionally-returning-spurious-values/2939/5
import numpy
from time import sleep
from datetime import datetime

from hardwarenew import Hardware
import json

hardware = Hardware()


# function which eliminates the noise
# by using a statistical model
# we determine the standard normal deviation and we exclude anything that goes beyond a threshold
# think of a probability distribution plot - we remove the extremes
# the greater the std_factor, the more "forgiving" is the algorithm with the extreme values
def eliminateNoise(values, std_factor=2):
    mean = numpy.mean(values)
    standard_deviation = numpy.std(values)

    if standard_deviation == 0:
        return values

    final_values = [element for element in values if element > mean - std_factor * standard_deviation]
    final_values = [element for element in final_values if element < mean + std_factor * standard_deviation]

    return final_values


# function for processing the data
# filtering, periods of time, yada yada


def read_sensors():
    seconds_window = 5  # after this many second we make a record
    filtered = []
    while True:
        samples = {
            'room_temp_c': [],
            'room_temp_f': [],
            'room_humidity': [],
            'tank_temp_c': [],
            'tank_temp_f': []
        }
        for second in range(seconds_window):
            dht = hardware.room_temperature()
            if dht:
                print('Values 1:', dht)
                samples['room_temp_c'].append(dht['temp_c'])
                samples['room_temp_f'].append(dht['temp_f'])
                samples['room_humidity'].append(dht['humidity'])

            ds18b20 = hardware.read_temperature('temp_tank')
            if ds18b20:
                print('Values 2:', ds18b20)
                samples['tank_temp_c'].append(ds18b20[0])
                samples['tank_temp_f'].append(ds18b20[1])

            sleep(1)

        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print('Samples Before:')
        print(samples)

        # Calculate mean of samples
        for sample_type in samples:
            samples[sample_type] = numpy.mean(eliminateNoise(samples[sample_type]))

        print('Samples After:')
        print(samples)
        print()

        # TODO: Write to DB here
        filtered.append(samples)
        with open('sensors.json', 'w') as sensor_json:
            json.dump(filtered, sensor_json, indent=4, sort_keys=True)


if __name__ == "__main__":
    read_sensors()
