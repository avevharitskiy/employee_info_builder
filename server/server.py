"""
    Модуль Flask. Предназначен для работы с запросами.
    Предоставляет API проекта.
"""

from flask import Flask
from flask import request

import datetime
import json
import bl_invoke

flask_server = Flask(__name__)

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
        sid = data.get('sid')
        pid = data.get('pid')
        query_str = data.get('query_str')
        contragent = data.get('contragent')
        record_limit = data.get('limit', 10)

        # Вызываем метод получения контактов
        contacts = bl_invoke.get_contacts(sid, pid, query_str, contragent, record_limit)

        # Преобразуем в JSON
        contacts = json.dumps(contacts)
    except Exception as exc:
        return str(exc), 500
    return str(contacts)


if __name__ == '__main__':
    flask_server.run()
