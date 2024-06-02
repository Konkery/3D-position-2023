import redis
import json

'''
    Функция 'ConnectDB' выполняет подключение к БД Redis и возвращает активное соединение.
'''
def ConnectDB() -> object:

    # Выполнить подключение к базе данных Redis
    connect_db = redis.Redis( host='localhost', port=6379, db=0 )
    
    return connect_db

'''
    Функция 'WriteValJSONtoDB' записывает N значений JSON в БД Redis, производит сериализацию
    и выполняет запись в БД Redis.
    Аргументы:
    '_connectDB'     - ссылка на объект типа connect DB Redis;
    '_inputListKey'  - кортеж содержащий имена (string) N ключей БД Redis;
    '_inputListData' - кортеж содержащий значения (string) N ключей БД Redis.
'''
def WriteValJSONtoDB( _connectDB, _inputListKey, _inputListData ) -> None:
    
    for key, data in zip(_inputListKey, _inputListData):
        value_json = json.dumps(data)  # Сериализация списка целых чисел в JSON строку
        _connectDB.set(key, value_json)  # Запись сериализованных данных в Redis по соответствующему 

'''
    Функция 'ReadValJSONfromDB' читает N значений JSON из БД Redis, производит десериализацию
    и возвращает результирующих значений.
    Аргументы:
    '_connectDB'      - ссылка на объект типа connect DB Redis;
    '_inputListKey'   - кортеж содержащий имена (string) N ключей БД Redis;
    '_outputListData' - кортеж содержащий переменные в которые записываются считанные из БД значения
'''
def ReadValJSONfromDB( _connectDB, _inputListKey, _outputListData ) -> None:

    # Считать и десериализовать JSON значения ключей из Redis
    for i, key in enumerate(_inputListKey):
        data_json = _connectDB.get(key)  # Прочитать JSON значение из Redis по ключу        
        # Если ключ содержит значение - присвоить его, в противном случае - None
        _outputListData[i] = json.loads(data_json) if data_json is not None else None