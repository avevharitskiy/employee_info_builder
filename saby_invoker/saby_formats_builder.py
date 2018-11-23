"""
Модуль приведения python типов к типам данных СБИС.
По умолчанию приводит все словари к вложенным  Record`ам.
Если неоходимо передать внутри Record`a JSON неоходимо передать его в виде:
{
    "_type": "JSON"
    "value": {/*словарь который необходимо передать в виде json объекта*/}
}
"""
import base64
from collections import namedtuple
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

saby_type_meta = namedtuple("saby_meta", 'type, converter')

byte_saby_meta = saby_type_meta("Двоичное", lambda val: base64.b64encode(val).decode())
SABY_TYPES = {
    date: saby_type_meta("Дата", lambda val: str(val)),
    datetime: saby_type_meta("Дата и время", lambda val: str(val)),
    float: saby_type_meta("Число вещественное", lambda val: val),
    int: saby_type_meta("Число целое", lambda val: val),
    Decimal: saby_type_meta("Деньги", lambda val: val),
    str: saby_type_meta("Строка", lambda val: val),
    UUID: saby_type_meta("UUID", lambda val: str(val)),
    bytearray: byte_saby_meta,
    bytes: byte_saby_meta,
    bool: saby_type_meta("Логическое", lambda val: val),
}

SPECIAL_TYPES = [list, dict]


def build_record(dictionary: dict,) -> dict:
    if type(dictionary) is not dict:
        raise TypeError("Значение аргумента не является словарем!")

    record_dict = {'_type': 'record', 's': [], 'd': []}

    for key, value in dictionary:
        # check unsupported types
        if type(value) not in list(SABY_TYPES) + SPECIAL_TYPES:
            raise TypeError("Значение словаря имеет не поддерживаемый тип!")
        
        # check simple types
        elif type(value) in SABY_TYPES:
            saby_converter = SABY_TYPES[type(value)]
            record_dict['d'].append(saby_converter.converter(value))
            record_dict['s'].append({'n': key, 's': saby_converter.type})
        
        # check complicated types
        elif type(value) in SPECIAL_TYPES:
            
