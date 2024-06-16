import time
import struct
import sys

__version__ = '0.0.9'

CHIP_ID = 0xEA
I2C_ADDR = 0x68
I2C_ADDR_ALT = 0x69
ICM20948_BANK_SEL = 0x7f            #стр 76

# bank 3
ICM20948_I2C_MST_ODR_CONFIG = 0x00     # стр 68 частота опроса магнитометра по aux-i2c шине    
ICM20948_I2C_MST_CTRL = 0x01           # стр 68 конфигурация  I2C Master модуля   
ICM20948_I2C_MST_DELAY_CTRL = 0x02
ICM20948_I2C_SLV0_ADDR = 0x03          # стр 69 адрес магнитометра как slave-устройства  
ICM20948_I2C_SLV0_REG = 0x04           # стр 69 хранит указание на регистр магнитометра, с которого настроено считывание данных
ICM20948_I2C_SLV0_CTRL = 0x05          # стр 70 предназначен для запуска чтения с магнитометра 
ICM20948_I2C_SLV0_DO = 0x06            # стр 69 предназначен для старта записи в регистр магнитометра  
ICM20948_I2C_SLV1_ADDR = 0x07
ICM20948_I2C_SLV1_REG = 0x08
ICM20948_I2C_SLV1_CTRL = 0x09
ICM20948_I2C_SLV1_DO = 0x0A
ICM20948_EXT_SLV_SENS_DATA_00 = 0x3B    # стр 45 хранит данные, считанные с магнитометра

# bank 2
ICM20948_GYRO_SMPLRT_DIV = 0x00         # стр 59 делитель, который задает ODR гироскопа 
ICM20948_GYRO_CONFIG_1 = 0x01           # стр 59 настраивает ФНЧ и диапазон работы гироскопа
ICM20948_GYRO_CONFIG_2 = 0x02
ODR_ALIGN_EN = 0x09                     # стр 63 включает выравнивание старта опроса датчиков
ICM20948_ACCEL_SMPLRT_DIV_1 = 0x10      # стр 63 старший бит делителя, который задает ODR акселерометра 
ICM20948_ACCEL_SMPLRT_DIV_2 = 0x11      # стр 63 младший бит делителя, который задает ODR акселерометра 
ICM20948_ACCEL_INTEL_CTRL = 0x12
ICM20948_ACCEL_WOM_THR = 0x13
ICM20948_ACCEL_CONFIG = 0x14            # стр 67 настраивает ФНЧ и диапазон работы акселерометра

# Bank 0
ICM20948_WHO_AM_I = 0x00
ICM20948_USER_CTRL = 0x03               # стр 36 предназначен для включения DMP, FIFO, I2C Master 
ICM20948_LP_CONFIG = 0x05               # стр 37 согласно документации переводит датчик(-и) в duty cycle режим; данный режим необходим для работы I2C Master
ICM20948_PWR_MGMT_1 = 0x06              # стр 37 предназначен для выполнения ресета, перехода в Low power режим, настройки тактовой частоты, выкл термометра 
ICM20948_PWR_MGMT_2 = 0x07              # стр 38 предназначен для вкл/выкл осей акселерометра и гироскопа (по-умолчанию все оси вкл)
ICM20948_INT_PIN_CFG = 0x0F


ICM20948_ACCEL_XOUT_H = 0x2D
ICM20948_GRYO_XOUT_H = 0x33

ICM20948_TEMP_OUT_H = 0x39
ICM20948_TEMP_OUT_L = 0x3A

# Offset and sensitivity - defined in electrical characteristics, and TEMP_OUT_H/L of datasheet
ICM20948_TEMPERATURE_DEGREES_OFFSET = 21
ICM20948_TEMPERATURE_SENSITIVITY = 333.87
ICM20948_ROOM_TEMP_OFFSET = 21

AK09916_I2C_ADDR = 0x0c                 # адрес магнитометра
AK09916_CHIP_ID = 0x09
AK09916_WIA = 0x01
AK09916_ST1 = 0x10                      # ст 78 статус готовности данных
AK09916_ST1_DOR = 0b00000010   # Data overflow bit
AK09916_ST1_DRDY = 0b00000001  # Data self.ready bit
AK09916_HXL = 0x11
AK09916_ST2 = 0x18
AK09916_ST2_HOFL = 0b00001000  # Magnetic sensor overflow bit
AK09916_CNTL2 = 0x31
AK09916_CNTL2_MODE = 0b00001111
AK09916_CNTL2_MODE_OFF = 0
AK09916_CNTL2_MODE_SINGLE = 1
AK09916_CNTL2_MODE_CONT1 = 2    # 10Гц
AK09916_CNTL2_MODE_CONT2 = 4    # 20Гц
AK09916_CNTL2_MODE_CONT3 = 6    # 50Гц
AK09916_CNTL2_MODE_CONT4 = 8    # 100Гц
AK09916_CNTL2_MODE_TEST = 16
AK09916_CNTL3 = 0x32                # стр 80 позволяет выполнить ресет магнитометра


class ICM20948:
    def write(self, reg, value):
        """Записать байт в указанный регистр"""
        self._bus.write_byte_data(self._addr, reg, value)
        time.sleep(0.0001)

    def read(self, reg):
        """Считать 1 байт по указанному адресу"""
        return self._bus.read_byte_data(self._addr, reg)

    def read_bytes(self, reg, length=1):
        """Считать указанное количество байт"""
        return self._bus.read_i2c_block_data(self._addr, reg, length)

    def bank(self, value):
        """Переключить банк регистров"""
        if not self._bank == value:
            self.write(ICM20948_BANK_SEL, value << 4)
            self._bank = value

    def twos_comp_two_bytes(self, msb, lsb):
        """Упаковать 2 байта в шорт"""
        a = (msb<<8) + lsb
        if a >= (256*256)//2:
            a = a - (256*256)
        return a

    def mag_write(self, reg, value):
        """Записать байт в регистр SLV0-устройства (магнитометра)"""
        self.bank(3)
        self.write(ICM20948_I2C_SLV0_ADDR, AK09916_I2C_ADDR)  # передача адреса магнитометра, режим записи
        self.write(ICM20948_I2C_SLV0_REG, reg)                # выбор регистра для записи
        self.write(ICM20948_I2C_SLV0_DO, value)               # выполнение записи

    def mag_read(self, reg):
        """Считать 1 байт регистра SLV0-устройства (магнитометра)"""
        self.bank(3)
        self.write(ICM20948_I2C_SLV0_ADDR, AK09916_I2C_ADDR | 1 << 7) # передача адреса магнитометра, режим чтения
        self.write(ICM20948_I2C_SLV0_REG, reg)
        self.write(ICM20948_I2C_SLV0_CTRL, 1 << 7 | 1)  # считать 1 байт
        self.bank(0)
        time.sleep(0.01)
        return self.read(ICM20948_EXT_SLV_SENS_DATA_00)

    def mag_read_bytes(self, reg, length=1):
        """Считать до 24 байт с регистра SLV0-устройства (магнитометра)"""
        self.bank(3)
        self.write(ICM20948_I2C_SLV0_ADDR, AK09916_I2C_ADDR | 1 << 7) # переключить в режим чтения
        self.write(ICM20948_I2C_SLV0_REG, reg)                        # выбор регистра для чтения
        self.write(ICM20948_I2C_SLV0_CTRL, 1 << 7 | length)           # length - сколько байт будет считано length байт (не больше 15ти)
        self.bank(0)
        return self.read_bytes(ICM20948_EXT_SLV_SENS_DATA_00, length) # чтение данных с регистра ICM

    def resetMag(self):
        """Ресет магнитометра"""
        self.bank(3)
        self.mag_write(AK09916_CNTL3, 0b1)
        time.sleep(0.1) # Операция долгая - ожидание - 100мс

    def i2cMasterReset(self):
        """Ресет I2C мастер модуля - вызывать в случае проблем с модулем"""
        self.bank(0)
        temp = self.read(ICM20948_USER_CTRL)
        self.write(ICM20948_USER_CTRL, temp | 0b1)      # Взведение 1-го бита инициирует ресет
        time.sleep(0.1)                                 # Операция долгая - ожидание 100мс
    
    def i2cMasterEnable(self):
        """Включение I2C мастер модуля"""
        self.bank(0)
        value = self.read(ICM20948_USER_CTRL)
        value |= (1 << 5)                       # взведение 5-го бита включает I2C Master модуль
        self.write(ICM20948_USER_CTRL, value)
        self.bank(3)
        self.write(ICM20948_I2C_MST_CTRL, 0x07) # установка частоты aux-i2c шины ~400кГц (ст. 81-82)
        time.sleep(0.01)

    def resetICM(self):
        """Ресет ICM20948"""
        self.bank(0)
        # ресет + переход в sleep-режим + автоматический выбор лучшей тактовой частоты 
        self.write(ICM20948_PWR_MGMT_1, 1 << 7 | 1 << 6 | 1 << 0)
        time.sleep(0.1) # Операция долгая - ожидание 100мс     
        self.write(ICM20948_PWR_MGMT_1, 0b1)
        # Включение всех осей акселерометра и гироскопа 
        self.write(ICM20948_PWR_MGMT_2, 0)

    def checkMagWIA(self):
        """Проверка WIA id магнитометра"""
        tries = 0
        maxTries = 5
        while (tries < maxTries):
            # Пробуем прочитать WIA с магнитометра
            if (self.mag_read(AK09916_WIA) == AK09916_CHIP_ID):
                break # Ответ получен!
            tries += 1
            time.sleep(0.1)

        if (tries == maxTries):
            return False
        return True

    def setupICM(self, gfs=500, gsr=50, glp=3, afs=2, asr=50, alp=3):
        """Настройка ICM20948 - гироскопа и акселерометра"""        
        self.bank(0)
        if not self.read(ICM20948_WHO_AM_I) == CHIP_ID: # Проверка датчика
            raise RuntimeError("Unable to find ICM20948")
        
        self.bank(2)
        # Вкл выравнивание старта опроса
        self.write(ODR_ALIGN_EN, 1 << 0)

        # Установка ODR и dlpf гиро - стр 59
        # 500dps, 50Hz, dlpf on, GYRO_DLPFCFG = 3
        self.set_gyro_full_scale(gfs)
        self.set_gyro_sample_rate(gsr) 
        self.set_gyro_low_pass(True, glp)
        
        # Установка ODR и dlpf акселерометра - стр 63
        # 2g, 50Hz, dlpf on, ACCEL_DLPFCFG = 3
        self.set_accelerometer_full_scale(afs)
        self.set_accelerometer_sample_rate(asr)   
        self.set_accelerometer_low_pass(True, alp)
        
    def setupMag(self, msm=50):
        """Настройка AK09916 - магнитометра"""
        # Ресет магнитометра

        if not self.checkMagWIA():
            raise RuntimeError("Unable to find AK09916 after 5 tries.")

        self.set_magnetometer_sample_mode(msm)  # Настройка режима работы магнитометра
        time.sleep(0.01)
        self.mag_read_bytes(AK09916_HXL, 8)     # первое считывание показаний запускает обновление данных на магнитометре и их передачу I2C Master'ом 

    def read_full_data(self):
        """Считывание данных, полученных со всех датчиков"""
        self.bank(0)
        data = self.read_bytes(ICM20948_ACCEL_XOUT_H, 22)

        # показания акселерометра, гироскопа и термометра: 7 signed short (по 2 байта на ось)
        ax, ay, az, gx, gy, gz, tmprt, lmx, hmx, lmy, hmy, lmz, hmz, st2 = struct.unpack(">hhhhhhhBBBBBBh", bytearray(data))
        # байты магнитометра идут в обратном порядке, поэтому показания рассчитываются вручную складывание 2-байт в одно число 
        mx = self.twos_comp_two_bytes(hmx, lmx)
        my = self.twos_comp_two_bytes(hmy, lmy)
        mz = self.twos_comp_two_bytes(hmz, lmz)

        # масштабирование показаний магнитометра в соответствии со значением масштабирующего коэффициента из документации
        mx *= 0.15
        my *= 0.15
        mz *= 0.15

        mag_arr = [mx, my, mz] # упаковать значения Магнитометра в массив

        self.bank(2)

        scale = (self.read(ICM20948_ACCEL_CONFIG) & 0x06) >> 1          # считывание текущего диапазона работы акселерометра

        gs = [16384.0, 8192.0, 4096.0, 2048.0][scale]                   # масштабирование измерения согласно текущему диапазону - стр 12

        ax /= gs
        ay /= gs
        az /= gs

        acc_arr = [ax, ay, az]                                          # упаковка показаний акселерометра в массив


        scale = (self.read(ICM20948_GYRO_CONFIG_1) & 0x06) >> 1         # считывание текущего диапазона работы гироскопа
        dps = [131, 65.5, 32.8, 16.4][scale]                            # масштабирование измерения согласно текущему диапазону - стр 11

        gx /= dps
        gy /= dps
        gz /= dps

        gyro_arr = [gx, gy, gz]                                         # упаковка значений гироскопа в массив

        return acc_arr, gyro_arr, mag_arr, tmprt

    def set_magnetometer_sample_mode(self, rate=50):
        """Настройка режима работы магнитометра"""
        value = 0x00
        value |= {1: 0b00001, 10: 0b00010, 20: 0b00100, 50: 0b00110, 100: 0b01000}[rate]
        self.mag_write(AK09916_CNTL2, value)

    def setI2CMstSampleRate(self, rate=275):
        """Настройка частоты семплирования I2C Master модулем - стр 63
            Доступны для выбора 1100, 550, 275, 137, 70Гц"""
        self.bank(3)
        value = {1100: 0, 550: 1, 275: 2, 137: 3, 70: 4}[rate]
        self.write(ICM20948_I2C_MST_ODR_CONFIG, value)

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

    def powerOff(self):
        """Выполнять по завершению работы программы"""
        self.mag_write(AK09916_CNTL2, 0b00000)        # выключение магнитометра
        self.bank(0)
        temp = self.read(ICM20948_USER_CTRL)
        self.write(ICM20948_USER_CTRL, temp & 0xDF)   # выключение I2C Master
        self.write(ICM20948_PWR_MGMT_1, 6 << 0)       # установка ICM в sleep режим

    def enableGyro(self, mode=True):
        temp = self.read(ICM20948_PWR_MGMT_2)
        if mode: temp |= 0b00000111
        else:    temp &= 0b11111000
        self.write(ICM20948_PWR_MGMT_2, temp)

    def enableAcc(self, mode=True):
        temp = self.read(ICM20948_PWR_MGMT_2)
        if mode: temp |= 0b00111000
        else:    temp &= 0b11000111
        self.write(ICM20948_PWR_MGMT_2, temp)

    def printDebug(self):
        """Метод предназначенный для отладки: выводит значения основных регистров ICM"""
        self.bank(0)
        print('###### BANK 0 ######')
        print(f'ICM20948_PWR_MGMT_1: {bin(self.read(ICM20948_PWR_MGMT_1))}')
        print(f'ICM20948_PWR_MGMT_2: {bin(self.read(ICM20948_PWR_MGMT_2))}')
        print(f'ICM20948_LP_CONFIG: {bin(self.read(ICM20948_LP_CONFIG))}')
        print(f'ICM20948_USER_CTRL: {bin(self.read(ICM20948_USER_CTRL))}')
        print(f'ICM20948_INT_PIN_CFG: {bin(self.read(ICM20948_INT_PIN_CFG))}')

        self.bank(2)
        print('###### BANK 2 ######')
        print(f'ODR_ALIGN_EN: {bin(self.read(ODR_ALIGN_EN))}')
        print(f'ICM20948_ACCEL_SMPLRT_DIV_1: {bin(self.read(ICM20948_ACCEL_SMPLRT_DIV_1))}')
        print(f'ICM20948_ACCEL_SMPLRT_DIV_2: {bin(self.read(ICM20948_ACCEL_SMPLRT_DIV_2))}')
        print(f'ICM20948_ACCEL_CONFIG: {bin(self.read(ICM20948_ACCEL_CONFIG))}')
        print(f'ICM20948_GYRO_SMPLRT_DIV: {bin(self.read(ICM20948_GYRO_SMPLRT_DIV))}')
        print(f'ICM20948_GYRO_CONFIG_1: {bin(self.read(ICM20948_GYRO_CONFIG_1))}')

        self.bank(3)
        print('###### BANK 3 ######')
        print(f'ICM20948_I2C_MST_CTRL: {bin(self.read(ICM20948_I2C_MST_CTRL))}')
        print(f'ICM20948_I2C_MST_ODR_CONFIG: {bin(self.read(ICM20948_I2C_MST_ODR_CONFIG))}')


    def __init__(self, gfs, gsr, glp, afs, asr, alp, msm, isr=275, i2c_addr=I2C_ADDR, i2c_bus=None):
        self._bank = -1
        self._addr = i2c_addr

        if i2c_bus is None:
            from smbus import SMBus
            self._bus = SMBus(1)
        else:
            self._bus = i2c_bus

        self.resetICM() 
        self.setupICM(gfs, gsr, glp, afs, asr, alp)     # настройка частоты и dlpf акселерометра и гироскопа

        # self.i2cMasterReset()                         # следует вызывать если i2c master завис
        self.i2cMasterEnable()                          # включение I2C Master модуля
        self.setI2CMstSampleRate(rate=isr)              # настройка частоты семплирования  

        if (not self.checkMagWIA()):
            raise RuntimeError("Unable to find AK09916 after 5 tries.")
        self.resetMag()
        self.setupMag(msm=msm)
