import requests
import urllib.parse as urlparse
try:
    import simplejson
except ImportError:
    raise RuntimeError("Не найдена библиотека simplejson! Пожалуйста установите ее.")

from saby_invoker.saby_formats_parser import parse_result


class RpcInvoker():
    """
    Класс вызова методов СБИС
    """
    def __init__(self, address: str, session_id: str=None):
        """
        Создает экземпляр класса RpcInvoker
        :param address: адрес сайта, на который будет отправлен запрос
        :type address: str
        :param session_id: идентификатор сессии, defaults to None
        :param session_id: str, optional
        """
        self.address = urlparse.urljoin(address, "/service/sbis-rpc-service300.dll")

        if session_id is None:
            with open('session', 'r') as session_file:
                self.session = session_file.read()
        else:
            self.session = session_id

    def invoke(self, method_name: str, **params):
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

        headers = {"Content-Type": "application/JSON; charset=utf-8", "X-SBISSessionID": self.session}

        response = requests.post(url=self.address, data=body, headers=headers)

        if not response.ok:
            return {'error': "{code}: {reason}".format(code=response.status_code, reason=response.reason)}

        response = simplejson.loads(response.text)

        if 'error' in response:
            error = response['error']
            return {'error': error['details'] if type(error) is dict else error}

        return parse_result(response['result'])
