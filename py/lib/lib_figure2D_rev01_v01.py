# Подключить библиотеки для мат обработки данных и генерации случайных данных
import numpy as np
import random
import math
# Подключить библиотеки для работы с 2D графиками
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FormatStrFormatter, AutoMinorLocator, NullFormatter



'''
    Класс создания 'тройной' 2D фигуры  Matplotlib.
'''
class Figure2D:
    # Аргументы конструктора:
    # _opts  - словарь содержащий следующие значения:
    #               -> figsize    - размер фигуры в дюймах, кортеж из двух значений типа *int*
    #               -> nrows      - количество осей (графиков) по вертикали, значение типа *int*
    #               -> suptitle   - подпись ко всей группе графиков в целом (к фигуре), тип *string*
    #               -> abscissa   - подпись к оси абсцисс (ось X), такая подпись одна (!), относится к фигуре в целом, тип *string*
    #               -> ordinate   - подпись к осям ординат (оси Y), кортеж типа *string*
    #               -> facecolor  - цет заливки фона графика, кортеж типа *string*
    #               -> alpha      - прозрачность цвета заливки графика, кортеж типа *int*
    #               -> graphcolor - цвет кривой графика, кортеж типа *string*
    #               -> xlim       - диапазон значений оси X Xmim, Xmax, кортеж из двух значений типа *int*
    #               -> ylim       - диапазон значений оси Y Ymim, Ymax, кортеж из двух значений типа *int*
    
    def __init__( self, _opts ):

        self.FigureOpt  = _opts            # поле хранит набор характеристик фигуры которую необходимо сгенерировать
        
        self.ValueLim   = _opts['xlim'][1] # количество значений сенсора хранящихся в массиве
        self.IterNumber = 0                # поле хранит номер измерения, которое может быть целым числом в диапазоне 0...360

        # заполнить '0' значениями массив данных сенсоров
        #self.Gyro  = [ [0] * self.ValueLim, [0] * self.ValueLim, [0] * self.ValueLim ]
        self.Data   = [ [0] * self.ValueLim, [0] * self.ValueLim, [0] * self.ValueLim ]
        #self.Mag   = [ [0] * self.ValueLim, [0] * self.ValueLim, [0] * self.ValueLim]

        self.X      = np.arange( self.ValueLim )     # набор целых чисел, являющиеся отсчетами оси Х
        
        self.Figure = None                    # хранит сгенерированную 'figure'
        self.Ax     = None                    # хранит сгенерированную 'axes'
        self.Lines  = []                      # хранит собственно 'кривые' графиков
    '''
        Метод CreateVectorFigure на основе значения аргументов словаря 'FigureOpt', в соответствии ними возвращает фигуру с созданными
        и настроенными графиками. Особенность функции - она специфичным способом компонует графики:
                      ВСЕ ГРАФИКИ БУДУТ ВЫСТРОЕНЫ В ОДИН ВЕРТИКАЛЬНЫЙ СТОЛБЕЦ, ПО ОДНОМУ ГРАФИКУ В СТРОКЕ
       
        Возвращаемое значение:
            figure    - созданная функцией фигура
            ax        - созданные "оси" (суб-графики) в данной фигуре
    '''
    def CreateVectorFigure( self ):
        self.Figure = plt.figure( figsize = self.FigureOpt['figsize'] ) # создать фигуру
        self.Ax = self.Figure.subplots( self.FigureOpt['nrows'], 1 )    # создать заданное количество осей Axes (графиков)
        
        # Сохранить 'кривые' графиков в массив
        for i in range(self.FigureOpt['nrows']):
            line, = self.Ax[i].plot(self.X, self.Data[i])  
            self.Lines.append(line)
    
        self.StartPropertyAxes() # задать характеристики отображения регионов построения графиков и собственно графиков
    
    '''
        Метод StartPropertyAxes принимает ряд аргументов и в соответствии с ними задает 
        ряд свойств области графика (не figure!) на этапе создания 'figure'. Данная функция
        предназначена только для задания стартовых свойств Axes ! Для задания свойств во время 
        модификации необходимо использовать другой метод.
        Аргументы:
        _opts     - словарь содержащий следующие значения:
                   -> figure     - фигура (API matplotlib)
                   -> ax         - оси Axes переданной фигуры (API matplotlib)
                   -> suptitle   - подпись ко всей группе графиков в целом (к фигуре), тип *string*
                   -> abscissa   - подпись к оси абсцисс (ось X), такая подпись одна (!), относится к фигуре в целом, тип *string*
                   -> ordinate   - подпись к осям ординат (оси Y), кортеж типа *string*
                   -> facecolor  - цет заливки фона графика, кортеж типа *string*
                   -> alpha      - прозрачность цвета заливки графика, кортеж типа *int*
                   -> graphcolor - цвет кривой графика, кортеж типа *string*
                   -> xlim       - диапазон значений оси X Xmim, Xmax, кортеж из двух значений типа *int*
                   -> ylim       - диапазон значений оси Y Ymim, Ymax, кортеж из двух значений типа *int*
    '''

    def StartPropertyAxes( self ):
        
        self.Figure.suptitle( self.FigureOpt['suptitle'] ) # задать подпись к фигуре в целом
        _ax = self.Ax # создать временную локальную переменную
    
        # задать свойства осей и полигонов всех графиков
        for i in np.arange( self.FigureOpt['nrows'] ):
            _ax[i].set_ylabel( self.FigureOpt['ordinate'][i] , fontweight='bold' ) # задать жирное начертание для подписи к Y осям
            _ax[i].yaxis.get_label().set_rotation(0)                               # задать вращение подписей Y осей
        
            # задать подпись к единственной, последней оси абсцисс (ось Х), она одна для всех графиков
            _ax[i].set_xlabel( self.FigureOpt['abscissa'], fontweight='bold' ) if i == self.FigureOpt['nrows']-1 else None  
        
            # задать характеристики графика
            rect = _ax[i].patch                                  # добавить объект-фигуру в 'rect'
            rect.set_facecolor( self.FigureOpt['facecolor'][i] ) # задать цвет заливки фона графика
            rect.set_alpha( self.FigureOpt['alpha'][i] )         # задать прозрачность заливки фона графика    
        
            # Задание минимального и максимального значения для оси X
            _ax[i].set_xlim( self.FigureOpt['xlim'][0], self.FigureOpt['xlim'][1] )
            
            # Задание минимального и максимального значения для оси Y
            if isinstance(self.FigureOpt['ylim'], str) and self.FigureOpt['ylim'] == 'auto':
                _ax[i].set_ylim()
            else:
                _ax[i].set_ylim( self.FigureOpt['ylim'][0], self.FigureOpt['ylim'][1] )

    '''
    Метод UpdatePropertyAxes обновляет  ряд свойств области графика (не фигуры!).
    Данная функция предназначена для вызова при обновлении данных графика.
    '''
    
    def UpdatePropertyAxes( self ):

        self.Figure.suptitle( self.FigureOpt['suptitle'] ) # задать подпись к фигуре в целом
        _ax = self.Ax                                      # создать временную локальную переменную
    
        # задать свойства осей и полигонов всех графиков
        for i in np.arange( self.FigureOpt['nrows'] ):
            max_y = max(self.Data[i]) + math.ceil(max(self.Data[i])/10 ) # определить макс. значения по оси Y + 10%
            min_y = min(self.Data[i]) + math.floor(min(self.Data[i])/10 ) # определить мин. значения по оси Y + 10%

            _ax[i].set_ylim( min_y, max_y )         # задать минимальное и максимальное значения для оси Y
            self.Lines[i].set_ydata(self.Data[i])    # обновить значения оси Y
            _ax[i].lines[0].set_color( self.FigureOpt['graphcolor'][i] ) # задать цвет кривой графика
                
            _ax[i].grid(True) # задать сетку
            
    #
    #
    #

    def UpdateDataIMU(self):
        data     = math.sin(math.radians( (self.IterNumber*360)/self.ValueLim )) # получить текущее значение sin(x)
        
        data_acc_x   = data + random.uniform(0, data*0.1) # подмешать 10% шумов
        data_acc_y   = data + random.uniform(0, data*0.1) # подмешать 10% шумов
        data_acc_z   = data + random.uniform(0, data*0.1) # подмешать 10% шумов

        self.Data[0].append(data_acc_x)
        self.Data[1].append(data_acc_y)
        self.Data[2].append(data_acc_z)

        data_gyr_x = (data + random.uniform(0, data*0.1))*100  # масштабировать к 100 deg/s и подмешать 10% шумов
        data_gyr_y = (data + random.uniform(0, data*0.1))*100  # масштабировать к 100 deg/s и подмешать 10% шумов
        data_gyr_z = (data + random.uniform(0, data*0.1))*100  # масштабировать к 100 deg/s и подмешать 10% шумов

        self.Gyro[0].append(data_gyr_x)
        self.Gyro[1].append(data_gyr_y)
        self.Gyro[2].append(data_gyr_z)

        if len(self.Data[0]) > self.ValueLim:
            self.Data[0].pop(0)
            self.Data[1].pop(0)
            self.Data[2].pop(0)

            self.Gyro[0].pop(0)
            self.Gyro[1].pop(0)
            self.Gyro[2].pop(0)
        
        self.IterNumber += 1
        self.IterNumber = 1 if self.IterNumber > 360 else self.IterNumber # обнулить счетчик итераций если он стал > 360
    #
    #
    #
    def UpdateAnimation( self, frame ):
        self.UpdateDataIMU()
        self.UpdatePropertyAxes()