import time
import struct

__version__ = '0.0.8'

CHIP_ID = 0xEA
I2C_ADDR = 0x68
I2C_ADDR_ALT = 0x69
ICM20948_BANK_SEL = 0x7f

ICM20948_I2C_MST_ODR_CONFIG = 0x00
ICM20948_I2C_MST_CTRL = 0x01
ICM20948_I2C_MST_DELAY_CTRL = 0x02
ICM20948_I2C_SLV0_ADDR = 0x03
ICM20948_I2C_SLV0_REG = 0x04
ICM20948_I2C_SLV0_CTRL = 0x05
ICM20948_I2C_SLV0_DO = 0x06
ICM20948_EXT_SLV_SENS_DATA_00 = 0x3B

ICM20948_GYRO_SMPLRT_DIV = 0x00
ICM20948_GYRO_CONFIG_1 = 0x01
ICM20948_GYRO_CONFIG_2 = 0x02

# Bank 0
ICM20948_WHO_AM_I = 0x00
ICM20948_USER_CTRL = 0x03
ICM20948_LP_CONFIG = 0x05
ICM20948_PWR_MGMT_1 = 0x06
ICM20948_PWR_MGMT_2 = 0x07
ICM20948_INT_PIN_CFG = 0x0F

ICM20948_ACCEL_SMPLRT_DIV_1 = 0x10
ICM20948_ACCEL_SMPLRT_DIV_2 = 0x11
ICM20948_ACCEL_INTEL_CTRL = 0x12
ICM20948_ACCEL_WOM_THR = 0x13
ICM20948_ACCEL_CONFIG = 0x14
ICM20948_ACCEL_XOUT_H = 0x2D
ICM20948_GRYO_XOUT_H = 0x33

ICM20948_TEMP_OUT_H = 0x39
ICM20948_TEMP_OUT_L = 0x3A

# Offset and sensitivity - defined in electrical characteristics, and TEMP_OUT_H/L of datasheet
ICM20948_TEMPERATURE_DEGREES_OFFSET = 21
ICM20948_TEMPERATURE_SENSITIVITY = 333.87
ICM20948_ROOM_TEMP_OFFSET = 21

ODR_ALIGN_EN = 0x09

AK09916_I2C_ADDR = 0x0c
AK09916_CHIP_ID = 0x09
AK09916_WIA = 0x01
AK09916_ST1 = 0x10
AK09916_ST1_DOR = 0b00000010   # Data overflow bit
AK09916_ST1_DRDY = 0b00000001  # Data self.ready bit
AK09916_HXL = 0x11
AK09916_ST2 = 0x18
AK09916_ST2_HOFL = 0b00001000  # Magnetic sensor overflow bit
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
    def write(self, reg, value):
        """Записать байт в указанный регистр"""
        self._bus.write_byte_data(self._addr, reg, value)
        time.sleep(0.0001)

    def read(self, reg):
        """Считайть 1 байт по указанному адресу"""
        return self._bus.read_byte_data(self._addr, reg)

    def trigger_mag_io(self):
        """Старая функция, включающая на 5мс режим I2C мастера"""
        user = self.read(ICM20948_USER_CTRL)
        self.write(ICM20948_USER_CTRL, user | 0x20)
        time.sleep(0.005)
        self.write(ICM20948_USER_CTRL, user)

    def read_bytes(self, reg, length=1):
        """Считать указанное количество байт, начиная с указанного регистра"""
        return self._bus.read_i2c_block_data(self._addr, reg, length)

    def bank(self, value):
        """Переключить банк регистров, если выбран не текущий - стр 76"""
        if not self._bank == value:
            self.write(ICM20948_BANK_SEL, value << 4)
            self._bank = value
            # print("Установка банка ", value)

    def twos_comp_two_bytes(msb, lsb):
        """Упаковать 2 байта в шорт"""
        a = (msb<<8) + lsb
        if a >= (256*256)//2:
            a = a - (256*256)
        return a

    def mag_write(self, reg, value):
        """Записать байт в регист слейв магнитометра - стр 70"""
        self.bank(3)
        self.write(ICM20948_I2C_SLV0_ADDR, AK09916_I2C_ADDR)  # режим записи
        self.write(ICM20948_I2C_SLV0_REG, reg)
        self.write(ICM20948_I2C_SLV0_DO, value)
        self.write(ICM20948_I2C_SLV0_CTRL, 1 << 7) 
        self.bank(0)

    def mag_read(self, reg):
        """Считать 1 байт со слейв магнитометра - стр 70"""
        self.bank(3)
        self.write(ICM20948_I2C_SLV0_ADDR, AK09916_I2C_ADDR | 1 << 7) # переключить в режим чтения
        self.write(ICM20948_I2C_SLV0_REG, reg)
        self.write(ICM20948_I2C_SLV0_CTRL, 1 << 7 | 1)  # считать 1 байт
        self.bank(0)
        return self.read(ICM20948_EXT_SLV_SENS_DATA_00)

    def mag_read_bytes(self, reg, length=1):
        """Считать до 24 байт со слейв магнитометра - стр 70"""
        self.bank(3)
        self.write(ICM20948_I2C_SLV0_ADDR, AK09916_I2C_ADDR | 1 << 7) # переключить в режим чтения
        self.write(ICM20948_I2C_SLV0_REG, reg)
        self.write(ICM20948_I2C_SLV0_CTRL, 1 << 7 | length) # считать length байт, но не больше 15ти
        self.bank(0)
        return self.read_bytes(ICM20948_EXT_SLV_SENS_DATA_00, length)

    def magnetometer_ready(self):
        """Проверка бита готовности магнитометра - стр 78"""
        return self.mag_read(AK09916_ST1) & 0x01

    def mag_reset(self):
        """Ресет магнитометра - стр 80"""
        self.bank(3)
        self.mag_write(AK09916_CNTL3, 1 << 0)
        time.sleep(0.1) # Операция долгая - ожидание - 100мс

    def i2c_master_reset(self):
        """Ресет I2C мастера - стр 36"""
        self.bank(0)
        temp = self.read(ICM20948_USER_CTRL)
        self.write(ICM20948_USER_CTRL, temp | 1 << 1) # Взводим бит ресета
        time.sleep(0.1) # Операция долгая - ожидание - 100мс
    
    def i2c_master_enable(self):
        """Включение I2C мастера - стр 36"""
        self.bank(0)
        temp = self.read(ICM20948_USER_CTRL)
        self.write(ICM20948_USER_CTRL, temp | 1 << 5)  # С этой строкой не нужен trigger_io, включаем перманентно режим мастера
        time.sleep(0.1) # Операция долгая - ожидание - 100мс
        self.bank(3)
        self.write(ICM20948_I2C_MST_CTRL, 7 << 0) # Настройка частоты работы I2C мастреа - 400kHz, стр 68
        time.sleep(0.1) # Операция долгая - ожидание - 100мс

    def resetIMU(self):
        """Ресет ICM20948"""
        self.bank(0)
        # Включаем ресет и ждём - стр 37
        # Также включаем слип и выбираем подходящий цикл
        self.write(ICM20948_PWR_MGMT_1, 1 << 7 | 1 << 6 | 1 << 0)
        time.sleep(0.1) # Операция долгая - ожидание - 100мс

        # Выбираем наиболее подходящий цикл процессора - стр 37
        self.write(ICM20948_PWR_MGMT_1, 1 << 0)
        # time.sleep(0.05)
        # Включаем все оси акселерометра и гироскопа - стр 38
        self.write(ICM20948_PWR_MGMT_2, 0x00)

    def setupICM(self):
        """Настройка ICM20948 - гироскопа и акселерометра"""        
        self.resetIMU() # Ресетим датчик
        if not self.read(ICM20948_WHO_AM_I) == CHIP_ID: # Проверка датчика
            raise RuntimeError("Unable to find ICM20948")

        self.bank(2)
        # Вкл выравнивание - стр 63
        self.write(ODR_ALIGN_EN, 1 << 0)

        # Установка ODR и dlpf гиро - стр 59
        # 500dps, 50Hz, dlpf on, GYRO_DLPFCFG = 3
        self.set_gyro_full_scale(500)
        self.set_gyro_sample_rate(50)
        self.set_gyro_low_pass(True, 3)
        
        # Установка ODR и dlpf акселерометра - стр 63
        # 2g, 50Hz, dlpf on, ACCEL_DLPFCFG = 3
        self.set_accelerometer_full_scale(2)
        self.set_accelerometer_sample_rate(50)
        self.set_accelerometer_low_pass(True, 3)

    def setupAK(self):
        """Настройка AK09916 - магнитометра"""
        # Ресет магнитометра
        self.mag_reset()

        # Проверка магнитометра
        if not self.mag_read(AK09916_WIA) == AK09916_CHIP_ID:
            raise RuntimeError("Unable to find AK09916.")
         
        self.bank(0)
        self.write(ICM20948_INT_PIN_CFG, 1 << 5|1 << 4) # Отключить обход прерывания - стр 38

        # Ресетим мастера I2C
        self.i2c_master_reset()
        self.i2c_master_enable()

        # Работаем по циклу гироскопа - стр 37
        self.bank(3)
        self.write(ICM20948_LP_CONFIG, 1 << 4)
        time.sleep(0.1)          

        # Настройка режима работы магнитометра - стр 79
        self.mag_write(AK09916_CNTL2, AK09916_CNTL2_MODE_CONT3)
        #self.mag_read_bytes(AK09916_HXL, 8) # необходимо вызывать для чтения данных через метод read_acc_gyro_mag_data()

    def read_magnetometer_data(self, timeout=1.0):
        """Считывание данных с магнитометра"""
        data = self.mag_read_bytes(AK09916_HXL, 8) # По 2 байта на ось - 3 оси + регистр ST2 - стр 79
        # print(data)

        # Чтение регистра ST2 необходимо для 
        # последовательного режима
        # self.mag_read(AK09916_ST2)

        # Данные идут в обратном порядке!
        st2, lz, hz, ly, hy, lx, hx = struct.unpack(">hBBBBBB", bytearray(data)) # распаковать данные

        x = twos_comp_two_bytes(hx,lx)
        y = twos_comp_two_bytes(hy,ly)
        z = twos_comp_two_bytes(hz,lz)
        # Компенсировать измерения согласно константе - стр 13
        x *= 0.15
        y *= 0.15
        z *= 0.15

        return x, y, z

    def read_accelerometer_gyro_data(self):
        """Считывание данных с акселерометра и гироскопа"""
        self.bank(0)
        data = self.read_bytes(ICM20948_ACCEL_XOUT_H, 12) # По 2 байта на ось - 6 осей
        ax, ay, az, gx, gy, gz = struct.unpack(">hhhhhh", bytearray(data)) # распаковать данные - 6 signed short слева направо

        self.bank(2)
        # Считать текущий диапазон акселерометра из региста
        scale = (self.read(ICM20948_ACCEL_CONFIG) & 0x06) >> 1
        # Компенсировать измерения согласно текущему рабочему диапазону - стр 12
        gs = [16384.0, 8192.0, 4096.0, 2048.0][scale]

        ax /= gs
        ay /= gs
        az /= gs

        # Считать текущий диапазон гироскопа из региста
        scale = (self.read(ICM20948_GYRO_CONFIG_1) & 0x06) >> 1
         # Компенсировать измерения согласно текущему рабочему диапазону - стр 11
        dps = [131, 65.5, 32.8, 16.4][scale]

        gx /= dps
        gy /= dps
        gz /= dps

        return ax, ay, az, gx, gy, gz
    
    def read_acc_gyro_mag_data(self):
        self.bank(0)
        data = self.read_bytes(ICM20948_ACCEL_XOUT_H, 22)

        ax, ay, az, gx, gy, gz, tmprt, st2, lmz, hmz, lmy, hmy, lmx, hmx = struct.unpack(">hhhhhhhhBBBBBB", bytearray(data))

        mx = twos_comp_two_bytes(hmx,lmx)
        my = twos_comp_two_bytes(hmy,lmy)
        mz = twos_comp_two_bytes(hmz,lmz)
        self.bank(2)

        # Read accelerometer full scale range and
        # use it to compensate the self.reading to gs
        scale = (self.read(ICM20948_ACCEL_CONFIG) & 0x06) >> 1

        # scale ranges from section 3.2 of the datasheet
        gs = [16384.0, 8192.0, 4096.0, 2048.0][scale]

        ax /= gs
        ay /= gs
        az /= gs

        # Read back the degrees per second rate and
        # use it to compensate the self.reading to dps
        scale = (self.read(ICM20948_GYRO_CONFIG_1) & 0x06) >> 1

        # scale ranges from section 3.1 of the datasheet
        dps = [131, 65.5, 32.8, 16.4][scale]

        gx /= dps
        gy /= dps
        gz /= dps

        # необходимо развернуть байты данных с осей магнитометра
        mx *= 0.15
        my *= 0.15
        mz *= 0.15

        return ax, ay, az, gx, gy, gz, mx, my, mz

    def set_accelerometer_sample_rate(self, rate=50):
        """Настройка частоты семплирования акселерометра - стр 63"""
        self.bank(2)
        rate = int((1125.0 / rate) - 1)
        self.write(ICM20948_ACCEL_SMPLRT_DIV_1, (rate >> 8) & 0xff)
        self.write(ICM20948_ACCEL_SMPLRT_DIV_2, rate & 0xff)

    def set_accelerometer_full_scale(self, scale=2):
        """Настройка рабочего диапазона акселерометра - стр 64"""
        self.bank(2)
        value = self.read(ICM20948_ACCEL_CONFIG) & 0b11111001
        value |= {2: 0b00, 4: 0b01, 8: 0b10, 16: 0b11}[scale] << 1
        self.write(ICM20948_ACCEL_CONFIG, value)

    def set_accelerometer_low_pass(self, enabled=True, mode=5):
        """Настройка фильтра низких частот акселерометра - стр 63,64"""
        self.bank(2)
        value = self.read(ICM20948_ACCEL_CONFIG) & 0b10001110
        if enabled:
            value |= (((mode & 0x07) << 4 ) | 0b1)
        self.write(ICM20948_ACCEL_CONFIG, value)

    def set_gyro_sample_rate(self, rate=50):
        """Настройка частоты семплирования гироскопа - стр 59"""
        self.bank(2)
        rate = int((1100.0 / rate) - 1)
        self.write(ICM20948_GYRO_SMPLRT_DIV, rate)

    def set_gyro_full_scale(self, scale=500):
        """Настройка рабочего диапазона гироскопа - стр 59"""
        self.bank(2)
        value = self.read(ICM20948_GYRO_CONFIG_1) & 0b11111001
        value |= {250: 0b00, 500: 0b01, 1000: 0b10, 2000: 0b11}[scale] << 1
        self.write(ICM20948_GYRO_CONFIG_1, value)

    def set_gyro_low_pass(self, enabled=True, mode=5):
        """Настройка фильтра низких частот гироскопа - стр 59,60"""
        self.bank(2)
        value = self.read(ICM20948_GYRO_CONFIG_1) & 0b10001110
        if enabled:
            value |= (((mode & 0x07) << 4 ) | 0b1)
        self.write(ICM20948_GYRO_CONFIG_1, value)

    def read_temperature(self):
        """Чтение температуры с термометра - стр 14"""
        # PWR_MGMT_1 по умолчанию включает термометр
        self.bank(0)
        temp_raw_bytes = self.read_bytes(ICM20948_TEMP_OUT_H, 2)
        temp_raw = struct.unpack('>h', bytearray(temp_raw_bytes))[0]
        temperature_deg_c = ((temp_raw - ICM20948_ROOM_TEMP_OFFSET) / ICM20948_TEMPERATURE_SENSITIVITY) + ICM20948_TEMPERATURE_DEGREES_OFFSET
        return temperature_deg_c

    def __init__(self, i2c_addr=I2C_ADDR, i2c_bus=None):
        self._bank = -1
        self._addr = i2c_addr

        if i2c_bus is None:
            from smbus import SMBus
            self._bus = SMBus(1)
        else:
            self._bus = i2c_bus

        self.setupICM() # Вынес в отдельную функцию, чтобы не путать что к чему относится

        #self.setupAK()
        # self.write(ICM20948_I2C_MST_CTRL, 0x4D)
        # self.write(ICM20948_I2C_MST_DELAY_CTRL, 0x01)
        

if __name__ == "__main__":
    imu = ICM20948()

    while True:
        #x, y, z = imu.read_magnetometer_data()
        ax, ay, az, gx, gy, gz = imu.read_accelerometer_gyro_data()

        #print("""
#Accel: {:05.2f} {:05.2f} {:05.2f}
#Gyro:  {:05.2f} {:05.2f} {:05.2f}
#Mag:   {:05.2f} {:05.2f} {:05.2f}""".format(
            #ax, ay, az, gx, gy, gz, x, y, z
        #))
        print("""
            Accel: {:05.2f} {:05.2f} {:05.2f}
            Gyro:  {:05.2f} {:05.2f} {:05.2f}
            """.format( ax, ay, az, gx, gy, gz  ))

        time.sleep(1)