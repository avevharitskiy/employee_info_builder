from server import flask_server
from saby_invoker import SabyInvoker

invoker = SabyInvoker('https://test-online.sbis.ru/', '00000003-005dd73f-00ba-973811eb606adf7b')

result = invoker.invoke(
    'PrintingTemplateFolder.GetDefaultFolder',
    Endpoint='СчетИсх',
    Source=None
)
print(result)
