"""
    Модуль Flask. Предназначен для работы с запросами.
    Предоставляет API проекта.
"""

try:
    from flask import Flask
except ImportError:
    print("Can't import flask")

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
