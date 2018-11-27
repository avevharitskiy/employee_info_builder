import urllib.parse as urlparse

import requests
import simplejson

from helpers import Configuration
from saby_invoker.saby_formats_parser import parse_value


class RpcInvoker():
    """
    Класс вызова методов СБИС
    """
    @classmethod
    def initialize(cls, address: str = None, session_id: str = None):
        """
        Инициализирует RpcInvoker
        :param address: адрес сайта, на который будет отправлен запрос
        :type address: str
        :param session_id: идентификатор сессии, defaults to None
        :param session_id: str, optional
        """
        if not address:
            try:
                address = Configuration.app_config['SABY']['site']
            except KeyError:
                raise KeyError("В файле конфигурации не указан сайт СБИС!")

        cls.__address = urlparse.urljoin(address, "/service/sbis-rpc-service300.dll")

        if session_id is None:
            try:
                cls.__session = Configuration.app_config['SABY']['ssid']
            except KeyError:
                raise KeyError("В файле конфигурации не указан идентификатор сессии!")
        else:
            cls.__session = session_id

    @classmethod
    def invoke(cls, method_name: str, **params):
        """
        Вызывает метод бизнес логики с указанными параметрами
        :param method_name: имя метода
        :type method_name: str
        :return: результат выполнения метода
        """

        body = simplejson.dumps({
            "jsonrpc": "2.0",
            "protocol": 3,
            "method": method_name,
            "params": params,
            "id": 1
        })

        headers = {"Content-Type": "application/JSON; charset=utf-8", "X-SBISSessionID": cls.__session}

        response = requests.post(url=cls.__address, data=body, headers=headers)

        if not response.ok:
            return {'error': "{code}: {reason}".format(code=response.status_code, reason=response.reason)}

        response = simplejson.loads(response.text)

        if 'error' in response:
            error = response['error']
            return {'error': error['details'] if type(error) is dict else error}

        return parse_value(response['result'])
