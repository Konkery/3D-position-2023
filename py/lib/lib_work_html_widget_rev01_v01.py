# Подключить библиотеки для работы с виджетами в Jupyter Lab
import ipywidgets as widgets
from   ipywidgets import Output
from IPython.display import display


'''
    Функция 'CreateHTMLwidgest' выполняет создание HTML полей для отображение значений
    сырых данных от Акселерометра, Гироскопа, Магнетометра и др источников.
    Функция специфична - она создает сразу три поля под X, Y, Z значения и два разделителя.
    
'''
def CreateHTMLwidgest() -> object:
    
    # Создать три виджета и два разделителя для отображения значений
    x       = widgets.HTML(value=f'<div style="text-align: right; width: 100px; border: 3px solid #000"><span style="padding-right: 3px">{0.0:.1f}</span></div>')
    y       = widgets.HTML(value=f'<div style="text-align: right; width: 100px; border: 3px solid #000"><span style="padding-right: 3px">{0.0:.1f}</span></div>')
    z       = widgets.HTML(value=f'<div style="text-align: right; width: 100px; border: 3px solid #000"><span style="padding-right: 3px">{0.0:.1f}</span></div>')
    sep1    = widgets.HTML(value='', layout=widgets.Layout(width='50px'))
    sep2    = widgets.HTML(value='', layout=widgets.Layout(width='50px'))

    return x, y, z, sep1, sep2

'''
    Функция 'UpdateHTMLwidgest' выполняет обновление содержимого трех HTML виджетов.
    Функция принимает ссылки на виджеты и массив с тремя массивами, отбирает крайние
    элементы внутренних массивов и вставляет их в HTML поля виджета.

'''
def UpdateHTMLwidgest( _x, _y, _z, _arrVal ) -> None:
    
    _x.value = f'<div style="text-align: right; width: 100px; border: 3px solid #000"><span style="padding-right: 3px">{_arrVal[0][-1]:.4f}</span></div>'
    _y.value = f'<div style="text-align: right; width: 100px; border: 3px solid #000"><span style="padding-right: 3px">{_arrVal[1][-1]:.4f}</span></div>'
    _z.value = f'<div style="text-align: right; width: 100px; border: 3px solid #000"><span style="padding-right: 3px">{_arrVal[2][-1]:.4f}</span></div>'