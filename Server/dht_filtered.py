#import grovepi
import math
import numpy
import threading
from time import sleep
from datetime import datetime

from AquariumHardware2 import Hardware

hardware = Hardware()

#sensor = 4  # The Sensor goes on digital port 4.
# temp_humidity_sensor_type
#blue = 0  # The Blue colored sensor.
#white = 1  # The White colored sensor.

filtered_temperature_c = []  # here we keep the temperature C values after removing outliers
filtered_temperature_f = []  # here we keep the temperature F values after removing outliers
filtered_humidity = []  # here we keep the filtered humidity values after removing the outliers

lock = threading.Lock()  # we are using locks so we don't have conflicts while accessing the shared variables
event = threading.Event()  # we are using an event so we can close the thread as soon as KeyboardInterrupt is raised

dht = hardware.room_temperature()


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


def readingValues():
    seconds_window = 10  # after this many second we make a record
    values = []

    while not event.is_set():
        counter = 0
        while counter < seconds_window and not event.is_set():
            temp_c = None
            temp_f = None
            humidity = None
            try:
                [temp_c, temp_f, humidity] = (dht['temp_c'], dht['humidity'])

            except IOError:
                print("we've got IO error")

            if math.isnan(temp_c) is False and math.isnan(temp_f) is False and math.isnan(humidity) is False:
                values.append({"temp_c": temp_c, "temp_f": temp_f, "hum": humidity})
                counter += 1
            # else:
            # print("we've got NaN")

            sleep(1)

        lock.acquire()
        filtered_temperature_c.append(numpy.mean(eliminateNoise([x["temp_c"] for x in values])))
        filtered_temperature_f.append(numpy.mean(eliminateNoise([x["temp_f"] for x in values])))

        filtered_humidity.append(numpy.mean(eliminateNoise([x["hum"] for x in values])))
        lock.release()

        values = []


def Main():
    # here we start the thread
    # we use a thread in order to gather/process the data separately from the printing proceess
    data_collector = threading.Thread(target=readingValues)
    data_collector.start()

    while not event.is_set():
        if len(filtered_temperature_c) > 0:  # or we could have used filtered_humidity instead
            lock.acquire()

            # here you can do whatever you want with the variables: print them, file them out, anything
            temperature_c = filtered_temperature_c.pop()
            temperature_f = filtered_temperature_f.pop()
            humidity = filtered_humidity.pop()
            print('{},{:.01f},{:.01f},{:.01f}'.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), temperature_c, temperature_f, humidity))

            lock.release()

        # wait a second before the next check
        sleep(1)

    # wait until the thread is finished
    data_collector.join()


if __name__ == "__main__":
    try:
        Main()

    except KeyboardInterrupt:
        event.set()
