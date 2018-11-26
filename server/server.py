"""
    Модуль Flask. Предназначен для работы с запросами.
    Предоставляет API проекта.
"""

from flask import Flask

import json

flask_server = Flask(__name__)

@flask_server.route('/', methods=['GET', 'POST'])
def about():
    """
        Возвращает информацию о сервере
        :return: информация о сервере
    """
    return "This is Flask server."

if __name__ == '__main__':
    flask_server.run()
