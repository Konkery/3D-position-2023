# Блок импорта системных библиотек python
import asyncio
import functools
from typing import Any, Callable
import time

'''
Класс SetInterval реализует асинхронную модель работы метода 'run' аналогично
функции setInterval в JavaScript
'''
class SetInterval:
    def __init__(self, _interval, _fn, *args):
        
        self.interval            = _interval # интервал вызова пользовательской функции 'fn'       
        self.fn                  = functools.partial(_fn, *args) # пользовательский метод который будет асинхронно вызываться с заданным периодом
        self.is_running          = False # идет выполнение асинхронного кода
        self.task                = None
        self.last_execution_time = None # вспомогательное поле для определения истинного времени между вызовами, отладочный код 

    '''
    Метод 'run' является основным в реализации идеологии SetInterval, в нем происходит запуск 
    пользовательской функции 'fn'
    '''
    async def run(self):
        self.is_running = True
        while self.is_running:
            #self.calculate_elapsed_time()
            self.fn()
            await asyncio.sleep(self.interval)
    '''
    Метод 'calculate_elapsed_time' вспомогательный отладочный метод, предназначенный для 
    вычисления времени между двумя вызовами основного метода 'run' в котором происходит
    запуск пользовательского метода 'fn'.
    Данный метод после отладки кода можно отключить, т.к. он только добавляет небольшую
    трату вычислительных ресурсов.
    '''
    def calculate_elapsed_time(self):
        current_time = time.time()
        if self.last_execution_time is not None:
            elapsed_time = current_time - self.last_execution_time
            temp_delta = int(elapsed_time * 100000) / 100
            print(f"Delta time Python: {temp_delta} ms")
            
        self.last_execution_time = current_time
    
    '''
    Метод 'start' относится к сервисным, он непосредственно создает 'task' в терминологии
    библиотеки 'asyncio' Python в который на запуск передается метод 'run', который фактически
    вызывает запуск пользовательской функции 'fn'
    '''
    def start(self):
        self.task = asyncio.create_task(self.run())
    
    '''
    Метод 'stop' прекращает работу всей механики данного класса, фактически данный метод 
    аналогичен методу 'clearInterval' в JavaScript для 'setInterval'
    '''
    def stop(self):
        self.is_running = False