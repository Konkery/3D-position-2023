import sys
import os

# Добавить текущий рабочий каталог в sys.path
#sys.path.append(os.getcwd())

# Подключить библиотеки для мат обработки данных и генерации случайных данных
import numpy as np
import math

# Подключить библиотеки для работы с датой/временем
from datetime import datetime
import time 

# ------------------------------------------------------------------------
# Подключить пользовательские модули
# ------------------------------------------------------------------------
# Подключить модуль для работы с датчиком IMU ICM20948
from lib_imu_20948_horizon_rev01_v07 import *
# Подключить модуль для работы с БД Redis
from lib_work_redis_rev01_v01 import *


#------------------------------------------------------------------------
# Создать алиасы индексов соответствующих под-массивов, для удобства обращения
X_IND       = 0
Y_IND       = 1
Z_IND       = 2

ROLL_IND    = 0
PITCH_IND   = 1
YAW_IND     = 2
#------------------------------------------------------------------------

'''
    Класс CalculateAngles обеспечивает поддержку работу с микросхемой IMU20948, предоставляет методы чтения сырых данных
    с сенсоров: Акселерометра, Гироскопа, Магнитометра, Термометра.
    Основное назначение класса предоставить методы расчета углов Эйлера: Roll, Pitch, Yaw.
    Для коммуникаций с внешними компонентами программы проекта, методы класса опираются на глобальный объект
    RedisDB, который представляет собой коннект к базе данных Redis.
    Класс опирается на существующее соединение к Redis, которое должно быть поднято до вызова методов класса.
    
    _opts
'''
class CalculateAngles:
    def __init__(self, _connectDB, _limDataArr, _limWinArr) -> None:
        
        self.ConnectDB     = _connectDB  # коннект к БД Redis
        self.LimWinArr     = _limWinArr  # размер окно усреднения данных
        self.LimDataArr    = _limDataArr # количество 'сырых' значений хранящихся в массивах AccArrRaw/ GyroArrRaw/ MagArrRaw

        self.GyroFullScale  = 1000 # величина настроенного диапазона Гироскопа (+/-) 1000 град/сек
        self.GyroSampleRate = 50   # частота семплирования Гироскопа - 50Hz
        self.GyroLowPass    = 3    # фильтрация Гироскопа ~ 50Hz

        self.AccFullScale   = 2    # величина настроенного диапазона Акселерометра (+/-) 2g
        self.AccSampleRate  = 50   # частота семплирования Акселерометра - 50Hz
        self.AccLowPass     = 3    # фильтрация Акселерометра ~ 50Hz

        self.MagSampleRate  = 50    # частота семплирования Магнитометра - 50Hz

        self.Isr            = 137   # частота ODR в режиме пакетного чтения

        self.ICM20948 = ICM20948( gfs=self.GyroFullScale\
                                 ,gsr=self.GyroSampleRate\
                                 ,glp=self.GyroLowPass\
                                 ,afs=self.AccFullScale\
                                 ,asr=self.AccSampleRate
                                 ,alp=self.AccLowPass\
                                 ,msm=self.MagSampleRate\
                                 ,isr=self.Isr) # инстанцировать модуль для работы с датчиком IMU ICM20948
        
        # Набор итоговых тройных массивов для хранения  'сырых' данных от трех (3) сенсоров, по трем (3) осям
        self.AccArrRaw  = [ [0]*self.LimDataArr, [0]*self.LimDataArr, [0]*self.LimDataArr ] # заполнить массив '0' значениями
        self.GyroArrRaw = [ [0]*self.LimDataArr, [0]*self.LimDataArr, [0]*self.LimDataArr ] # заполнить массив '0' значениями
        self.MagArrRaw  = [ [0]*self.LimDataArr, [0]*self.LimDataArr, [0]*self.LimDataArr ] # заполнить массив '0' значениями

        # Набор итоговых тройных массивов для хранения усредненных данных от трех (3) сенсоров, по трем (3) осям
        self.AccArrAvg   = [ [0]*self.LimDataArr, [0]*self.LimDataArr, [0]*self.LimDataArr ] # заполнить массив '0' значениями
        self.GyroArrAvg  = [ [0]*self.LimDataArr, [0]*self.LimDataArr, [0]*self.LimDataArr ] # заполнить массив '0' значениями
        self.MagArrAvg   = [ [0]*self.LimDataArr, [0]*self.LimDataArr, [0]*self.LimDataArr ] # заполнить массив '0' значениями

        self.TEMP_SENSITIVITY = 333.87  # константа необходимая для расчета температуры в цельсиях
        self.TEMP_OFFSET      = 0       # константа хранит калибровочное смещение термометра

        self.TempArr  = [0]*self.LimDataArr # Массив текущих значений встроенного в ICM20948 термодатчика

        # Поля для хранения времени для вычисления угла
        self.TimeNewAngle=time.time()
        self.TimeOldAngle=time.time()
        self.TimeDeltaAngle = 0
        
        # Коэффициент альфа, для расчета углов в комплементарном фильтре
        self.Alpha = 0.98

        # Углы Эйлера полученные с помощью Акселерометра
        self.AccArrAngle  = [ [0]*self.LimDataArr, [0]*self.LimDataArr, [0]*self.LimDataArr ]
        # Углы Эйлера полученные с помощью Гироскопа
        self.GyroArrAngle = [ [0]*self.LimDataArr, [0]*self.LimDataArr, [0]*self.LimDataArr ]
        # Углы Эйлера полученные с помощью комплементарного фильтра слияния
        self.CompArrAngle = [ [0]*self.LimDataArr, [0]*self.LimDataArr, [0]*self.LimDataArr ]

    '''
        Метод ReadDateICM20948 выполняет чтение данных с сенсоров ICM20948, обновляет массивы сырых данных
        необходимых для вычисления углов Эйлера и построения графиков.
    '''
    def ReadDataICM20948(self) -> None:
        self.TimeNewAngle = time.time() # Зафиксировать время считывания данных, для последующего интегрирования значений Гироскопа

        # Набор вспомогательных переменных необходимых для стыковки формата данных отдаваемых библиотекой IMU20948
        acc   = [0, 0, 0] # массив 'сырых', мгновенных значений  Акселерометра, по одному значению на каждую ось [X_IND, Y_IND, Z_IND]
        gyro  = [0, 0, 0] # массив 'сырых', мгновенных значений  Гироскопа,     по одному значению на каждую ось [X_IND, Y_IND, Z_IND]
        mag   = [0, 0, 0] # массив 'сырых', мгновенных значений  Магнитометра,  по одному значению на каждую ось [X_IND, Y_IND, Z_IND]
        temp  = 0         # содержит сырое значение термометра
        
        # Считать 'сырые' данные от Акселерометра, Гироскопа, Магнитометра, Термометра IMU20948
        acc, gyro, mag, temp = self.ICM20948.read_full_data() # считать показания датчиков модуля ICM20948

        temp = (temp - self.TEMP_OFFSET)/self.TEMP_SENSITIVITY + 21.0 # формула получения температуры в цельсиях (см. док на ICM20948)

        # Добавить одиночное показание Термодатчика в массив
        self.TempArr.append(temp)
        # Отслеживать размер массива 'сырых' данных
        if len(self.TempArr) > self.LimDataArr:
            self.TempArr.pop(0)
        
        # Добавить данные от трех датчиков по трем осям в массив 'сырых' данных и усредненных
        for i in range(3):
            # Добавить 'сырые' данные Акселерометра
            self.AccArrRaw[i].append(acc[i])
            # Отслеживать размер массива 'сырых' данных
            if len(self.AccArrRaw[i]) > self.LimDataArr:
                self.AccArrRaw[i].pop(0)

            # Добавить 'сырые' данные Гироскопа
            self.GyroArrRaw[i].append(gyro[i])
            # Отслеживать размер массива 'сырых' данных
            if len(self.GyroArrRaw[i]) > self.LimDataArr:
                self.GyroArrRaw[i].pop(0)
            
            # Добавить 'сырые' данные Магнитометра
            self.MagArrRaw[i].append(mag[i])
            # Отслеживать размер массива 'сырых' данных
            if len(self.MagArrRaw[i]) > self.LimDataArr:
                self.MagArrRaw[i].pop(0)
            
            # Обновить усредненные данные по трем осям трех датчиков
            acc_avg  = sum( self.AccArrRaw[i][-self.LimWinArr:]) / self.LimWinArr
            gyro_avg = sum(self.GyroArrRaw[i][-self.LimWinArr:]) / self.LimWinArr
            mag_avg  = sum( self.MagArrRaw[i][-self.LimWinArr:]) / self.LimWinArr

            # Добавить усредненные данные Акселерометра
            self.AccArrAvg[i].append(acc_avg)
            # Отслеживать размер массива усредненных данных
            if len(self.AccArrAvg[i]) > self.LimDataArr:
                self.AccArrAvg[i].pop(0)
            
            # Добавить усредненные данные Гироскопа
            self.GyroArrAvg[i].append(gyro_avg)
            # Отслеживать размер массива усредненных данных
            if len(self.GyroArrAvg[i]) > self.LimDataArr:
                self.GyroArrAvg[i].pop(0)

            # Добавить усредненные данные Магнитометра
            self.MagArrAvg[i].append(mag_avg)
            # Отслеживать размер массива усредненных данных
            if len(self.MagArrAvg[i]) > self.LimDataArr:
                self.MagArrAvg[i].pop(0)

    '''
        Метод 'UpdateAngleEuler' выполняет расчет углов Эйлера как индивидуально по каналам Акселерометра,
        Гироскопа, комплементарного Фильтра.
        Рассчитанные значения сохраняются в БД Redis. Метод полагается на глобальный объект хранящий 
        коннект к БД Redis, который должен существовать к моменту вызова метода.
    '''
    def UpdateAngleEuler(self) -> None:

        # Вычислить разницу времени между получением данных с IMU сенсора
        self.TimeDeltaAngle = self.TimeNewAngle - self.TimeOldAngle
        self.TimeOldAngle = self.TimeNewAngle
        dt = self.TimeDeltaAngle

        # Рассчитать углы Эйлера от канала акселерометра
        self.AccArrAngle[ROLL_IND].append(math.degrees(math.atan2(self.AccArrRaw[Y_IND][-1], self.AccArrRaw[Z_IND][-1])))
        self.AccArrAngle[PITCH_IND].append(math.degrees(math.atan2(self.AccArrRaw[X_IND][-1], self.AccArrRaw[Z_IND][-1])))
        
        # Отслеживать размер массива 'сырых' данных
        if len(self.AccArrAngle[ROLL_IND]) > self.LimDataArr:
            self.AccArrAngle[ROLL_IND].pop(0)
            self.AccArrAngle[PITCH_IND].pop(0)

        # Рассчитать углы Эйлера от канала гироскопа
        self.GyroArrAngle[ROLL_IND].append( self.GyroArrAngle[ROLL_IND][-1]+ self.GyroArrRaw[X_IND][-1] * dt)
        self.GyroArrAngle[PITCH_IND].append( self.GyroArrAngle[PITCH_IND][-1]- self.GyroArrRaw[Y_IND][-1] * dt)
        self.GyroArrAngle[YAW_IND].append( self.GyroArrAngle[YAW_IND][-1]+ self.GyroArrRaw[Z_IND][-1] * dt)
        # Отслеживать размер массива 'сырых' данных
        if len(self.GyroArrAngle[ROLL_IND]) > self.LimDataArr:
            self.GyroArrAngle[ROLL_IND].pop(0)
            self.GyroArrAngle[PITCH_IND].pop(0)
            self.GyroArrAngle[YAW_IND].pop(0)

        # Рассчитать углы Эйлера комплиментарным фильтром
        self.CompArrAngle[ROLL_IND].append( (self.Alpha)* (self.GyroArrAngle[ROLL_IND][-1])  + (1-self.Alpha)*self.AccArrAngle[ROLL_IND][-1] )
        self.CompArrAngle[PITCH_IND].append( (self.Alpha)*(self.GyroArrAngle[PITCH_IND][-1]) + (1-self.Alpha)*self.AccArrAngle[PITCH_IND][-1] )
        self.CompArrAngle[YAW_IND].append(self.GyroArrAngle[YAW_IND][-1] )
        if len(self.CompArrAngle[ROLL_IND]) > self.LimDataArr:
             self.CompArrAngle[ROLL_IND].pop(0)
             self.CompArrAngle[PITCH_IND].pop(0)
             self.CompArrAngle[YAW_IND].pop(0)
    
    '''
        Метод 'WriteDatefromDB' сохраняет все рабочие данные вырабатываемые в методах класса
        в БД Redis.
    '''
    def WriteDataDB(self) -> None:

        # Сохранить массив сырых данных IMU в БД
        ImuListRawKey = ('AccArrRaw', 'GyroArrRaw', 'MagArrRaw')
        ImuListRawData = (self.AccArrRaw, self.GyroArrRaw, self.MagArrRaw)
        WriteValJSONtoDB( self.ConnectDB, ImuListRawKey, ImuListRawData )

        # Сохранить массив сырых усредненных данных IMU в БД
        ImuListAvgKey = ('AccArrAvg', 'GyroArrAvg', 'MagArrAvg')
        ImuListAvgData = (self.AccArrAvg, self.GyroArrAvg, self.MagArrAvg)
        WriteValJSONtoDB(self.ConnectDB, ImuListAvgKey, ImuListAvgData)

        # Сохранить массивы со значениями углов Эйлера в БД
        AngelListKey = ('AccArrAngle', 'GyroArrAngle', 'CompArrAngle')
        AngelListData = (self.AccArrAngle, self.GyroArrAngle, self.CompArrAngle)
        WriteValJSONtoDB( self.ConnectDB, AngelListKey, AngelListData )

        # Сохранить массив со значениями температуры IMU в БД
        TempListKey = ('TempArr',)
        TempListData = (self.TempArr,)
        WriteValJSONtoDB(self.ConnectDB, TempListKey, TempListData)   

        # Сохранить значение дельты времени обращений к IMU в БД
        TimeDeltaAngleKey = ('TimeDeltaAngle',)
        TimeDeltaAngleData = (self.TimeDeltaAngle,)
        WriteValJSONtoDB(self.ConnectDB, TimeDeltaAngleKey, TimeDeltaAngleData)

        # Сохранить значение коэффициента Альфа, используемого при вычисления значений углов Эйлера в фильтре слияния
        AlphaKey = ('AlphaKey',)
        AlphaData = (self.Alpha,)
        WriteValJSONtoDB(self.ConnectDB, AlphaKey, AlphaData)

    '''
        Метод UpdateAll выполняет функцию агрегатора, который объединяет все методы класса, которые
        должны быть вызваны для пересчета углов Эйлела.
        Данный метод, предоставляет удобный способ вызвать все функции участвующие в пересчете углов 
        Эйлера в специальной оберткой имитирующей асинхронную функцию setInterval в языке JavaScript.
    '''
    def UpdateAll(self) -> None:
        self.ReadDataICM20948()
        self.UpdateAngleEuler()
        self.WriteDataDB()