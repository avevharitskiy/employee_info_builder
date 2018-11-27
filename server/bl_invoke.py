"""
    Модуль работы с внешними вызовами бизнес-логики online.sbis.ru
"""

import requests
import json
import sys

# Подключаем парсер
sys.path.append('../saby_invoker')
import saby_formats_parser


def get_contacts(sid, pid, query_str, contragent, record_limit=10):
    """
        Возвращает список контактов по строке строке запроса.
        :param sid: идентификатор сессии
        :param pid: идентификатор пользователя
        :param query_str: строка запроса
        :param contragent: идентификатор контрагента
        :param record_limit=10: ограничение на количество возвращаемых записей
        :return: список сотрудников
    """
    # Проверка параметров
    if not sid:
        raise Exception('Отсутствует параметр sid')
    if not pid:
        raise Exception('Отсутствует параметр pid')
    if not query_str:
        raise Exception('Отсутствует параметр query_str')
    if not contragent:
        raise Exception('Отсутствует параметр contragent')

    # Возвращаемый результат
    result = {}

    # Устанавливаем заголовки
    headers = {'Content-Type': 'application/JSON; charset=utf-8'}

    # Устанавливаем cookies
    cookies = {'sid': sid, 'CpsUserId': pid}

    # Устанавливаем тело запроса
    payload = {"jsonrpc": "2.0",
               "protocol": 5,
               "method": "Staff.BrowserList",
               "params": {"Фильтр": {"d": [True,
                                           True,
                                           True,
                                           False,
                                           "full",
                                           True,
                                           contragent,
                                           True,
                                           True,
                                           "С разворотом",
                                           True,
                                           query_str,
                                           None],
                                     "s": [{"n": "CalcWorkState", "t": "Логическое"},
                                           {"n": "ShowOtherEmployees", "t": "Логическое"},
                                           {"n": "newList", "t": "Логическое"},
                                           {"n": "showAsGroups", "t": "Логическое"},
                                           {"n": "usePages", "t": "Строка"},
                                           {"n": "ВернутьИдСервисаПрофилей", "t": "Логическое"},
                                           {"n": "Контрагент", "t": "Строка"},
                                           {"n": "ПоощренияВзыскания", "t": "Логическое"},
                                           {"n": "ПутьКУзлу", "t": "Логическое"},
                                           {"n": "Разворот", "t": "Строка"},
                                           {"n": "СтатусАктивности", "t": "Логическое"},
                                           {"n": "СтрокаПоиска", "t": "Строка"},
                                           {"n": "CurrentRoot", "t": "Строка"}],
                                     "_type": "record"},
                         "Сортировка": None,
                         "Навигация":{"d": [True, 10, 0],
                                      "s": [{"n": "ЕстьЕще", "t": "Логическое"},
                                            {"n": "РазмерСтраницы", "t": "Число целое"},
                                            {"n": "Страница", "t": "Число целое"}],
                                      "_type": "record"},
                         "ДопПоля": []},
               "id": 1}

    # Кодируем в JSON
    payload = json.dumps(payload)

    # Указываем адрес на который необходимо направлять запрос
    url = 'https://fix-online.sbis.ru/service/'

    # Отправляем запрос
    response = requests.post(url, data=payload, headers=headers, cookies=cookies)

    if response.status_code == 200:
        # Если мы получили успешный ответ - разбираем JSON тело ответа
        response = json.loads(response.text)
    else:
        raise Exception('Сервер вернул код ответа отличный от 200. Детали: {response}'.format(response=str(response)))

    # Парсим ответ БЛ (Получаем результат в виде нативных типов и структур)
    result = parse_result(response)

    return result[:record_limit]

def parse_result(body):
    """
        Возвращает распарсеный результат ответа БЛ
        :param body: тело ответа БЛ
        :return: распарсеный результат
    """
    result = []
    if body and (type(body) is dict):
        # Парсим результат
        if body.get('result'):
            result = saby_formats_parser.parse_result(body.get('result'))
        else:
            raise Exception('Отсутствует поле "result". Детали: {response}'.format(response=str(body)))
    return result
