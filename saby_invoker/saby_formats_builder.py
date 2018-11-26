"""
Модуль приведения python типов к типам данных СБИС.
По умолчанию приводит все словари к вложенным  Record`ам.
Если неоходимо передать внутри Record`a JSON неоходимо передать его в виде:
{
    "_type": "JSON"
    "_value": {/*словарь который необходимо передать в виде json объекта*/}
}
"""
import base64
from collections import namedtuple
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

saby_type_meta = namedtuple("saby_meta", 'type, converter')

byte_saby_meta = saby_type_meta("Двоичное", lambda val: base64.b64encode(val).decode())


def __check_broken_format(value):
    recordset_format = set(value[0])
    for ind in range(1, len(value)):
        if recordset_format ^ set(value[ind]):
            return True
    return False


def build_recordset(value):
    if not all(isinstance(val, dict) for val in value):
        raise TypeError("Все значения в списке должны быть словарями!")

    elif __check_broken_format(value):
        raise TypeError("Формат записей внутри списка должен быть одинаков!")
    recordset_dict = {'_type': 'recordset'}
    records_list = [build_record(row) for row in value]

    recordset_dict['s'] = records_list[0].get("s")
    recordset_dict['d'] = [record.get('d') for record in records_list]

    return recordset_dict


def build_record(dictionary: dict,) -> dict:
    if type(dictionary) is not dict:
        raise TypeError("Значение аргумента не является словарем!")

    record_dict = {'_type': 'record', 's': [], 'd': []}

    for key, value in dictionary:
        saby_converter = None

        if type(value) not in SABY_TYPES + [list, dict]:
            raise TypeError("Неверный тип значения в записи!")

        # check simple types
        if type(value) in SABY_TYPES:
            saby_converter = SABY_TYPES[type(value)]
        # check JSON or Record type
        elif type(value) is dict:
            is_json = str(value.get('_type', None)).lower() == 'json'
            value = value.get('_value', None)
            saby_converter = SABY_TYPES['json'] if is_json else SABY_TYPES['record']

        # check Array or RecordSet type
        elif type(value) is list:
            list_type = type(value[0])

            if not all(isinstance(val, list_type) for val in value):
                raise TypeError("Значения в списке имеют разлиный тип!")

            saby_converter = SABY_TYPES['recordset'] if list_type is dict else SABY_TYPES['array']

            if list_type is not dict:
                saby_converter.type['t'] = SABY_TYPES[list_type].type

        record_dict['s'].append({'n': key, 't': saby_converter.type})
        record_dict['d'].append(saby_converter.converter(value))

    return record_dict


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
    'json': saby_type_meta('JSON-объект', lambda val: val),
    'record': saby_type_meta("Запись", lambda val: build_record(val)),
    'recordset': saby_type_meta("Выборка", lambda val: build_recordset(val)),
    'array': saby_type_meta({"n": "Массив"}, lambda val: val)
}
