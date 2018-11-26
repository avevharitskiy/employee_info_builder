"""
    Модуль Flask. Предназначен для работы с запросами.
    Предоставляет API проекта.
"""

from flask import Flask

import json
import bl_invoke

flask_server = Flask(__name__)

@flask_server.route('/', methods=['GET', 'POST'])
def about():
    """
        Возвращает информацию о сервере
        :return: информация о сервере
    """
    sid = '00000003-00066e3e-00ba-b977e62f351fda3b'
    pid = 'fcdb06d6-1b50-4aee-8336-b13d39e19e65'
    query_str = 'Демо'
    contragent = '-2'
    bl_invoke.get_contacts(sid, pid, query_str, contragent)
    return "This is Flask server."



if __name__ == '__main__':
    flask_server.run()
