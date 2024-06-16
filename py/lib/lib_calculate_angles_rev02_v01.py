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
    Аргументы:
        -> _connectDB  - объект соединения с БД RedisDB
        -> _limDataArr - ограничение на размер массивов хранящие оперативный набор сырых данных Акселерометра, Гироскопа, Магнитометра
        -> _limWinArr  - ограничение на размер окна усреднения данных
        -> _optIMU - опции для работы с микросхемой IMU20948
        -> _optAng - набор значений смещений (ошибок) по осям X, Y, Z требуемые для получения точных данных от Акселерометра, Гироскопа, Магнитометра
'''
class CalculateAngles:
    def __init__(self, _connectDB) -> None:

        self.ConnectDB  = _connectDB  # коннект к БД Redis

        self.AccOffsetX = 0   # default, смещение Акселерометра по оси Х
        self.AccOffsetY = 0   # default, смещение Акселерометра по оси Y
        self.AccOffsetZ = 0   # default, смещение Акселерометра по оси Z

        self.GyrOffsetX = 0   # default, смещение Гироскопа по оси X
        self.GyrOffsetY = 0   # default, смещение Гироскопа по оси Y
        self.GyrOffsetZ = 0   # default, смещение Гироскопа по оси Z

        self.MagOffsetX = 0   # default, смещение Магнитометра по оси X
        self.MagOffsetY = 0   # default, смещение Магнитометра по оси Y
        self.MagOffsetZ = 0   # default, смещение Магнитометра по оси Z

        self.Gfs        = 250 # default, диапазон работы Гироскопа 
        self.Gsr        = 50  # default, частота семплирования Гироскопа
        self.Glp        = 3   # default, частота фильтра нижних частот Гироскопа

        self.Afs        = 2   # default, диапазон работы Акселерометра 
        self.Asr        = 50  # default, частота семплирования Акселерометра
        self.Alp        = 3   # default, частота фильтра нижних частот Акселерометра

        self.Msr        = 50  # default, частота семплирования Магнитометра

        self.Isr        = 137 # default, частота семплирования пакетного считывания данных со всех трех сенсоров IMU

        self.TempSensitivity = 333.87  # константа необходимая для расчета температуры в цельсиях
        self.TempOffset      = 0       # константа хранит калибровочное смещение термометра

        self.ReadDataDB() # инициализировать поля класса значениями хранящимися в БД

        self.ICM20948   = ICM20948(   gfs = self.Gfs\
                                    , gsr = self.Gsr\
                                    , glp = self.Glp\
                                    , afs = self.Afs\
                                    , asr = self.Asr\
                                    , alp = self.Alp\
                                    , msm = self.Msr\
                                    , isr = self.Isr\
                                   ) # инстанцировать модуль датчика IMU ICM20948
        
        self.LimDataArr = 4 # default, количество 'сырых' значений хранящихся в массивах AccArrRaw/ GyroArrRaw/ MagArrRaw
        self.LimWinArr  = 50 # default, размер окно усреднения данных

        # Набор итоговых тройных массивов для хранения  'сырых' данных от трех (3) сенсоров, по трем (3) осям
        self.AccArrRaw = [ [0]*self.LimDataArr, [0]*self.LimDataArr, [0]*self.LimDataArr ] # заполнить массив '0' значениями
        self.GyrArrRaw = [ [0]*self.LimDataArr, [0]*self.LimDataArr, [0]*self.LimDataArr ] # заполнить массив '0' значениями
        self.MagArrRaw = [ [0]*self.LimDataArr, [0]*self.LimDataArr, [0]*self.LimDataArr ] # заполнить массив '0' значениями

        # Набор итоговых тройных массивов для хранения усредненных данных от трех (3) сенсоров, по трем (3) осям
        self.AccArrAvg = [ [0]*self.LimDataArr, [0]*self.LimDataArr, [0]*self.LimDataArr ] # заполнить массив '0' значениями
        self.GyrArrAvg = [ [0]*self.LimDataArr, [0]*self.LimDataArr, [0]*self.LimDataArr ] # заполнить массив '0' значениями
        self.MagArrAvg = [ [0]*self.LimDataArr, [0]*self.LimDataArr, [0]*self.LimDataArr ] # заполнить массив '0' значениями

        self.TempArrRaw  = [0]*self.LimDataArr # Массив текущих значений встроенного в ICM20948 термодатчика

        # Поля для хранения времени для вычисления угла
        self.TimeNewAngle=time.time()
        self.TimeOldAngle=time.time()
        self.TimeDeltaAngle = 0
        
        self.Alpha = 0.98 # default, коэффициент альфа, для расчета углов в комплементарном фильтре

        # Углы Эйлера полученные с помощью Акселерометра
        self.AccArrAngle = [ [0]*self.LimDataArr, [0]*self.LimDataArr, [0]*self.LimDataArr ]
        # Углы Эйлера полученные с помощью Гироскопа
        self.GyrArrAngle = [ [0]*self.LimDataArr, [0]*self.LimDataArr, [0]*self.LimDataArr ]
        # Углы Эйлера полученные с помощью комплементарного фильтра слияния
        self.ComArrAngle = [ [0]*self.LimDataArr, [0]*self.LimDataArr, [0]*self.LimDataArr ]

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

        temp = (temp - self.TempOffset)/self.TempSensitivity + 21.0 # формула получения температуры в цельсиях (см. док на ICM20948)

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
            self.GyrArrRaw[i].append(gyro[i])
            # Отслеживать размер массива 'сырых' данных
            if len(self.GyrArrRaw[i]) > self.LimDataArr:
                self.GyrArrRaw[i].pop(0)
            
            # Добавить 'сырые' данные Магнитометра
            self.MagArrRaw[i].append(mag[i])
            # Отслеживать размер массива 'сырых' данных
            if len(self.MagArrRaw[i]) > self.LimDataArr:
                self.MagArrRaw[i].pop(0)
            
            # Обновить усредненные данные по трем осям трех датчиков
            acc_avg  = sum( self.AccArrRaw[i][-self.LimWinArr:]) / self.LimWinArr
            gyro_avg = sum(self.GyrArrRaw[i][-self.LimWinArr:]) / self.LimWinArr
            mag_avg  = sum( self.MagArrRaw[i][-self.LimWinArr:]) / self.LimWinArr

            # Добавить усредненные данные Акселерометра
            self.AccArrAvg[i].append(acc_avg)
            # Отслеживать размер массива усредненных данных
            if len(self.AccArrAvg[i]) > self.LimDataArr:
                self.AccArrAvg[i].pop(0)
            
            # Добавить усредненные данные Гироскопа
            self.GyrArrAvg[i].append(gyro_avg)
            # Отслеживать размер массива усредненных данных
            if len(self.GyrArrAvg[i]) > self.LimDataArr:
                self.GyrArrAvg[i].pop(0)

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
        self.GyrArrAngle[ROLL_IND].append( self.GyrArrAngle[ROLL_IND][-1] + self.GyrArrRaw[X_IND][-1] * dt)
        self.GyrArrAngle[PITCH_IND].append( self.GyrArrAngle[PITCH_IND][-1] - self.GyrArrRaw[Y_IND][-1] * dt)
        self.GyrArrAngle[YAW_IND].append( self.GyrArrAngle[YAW_IND][-1] + self.GyrArrRaw[Z_IND][-1] * dt)
        # Отслеживать размер массива 'сырых' данных
        if len(self.GyrArrAngle[ROLL_IND]) > self.LimDataArr:
            self.GyrArrAngle[ROLL_IND].pop(0)
            self.GyrArrAngle[PITCH_IND].pop(0)
            self.GyrArrAngle[YAW_IND].pop(0)

        # Рассчитать углы Эйлера комплиментарным фильтром
        self.ComArrAngle[ROLL_IND].append( (self.Alpha)* (self.GyrArrAngle[ROLL_IND][-1])  + (1-self.Alpha)*self.AccArrAngle[ROLL_IND][-1] )
        self.ComArrAngle[PITCH_IND].append( (self.Alpha)*(self.GyrArrAngle[PITCH_IND][-1]) + (1-self.Alpha)*self.AccArrAngle[PITCH_IND][-1] )
        self.ComArrAngle[YAW_IND].append(self.GyrArrAngle[YAW_IND][-1] )
        if len(self.ComArrAngle[ROLL_IND]) > self.LimDataArr:
             self.ComArrAngle[ROLL_IND].pop(0)
             self.ComArrAngle[PITCH_IND].pop(0)
             self.ComArrAngle[YAW_IND].pop(0)
    
    '''
        Метод 'ReadDataDB' загружает из БД Redis требуемые для работы класса параметры.
        После перехода на обмен данными между блокнотами посредством БД Redis, стало понятно
        что предпочтительно все глобальные параметры нужные для работы данного класса и
        блокнотов в целом передавать через ключи БД.
        В связи с этим появилась потребность в данном методе.
        Аргументов у метода как таковых нет, но как и метод 'WriteDataDB', данный метод использует
        функцию 'ReadValJSONfromDB' python модуля 'lib_work_redis_rev01_v01' и поля класса, которые
        он инициализирует через вспомогательные локальные переменные.

    '''
    def ReadDataDB(self) -> None:

        # Инициализировать поля класса хранящие смещения (ошибку) Акселерометра
        ImuListKeyAccOffset     = ('AccOffsetX','AccOffsetY', 'AccOffsetZ')
        ImuListDataAccOffset    = [self.AccOffsetX, self.AccOffsetY, self.AccOffsetZ]
        ReadValJSONfromDB( self.ConnectDB, ImuListKeyAccOffset, ImuListDataAccOffset )

        # Инициализировать поля класса хранящие смещения (ошибку) Гироскопа
        ImuListKeyGyrOffset     = ('GyrOffsetX', 'GyrOffsetY', 'GyrOffsetZ')
        ImuListDataGyrOffset    = [self.GyrOffsetX, self.GyrOffsetY, self.GyrOffsetZ]
        ReadValJSONfromDB( self.ConnectDB, ImuListKeyGyrOffset, ImuListDataGyrOffset )

        # Инициализировать поля класса хранящие смещения (ошибку) Магнитометра
        ImuListKeyMagOffset     = ('MagOffsetX', 'MagOffsetY', 'MagOffsetZ')
        ImuListDataMagOffset    = [self.MagOffsetX, self.MagOffsetY, self.MagOffsetZ]
        ReadValJSONfromDB( self.ConnectDB, ImuListKeyMagOffset, ImuListDataMagOffset )

        # Инициализировать поля класса хранящие параметры инициализации Акселерометра
        ImuListKeyGyrSet        = ('Gfs', 'Gsr', 'Glp')
        ImuListDataGyrSet       = [self.Gfs, self.Gsr, self.Glp]
        ReadValJSONfromDB( self.ConnectDB, ImuListKeyGyrSet, ImuListDataGyrSet )

        # Инициализировать поля класса хранящие параметры инициализации Гироскопа
        ImuListKeyAccSet        = ('Afs', 'Asr', 'Alp')
        ImuListDataAccSet       = [self.Afs, self.Asr, self.Alp]
        ReadValJSONfromDB( self.ConnectDB, ImuListKeyAccSet, ImuListDataAccSet )

        # Инициализировать поля класса хранящие параметры инициализации Магнитометра
        ImuListKeyMagSet        = ('Msr',)
        ImuListDataMagSet       = [self.Msr]
        ReadValJSONfromDB( self.ConnectDB, ImuListKeyMagSet, ImuListDataMagSet )

        # Инициализировать поле класса хранящее внутреннюю (IMU) частоту пакетного считывания трех сенсоров IMU
        ImuListKeyOdrSet        = ('Isr',)
        ImuListDataOdrSet       = [self.Isr]
        ReadValJSONfromDB( self.ConnectDB, ImuListKeyOdrSet, ImuListDataOdrSet )

        # Инициализировать поле класса хранящее значение коэффициента Альфа, новым, заданным в БД значением
        ImuListKeyAlpha         = ('AlphaIn',)
        ImuListDataAlpha        = [self.Alpha]
        ReadValJSONfromDB( self.ConnectDB, ImuListKeyAlpha, ImuListDataAlpha )

    '''
        Метод 'WriteDataDB' сохраняет все данные вырабатываемые в методах класса
        в БД Redis. Набор данных не детерминирован и определяется стадией реализации
        проекта 
    '''
    def WriteDataDB(self) -> None:

        # Сохранить массив сырых данных IMU в БД
        ImuListRawKey = ('AccArrRaw', 'GyroArrRaw', 'MagArrRaw', 'TemapArrRw')
        ImuListRawData = (self.AccArrRaw, self.GyrArrRaw, self.MagArrRaw, self.TempArrRaw)
        WriteValJSONtoDB( self.ConnectDB, ImuListRawKey, ImuListRawData )

        # Сохранить массив сырых усредненных данных IMU в БД
        ImuListAvgKey = ('AccArrAvg', 'GyroArrAvg', 'MagArrAvg')
        ImuListAvgData = (self.AccArrAvg, self.GyrArrAvg, self.MagArrAvg)
        WriteValJSONtoDB(self.ConnectDB, ImuListAvgKey, ImuListAvgData)

        # Сохранить массивы со значениями углов Эйлера в БД
        AngelListKey = ('AccArrAngle', 'GyroArrAngle', 'CompArrAngle')
        AngelListData = (self.AccArrAngle, self.GyrArrAngle, self.ComArrAngle)
        WriteValJSONtoDB( self.ConnectDB, AngelListKey, AngelListData ) 

        # Сохранить значение дельты времени обращений к IMU в БД
        TimeDeltaAngleKey = ('TimeDeltaAngle',)
        TimeDeltaAngleData = (self.TimeDeltaAngle,)
        WriteValJSONtoDB(self.ConnectDB, TimeDeltaAngleKey, TimeDeltaAngleData)

        # Сохранить текущее значение коэффициента Альфа, используемого при вычисления значений углов Эйлера в фильтре слияния
        AlphaKey = ('AlphaOut',)
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