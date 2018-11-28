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
    def initialize(cls, address: str = None):
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

    @classmethod
    def invoke(cls, method_name: str, session_id: str = None, **params):
        """
        Вызывает метод бизнес логики с указанными параметрами
        :param method_name: имя метода
        :type method_name: str
        :param session_id: идентификатор сессии пользователя
        :type session_id: str
        :param person_id: идентификатор сессии пользователя
        :type person_id: str
        :return: результат выполнения метода
        """

        if session_id is None:
            try:
                session_id = Configuration.app_config['SABY']['session_id']
            except KeyError:
                raise KeyError("В файле конфигурации не указан идентификатор сессии!")

        body = simplejson.dumps({
            "jsonrpc": "2.0",
            "protocol": 5,
            "method": method_name,
            "params": params,
            "id": 1
        })

        headers = {"Content-Type": "application/JSON; charset=utf-8", "X-SBISSessionID": session_id}

        response = requests.post(url=cls.__address, data=body, headers=headers)
        response_dict = simplejson.loads(response.text)

        if not response.ok:
            result = {'error': "{code}: {reason}".format(code=response.status_code, reason=response.reason)}

            if 'error' in response_dict:
                error = response_dict['error']
                result['details'] = error['details'] if type(error) is dict else error

            return result

        return parse_value(response_dict['result'])
