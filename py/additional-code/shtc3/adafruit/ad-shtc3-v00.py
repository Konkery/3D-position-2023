import time
import board
import adafruit_shtc3

i2c = board.I2C()   # uses board.SCL and board.SDA
sht = adafruit_shtc3.SHTC3(i2c)

while True:
    temperature, relative_humidity = sht.measurements
    print(f'Значение идентификатора сенсора: {sht._chip_id}')
    print("Temperature: %0.1f C" % temperature)
    print("Humidity: %0.1f %%" % relative_humidity)
    print("")
    time.sleep(1)
