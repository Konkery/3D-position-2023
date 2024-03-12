import asyncio
import time

'''
Класс SetInterval реализует асинхронную модель работы метода 'run' аналогично
функции setInterval в JavaScript
'''
class setInterval:
    def __init__(self, interval, fn):
        self.interval = interval        # интервал вызова пользовательской функции 'fn'
        self.fn = fn                    # пользовательский метод который будет асинхронно вызываться с заданным периодом
        self.is_running = False         # идет выполнение 'run'
        self.task = None
        self.last_execution_time = None # вспомогательное поле для определения истинного времени между вызовами, отладочный код 

    '''
    Метод 'run' является основным в реализации идеологии SetInterval, в нем происходит запуск 
    пользовательской функции 'fn'
    '''
    async def run(self):
        self.is_running = True
        while self.is_running:
            self.calculate_elapsed_time()
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


if __name__ == "__main__":
    async def Main():
        # Пример использования
        def FuncUser_1():
            print("Hello world!---1")
        def FuncUser_2():
            print("Hello world!---2")
        def FuncUser_3():
            print("Hello world!---3")

        interval_1 = SetInterval(0.05, FuncUser_1)
        interval_2 = SetInterval(0.05, FuncUser_2)
        interval_3 = SetInterval(0.05, FuncUser_3)
    
        interval_1.start()
        interval_2.start()
        interval_3.start()

        # Ждем XXX секунд, затем останавливаем выполнение
        await asyncio.sleep( 3 )

        interval_1.stop()
        interval_2.stop()
        interval_3.stop()
    
    asyncio.run( Main() )