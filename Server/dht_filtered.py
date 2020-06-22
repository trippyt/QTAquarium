#import grovepi
import math
import numpy
from loguru import logger
from time import sleep
from datetime import datetime


from AquariumHardware2 import Hardware

hardware = Hardware()

filtered_room_temperature_c = []  # here we keep the temperature C values after removing outliers
filtered_room_temperature_f = []  # here we keep the temperature F values after removing outliers
filtered_room_humidity = []  # here we keep the filtered humidity values after removing the outliers

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
    room_counter = 0
    tank_counter = 0
    while room_counter < seconds_window:
        unfiltered_room_temp_c = None
        unfiltered_room_temp_f = None
        unfiltered_room_humidity = None
        filtered_room_temp_c = None
        filtered_room_temp_f = None
        filtered_room_humidity = None
        unfiltered_tank_temp_c = None
        unfiltered_tank_temp_f = None
        unfiltered_tank_humidity = None
        filtered_tank_temp_c = None
        filtered_tank_temp_f = None
        filtered_tank_humidity = None
        try:
            dht = hardware.room_temperature()
            if dht:
                [unfiltered_room_temp_c, unfiltered_room_temp_f, unfiltered_room_humidity, _] = dht.values()

                if math.isnan(unfiltered_room_temp_c) is False and math.isnan(unfiltered_room_temp_f) is False\
                        and math.isnan(unfiltered_room_humidity) is False:
                    values.append({"temp_c": unfiltered_room_temp_c, "temp_f": unfiltered_room_temp_f, "hum": unfiltered_room_humidity})
                    room_counter += 1
                # else:
                # print("we've got NaN")
            ds18b20 = hardware.read_temperature()
            if ds18b20:
                [unfiltered_tank_temp_c, unfiltered_tank_temp_f] = ds18b20.values()
                if math.isnan(unfiltered_tank_temp_c) is False and math.isnan(unfiltered_room_temp_f) is False:
                    values.append({"temp_c": unfiltered_tank_temp_c, "temp_f": unfiltered_tank_temp_f})
                    tank_counter += 1

        except IOError:
            print("we've got IO error")

        except Exception as error:
            logger.exception(error.args[0])

        sleep(1)

        filtered_room_temperature_c.append(numpy.mean(eliminateNoise([x["filtered_room_temp_c"] for x in values])))
        filtered_room_temperature_f.append(numpy.mean(eliminateNoise([x["unfiltered_room_temp_f"] for x in values])))
        filtered_room_humidity.append(numpy.mean(eliminateNoise([x["hum"] for x in values])))

        values = []


def Main():
    # here we start the thread
    # we use a thread in order to gather/process the data separately from the printing proceess
    data_collector = threading.Thread(target=readingValues)
    data_collector.start()

    while not event.is_set():
        if len(filtered_room_temperature_c) > 0:  # or we could have used filtered_humidity instead
            lock.acquire()

            # here you can do whatever you want with the variables: print them, file them out, anything
            temperature_c = filtered_room_temperature_c.pop()
            temperature_f = filtered_room_temperature_f.pop()
            humidity = filtered_room_humidity.pop()
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
