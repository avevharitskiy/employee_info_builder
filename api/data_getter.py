from saby_invoker import SabyInvoker


def test():
    result = SabyInvoker.invoke("Местоположение.СводкаЗаДень", ЧастноеЛицо=16304156, Дата="2018-11-27", Опции={})
    print(result)