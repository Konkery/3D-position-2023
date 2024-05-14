import time
import struct
import sys

__version__ = '0.1.0'

CHIP_ID = 0xEA # ID датчика WAI - стр 36
I2C_ADDR = 0x68 # Адрес датчика на шине по-умолчанию - стр 14
I2C_ADDR_ALT = 0x69 # Альтернативный адрес датчика на шине - стр 14
ICM20948_BANK_SEL = 0x7f # Регист для переключения банков - стр 54

# Регистры настройки I2C-мастера - стр 68,69 из ICM-20948.pdf
ICM20948_I2C_MST_ODR_CONFIG = 0x00
ICM20948_I2C_MST_CTRL = 0x01
ICM20948_I2C_MST_DELAY_CTRL = 0x02

# Регистры для чтения данных с магнитометра - стр 69,70 из ICM-20948.pdf
ICM20948_I2C_SLV0_ADDR = 0x03
ICM20948_I2C_SLV0_REG = 0x04
ICM20948_I2C_SLV0_CTRL = 0x05
ICM20948_I2C_SLV0_DO = 0x06

# Регистры для настройки гироскопа - стр 59,60 из ICM-20948.pdf
ICM20948_GYRO_SMPLRT_DIV = 0x00
ICM20948_GYRO_CONFIG_1 = 0x01
ICM20948_GYRO_CONFIG_2 = 0x02

# Регистры для настройки акселерометра - стр 63,64 из ICM-20948.pdf
ICM20948_ACCEL_SMPLRT_DIV_1 = 0x10
ICM20948_ACCEL_SMPLRT_DIV_2 = 0x11
ICM20948_ACCEL_INTEL_CTRL = 0x12
ICM20948_ACCEL_WOM_THR = 0x13
ICM20948_ACCEL_CONFIG = 0x14

# Общие настройки датчика - стр 36-38 из ICM-20948.pdf
ICM20948_WHO_AM_I = 0x00
ICM20948_USER_CTRL = 0x03
ICM20948_LP_CONFIG = 0x05
ICM20948_PWR_MGMT_1 = 0x06
ICM20948_PWR_MGMT_2 = 0x07
ICM20948_INT_PIN_CFG = 0x0F

# Регистры вывода данных - стр 42-45 из ICM-20948.pdf
ICM20948_ACCEL_XOUT_H = 0x2D
ICM20948_GYRO_XOUT_H = 0x33
ICM20948_TEMP_OUT_H = 0x39
ICM20948_TEMP_OUT_L = 0x3A
ICM20948_EXT_SLV_SENS_DATA_00 = 0x3B

# Константы для преобразования значений температуры - стр 14 из ICM-20948.pdf
ICM20948_TEMPERATURE_DEGREES_OFFSET = 21
ICM20948_TEMPERATURE_SENSITIVITY = 333.87
ICM20948_ROOM_TEMP_OFFSET = 21

# Регистр выравнивания - стр 63 из ICM-20948.pdf
ODR_ALIGN_EN = 0x09

# Регистры магнитометра - стр 77-80 из ICM-20948.pdf
AK09916_I2C_ADDR = 0x0c
AK09916_CHIP_ID = 0x09
AK09916_WIA = 0x01
AK09916_ST1 = 0x10
AK09916_ST1_DOR = 0b00000010
AK09916_ST1_DRDY = 0b00000001
AK09916_HXL = 0x11
AK09916_ST2 = 0x18
AK09916_ST2_HOFL = 0b00001000
AK09916_CNTL2 = 0x31
AK09916_CNTL2_MODE = 0b00001111
AK09916_CNTL2_MODE_OFF = 0
AK09916_CNTL2_MODE_SINGLE = 1
AK09916_CNTL2_MODE_CONT1 = 2
AK09916_CNTL2_MODE_CONT2 = 4
AK09916_CNTL2_MODE_CONT3 = 6
AK09916_CNTL2_MODE_CONT4 = 8
AK09916_CNTL2_MODE_TEST = 16
AK09916_CNTL3 = 0x32

class ICM20948:
    """Базовые методы чтения/записи."""
    # Запись байта в указанный регистр
    def write(self, reg, value):
        self._bus.write_byte_data(self._addr, reg, value)
        time.sleep(0.0001)

    # Считать один байт с указанного регистра
    def read(self, reg):
        return self._bus.read_byte_data(self._addr, reg)

    # Считать несколько байт с указанного регистра
    def read_bytes(self, reg, length=1):
        return self._bus.read_i2c_block_data(self._addr, reg, length)

    # Переключить банк регистров, если выбран не текущий - стр 76 из ICM-20948.pdf
    def bank(self, value):
        if not self._bank == value:
            self.write(ICM20948_BANK_SEL, value << 4)
            self._bank = value

    # Записать байт в регистр слейв магнитометра - стр 70 из ICM-20948.pdf
    def mag_write(self, reg, value):
        self.bank(3)
        self.write(ICM20948_I2C_SLV0_ADDR, AK09916_I2C_ADDR)  # режим записи
        self.write(ICM20948_I2C_SLV0_REG, reg)
        self.write(ICM20948_I2C_SLV0_DO, value)
        self.write(ICM20948_I2C_SLV0_CTRL, 1 << 7) 
        self.bank(0)

    # Считать один байт со слейв магнитометра - стр 70 из ICM-20948.pdf
    def mag_read(self, reg):
        self.bank(3)
        self.write(ICM20948_I2C_SLV0_ADDR, AK09916_I2C_ADDR | 1 << 7) # переключить в режим чения
        self.write(ICM20948_I2C_SLV0_REG, reg)
        self.write(ICM20948_I2C_SLV0_CTRL, 1 << 7 | 1)  # считать 1 байт
        self.bank(0)
        return self.read(ICM20948_EXT_SLV_SENS_DATA_00)

    # Считать несколько байт со слейв магнитометра - стр 70 из ICM-20948.pdf
    def mag_read_bytes(self, reg, length=1):
        self.bank(3)
        self.write(ICM20948_I2C_SLV0_CTRL, 0x00)
        self.write(ICM20948_I2C_SLV0_ADDR, AK09916_I2C_ADDR | 1 << 7) # переключить в режим чения
        self.write(ICM20948_I2C_SLV0_REG, reg)
        self.write(ICM20948_I2C_SLV0_CTRL, 1 << 7 | (0xF & length)) # считать length байт, но не больше 15ти
        self.bank(0)
        return self.read_bytes(ICM20948_EXT_SLV_SENS_DATA_00, length)

    """Методы настроек гироскопа/акселерометра."""
    # Настройка частоты семплирования гироскопа - стр 59 из ICM-20948.pdf
    def set_gyro_sample_rate(self, rate=50):
        self.bank(2)
        rate = int((1100.0 / rate) - 1)
        self.write(ICM20948_GYRO_SMPLRT_DIV, rate)

    # Настройка рабочего диапазона гироскопа - стр 59 из ICM-20948.pdf
    def set_gyro_full_scale(self, scale=500):
        self.bank(2)
        value = self.read(ICM20948_GYRO_CONFIG_1) & 0b11111001
        value |= {250: 0b00, 500: 0b01, 1000: 0b10, 2000: 0b11}[scale] << 1
        self.write(ICM20948_GYRO_CONFIG_1, value)

    # Настройка фильтра низких частот гироскопа - стр 59,60 из ICM-20948.pdf
    def set_gyro_low_pass(self, enabled=True, mode=5):
        self.bank(2)
        value = self.read(ICM20948_GYRO_CONFIG_1) & 0b10001110
        if enabled:
            value |= (((mode & 0x07) << 4 ) | 0b1)
        self.write(ICM20948_GYRO_CONFIG_1, value)

    # Настройка частоты семплирования акселерометра - стр 63 из ICM-20948.pdf
    def set_accelerometer_sample_rate(self, rate=50):
        self.bank(2)
        rate = int((1125.0 / rate) - 1)
        self.write(ICM20948_ACCEL_SMPLRT_DIV_1, (rate >> 8) & 0xff)
        self.write(ICM20948_ACCEL_SMPLRT_DIV_2, rate & 0xff)

    # Настройка рабочего диапазона акселерометра - стр 64 из ICM-20948.pdf
    def set_accelerometer_full_scale(self, scale=2):
        self.bank(2)
        value = self.read(ICM20948_ACCEL_CONFIG) & 0b11111001
        value |= {2: 0b00, 4: 0b01, 8: 0b10, 16: 0b11}[scale] << 1
        self.write(ICM20948_ACCEL_CONFIG, value)

    # Настройка фильтра низких частот акселерометра - стр 63,64 из ICM-20948.pdf
    def set_accelerometer_low_pass(self, enabled=True, mode=5):
        self.bank(2)
        value = self.read(ICM20948_ACCEL_CONFIG) & 0b10001110
        if enabled:
            value |= (((mode & 0x07) << 4 ) | 0b1)
        self.write(ICM20948_ACCEL_CONFIG, value)

    # Настройка режима частоты семплирования - стр 37 из ICM-20948.pdf
    def setSampleMode(self):
        self.bank(0)
        value = self.read(ICM20948_LP_CONFIG)
        value |= (1 << 4) # Гироскоп семплирует данные с частотой, вычисленной по значению регистра GYRO_SMPLRT_DIV
        value &= ~(1 << 5) # Акселерометр семплирует данные с частотой, ориентируясь на гироскоп
        value |= (1 << 6) # I2C мастер работает в Continuous режиме (это не равно частоте работы магнитометра)
        self.write(ICM20948_LP_CONFIG, value)

    # Ресет ICM20948 - стр 37,38 из ICM-20948.pdf
    def resetIMU(self):
        self.write(ICM20948_PWR_MGMT_1, 0b11000001)
        time.sleep(0.1)
        self.write(ICM20948_PWR_MGMT_1, 1 << 0)
        time.sleep(0.05)
        self.write(ICM20948_PWR_MGMT_2, 0x00)

    # Главная настройка ICM20948 - стр 59,63 из ICM-20948.pdf
    def setupICM(self, gfs=500, gsr=50, glp=3, afs=2, asr=50, alp=3):
        self.bank(0)
        if not self.read(ICM20948_WHO_AM_I) == CHIP_ID:
            raise RuntimeError("Unable to find ICM20948")
        self.resetIMU()
        self.setSampleMode()
        self.bank(2)
        self.write(ODR_ALIGN_EN, 1 << 0) # Вкл выравнивание
        self.set_gyro_full_scale(gfs)
        self.set_gyro_sample_rate(gsr)
        self.set_gyro_low_pass(True, glp)
        self.set_accelerometer_full_scale(afs)
        self.set_accelerometer_sample_rate(asr)
        self.set_accelerometer_low_pass(True, alp)

    """Методы настройки магнитометра"""
    # Проверка бита готовности магнитометра - стр 78 из ICM-20948.pdf
    def magnetometer_ready(self):
        return self.mag_read(AK09916_ST1) & 0x01

    # Ресет магнитометра - стр 80 из ICM-20948.pdf
    def mag_reset(self):
        self.bank(3)
        self.mag_write(AK09916_CNTL3, 1 << 0)
        time.sleep(0.1)

    # Ресет I2C мастера - стр 36 из ICM-20948.pdf
    def i2c_master_reset(self):
        self.bank(0)
        temp = self.read(ICM20948_USER_CTRL)
        self.write(ICM20948_USER_CTRL, temp | 1 << 1) # |0x02
        time.sleep(0.1)

    # Включение I2C мастера - стр 36
    def i2c_master_enable(self):
        self.bank(0)
        temp = self.read(ICM20948_USER_CTRL)
        self.write(ICM20948_USER_CTRL, temp | 1 << 5)
        time.sleep(0.01)
        self.bank(3)
        self.write(ICM20948_I2C_MST_CTRL, 7 << 0) # 400kHz - стр 68 из ICM-20948.pdf
        time.sleep(0.01)

    # Настройка AK09916 - магнитометра
    def setupAK(self, msm):
        self.bank(0)
        self.write(ICM20948_INT_PIN_CFG, 1 << 5 | 1 << 4) # Отключение обхода прерывания - стр 38 из ICM-20948.pdf
        self.i2c_master_reset()
        self.i2c_master_enable()
        self.mag_reset()        
        c = 0
        while not self.mag_read(AK09916_WIA) == AK09916_CHIP_ID:
            time.sleep(0.001)
            c += 1
            if c > 20:
                raise RuntimeError("Unable to find AK09916")

        self._msm = 0x00
        self._msm |= {1: 0b00001, 10: 0b00010, 20: 0b00100, 50: 0b00110, 100: 0b01000}[msm]

    """Методы вывода данных."""
    # Чтение данных с магнитометра
    def read_magnetometer_data(self, timeout=1.0):
        data = self.mag_read_bytes(AK09916_HXL, 8)
        mx, my, mz, st2 = struct.unpack("<hhhh", bytearray(data))
        # Компенсировать измерения согласно константе - стр 13 из ICM-20948.pdf
        mx *= 0.15
        my *= 0.15
        mz *= 0.15
        mag_arr = [mx, my, mz] # Упаковать значения Магнитометра в массив
        return mag_arr

    # Чтение данных с гироскопа/акселерометра
    def read_accelerometer_gyro_data(self):
        self.bank(0)
        data = self.read_bytes(ICM20948_ACCEL_XOUT_H, 12)
        ax, ay, az, gx, gy, gz = struct.unpack(">hhhhhh", bytearray(data))
        self.bank(2)
        # Считать текущий диапазон акселерометра из региста
        scale = (self.read(ICM20948_ACCEL_CONFIG) & 0x06) >> 1
        # Компенсировать измерения согласно текущему рабочему диапазону - стр 12 из ICM-20948.pdf
        gs = [16384.0, 8192.0, 4096.0, 2048.0][scale]
        ax /= gs
        ay /= gs
        az /= gs
        # Считать текущий диапазон гироскопа из региста
        scale = (self.read(ICM20948_GYRO_CONFIG_1) & 0x06) >> 1
        # Компенсировать измерения согласно текущему рабочему диапазону - стр 11 из ICM-20948.pdf
        dps = [131, 65.5, 32.8, 16.4][scale]
        gx /= dps
        gy /= dps
        gz /= dps
        acc_arr = [ax, ay, az] # Упаковать значения Акселерометра в массив
        gyro_arr = [gx, gy, gz] # Упаковать значения Гироскопа в массив
        return acc_arr, gyro_arr

    # Чтение данных с термометра - стр 32 из ICM-20948.pdf
    def read_temperature(self):
        self.bank(0)
        temp_raw_bytes = self.read_bytes(ICM20948_TEMP_OUT_H, 2)
        temp_raw = struct.unpack('>h', bytearray(temp_raw_bytes))[0]
        temperature_deg_c = ((temp_raw - ICM20948_ROOM_TEMP_OFFSET) / ICM20948_TEMPERATURE_SENSITIVITY) + ICM20948_TEMPERATURE_DEGREES_OFFSET
        return temperature_deg_c

    # Последовательное чтение всех датчиков
    def read_full_data(self):
        self.bank(0)
        data = self.read_bytes(ICM20948_ACCEL_XOUT_H, 14)
        ax, ay, az, gx, gy, gz, tmprt = struct.unpack(">hhhhhhh", bytearray(data))
        temp = tmprt # значение температуры термодатчика ICM20948
        self.mag_write(AK09916_CNTL2, self._msm)
        data = self.mag_read_bytes(AK09916_HXL, 8)
        mx, my, mz, st2 = struct.unpack("<hhhh", bytearray(data))
        # масштабировать показания магнитометра в соответствии со значением масштабирующего коэффициента из документации
        mx *= 0.15
        my *= 0.15
        mz *= 0.15
        mag_arr = [mx, my, mz] # Упаковать значения Магнитометра в массив
        self.bank(2)
        # Считать значения для масштабирования показания акселерометра из регистра
        scale = (self.read(ICM20948_ACCEL_CONFIG) & 0x06) >> 1
        # Компенсировать измерения согласно текущему скалирующему показателю - стр 12
        gs = [16384.0, 8192.0, 4096.0, 2048.0][scale]
        ax /= gs
        ay /= gs
        az /= gs
        acc_arr = [ax, ay, az] # Упаковать значения Акселерометра в массив
        # Считать текущий диапазон гироскопа из регистра
        scale = (self.read(ICM20948_GYRO_CONFIG_1) & 0x06) >> 1
        # Компенсировать измерения согласно текущему рабочему диапазону - стр 11
        dps = [131, 65.5, 32.8, 16.4][scale]
        gx /= dps
        gy /= dps
        gz /= dps
        gyro_arr = [gx, gy, gz] # Упаковать значения Гироскопа в массив
        return acc_arr, gyro_arr, mag_arr, temp

    """Инициализация"""    
    def __init__(self, gfs, gsr, glp, afs, asr, alp, msm, i2c_addr=I2C_ADDR, i2c_bus=None):
        self._bank = -1
        self._addr = i2c_addr
        if i2c_bus is None:
            from smbus import SMBus
            self._bus = SMBus(1)
        else:
            self._bus = i2c_bus
        self.setupICM(gfs, gsr, glp, afs, asr, alp)
        self.setupAK(msm)

if __name__ == "__main__":
    """Установка параметров измерений."""
    gyro_full_scale = 500 # Рабочий диапазон гироскопа
    gyro_sample_rate = 50 # Частота сэмплирования гироскопа
    gyro_low_pass = 3 # ФНЧ гироскопа

    accel_full_scale = 2 # Рабочий диапазон акселерометра
    accel_sample_rate = 50 # Частота сэмплирования акселерометра
    accel_low_pass = 3 # ФНЧ акселерометра

    magnetometer_sample_mode = 50 # Частота сэмплирования магнитометра

    imu = ICM20948( gfs=gyro_full_scale\
                   ,gsr=gyro_sample_rate\
                   ,glp=gyro_low_pass\
                   ,afs=accel_full_scale\
                   ,asr=accel_sample_rate
                   ,alp=accel_low_pass\
                   ,msm=magnetometer_sample_mode)

    """Главный цикл выводит данные 2 раза в секунду"""
    try:
        while True:
            acc_arr, gyr_arr, mag_arr, t = imu.read_full_data()
            print("""
Accel: {:05.2f} {:05.2f} {:05.2f}
Gyro:  {:05.2f} {:05.2f} {:05.2f}
Mag:   {:05.2f} {:05.2f} {:05.2f}""".format(
            acc_arr[0], acc_arr[1], acc_arr[2], gyr_arr[0], gyr_arr[1], gyr_arr[2], mag_arr[0], mag_arr[1], mag_arr[2]
        ))

            time.sleep(0.5)
    except (KeyboardInterrupt, SystemExit) as exErr:
        print("\nEnding program")
        sys.exit(0)