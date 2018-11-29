"""
    Модуль Flask. Предназначен для работы с запросами.
    Предоставляет API проекта.
"""
import datetime
import json

from flask import request

from api import get_contacts, get_user_info
from server import flask_server


@flask_server.route('/', methods=['GET', 'POST'])
def about():
    """
        Возвращает информацию о сервере
        :return: информация о сервере
    """
    return "Flask server. Authors: ev.myshko, av.evharitskiy. Now: {now}".format(now=datetime.datetime.now())


@flask_server.route('/contacts', methods=['POST'])
def contacts():
    """
        Возвращает список контактов
        :return: список контактов
    """
    # Получаем данные запроса
    try:
        raw_data = request.data.decode()
        data = json.loads(raw_data)

        # Заполняем параметры
        ssid = data.get('sid')
        query_str = data.get('query_str')
        record_limit = data.get('limit', 10)
        if not query_str:
            return 'Отсутствует параметр: query_str', 500
        # Вызываем метод получения контактов
        contacts = get_contacts(query_str, record_limit=record_limit, sid=ssid)

        # Преобразуем в JSON
        contacts = json.dumps(contacts)
    except Exception as exc:
        return str(exc), 500
    return str(contacts)


@flask_server.route("/get_user_info", methods=['POST'])
def get_user_information():
    """
    Возвращает информацию по пользователю

    :return: Информация по пользователю
    :rtype: str
    """

    # get data
    try:
        raw_data = request.data.decode()
        data = json.loads(raw_data)

        # fill params
        ssid = data.get('sid')
        user_id = data.get('user_id')

        # invoke data mining
        user_info = get_user_info(user_id)

        # build JSON string
        user_info = json.dumps(user_info)

    except BaseException as exc:
        return str(exc), 500

    return str(user_info)
