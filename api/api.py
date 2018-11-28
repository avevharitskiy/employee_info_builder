import urllib.parse as urlparse
from datetime import timedelta

from api import mine_user_info
from helpers import Configuration, Database
from saby_invoker import SabyFormatsBuilder, SabyInvoker


#   + Public methods
def get_user_info(user_id: int) -> dict:
    mined_users = [row["UserID"] for row in Database.query('SELECT * FROM "MinedUsers"')]

    if user_id not in mined_users:
        mine_user_info(user_id)

    result = {}
    user_responsibility = __calculate_user_responsibility(user_id)
    return result


def get_contacts(query_str, contragent="-2", record_limit=10, sid=None):
    """
        Возвращает список контактов по строке запроса.
        :param query_str: строка запроса
        :param contragent: идентификатор контрагента
        :param record_limit=10: ограничение на количество возвращаемых записей
        :param sid: идентификатор сессии
        :return: список сотрудников
    """
    rpc_result = SabyInvoker.invoke(
        "Staff.BrowserList",
        sid,
        Фильтр=SabyFormatsBuilder.build_record({
            "CalcWorkState": True,
            "ShowOtherEmployees": True,
            "newList": True,
            "showAsGroups": False,
            "usePages": "full",
            "ВернутьИдСервисаПрофилей": True,
            "Контрагент": contragent,
            "ПоощренияВзыскания": True,
            "ПутьКУзлу": True,
            "Разворот": "С разворотом",
            "СтатусАктивности": True,
            "СтрокаПоиска": query_str,
            "CurrentRoot": None
        }),
        Сортировка=None,
        Навигация=SabyFormatsBuilder.build_record({
            "ЕстьЕще": True,
            "РазмерСтраницы": 10,
            "Страница": 0
        }),
        ДопПоля=[]
    )
    contacts = __select_only_person(rpc_result['rec'], record_limit)

    return __formatting(contacts)


#   + Private methods
def __calculate_user_responsibility(user_id: int) -> int:
    # !Settings
    # max overwork hours per day (setting)
    MAX_OVERWORK = 2

    # get user plan percent
    user_plan_percent = Database.query_row(
        'SELECT "PlanPercent" from "UserPlanPercent" WHERE "UserID" = %s LIMIT 1',
        (user_id,)
        )

    # get user overwork
    user_overwork = Database.query_row(
        """
            SELECT sum("Overwork") AS "TotalOverwork", count("UserID") as "TotalDays"
            FROM "UserOverwork"
            WHERE "UserID" = %s
            group by "UserID"
        """,
        (user_id,)
    )

    # if can't find overwork and plan info return unknown value
    if not user_overwork and not user_plan_percent:
        return -1

    # if find only user plan info return plan percent
    elif user_plan_percent and not user_overwork:
        return int(user_plan_percent["PlanPercent"] / 10)

    # if find user overwork info
    elif user_overwork:
        # calculate overwork percents
        total_max_overwork = timedelta(hours=MAX_OVERWORK * user_overwork["TotalDays"])
        overwork_percents = (user_overwork['TotalOverwork'].total_seconds()/total_max_overwork.total_seconds()) * 100
        overwork_percents = 100 if overwork_percents > 100 else overwork_percents

        if user_plan_percent:
            return int((overwork_percents + user_plan_percent) / 20)

        return int(overwork_percents / 10)


def __select_only_person(records, record_limit):
    """
        Выбирает только персоны (сотрудники) из выборки сотрудников.
        Т.к. в выборке сотрудников могут быть еще и разделы.
        :param records: список записей сотрудников
        :param record_limit: ограничение на размер количества записей в результате
        :return: список сотрудников
    """
    result = []
    for record in records:
        if not record.get('Раздел@'):
            result.append(record)
            if len(result) >= record_limit:
                break
    return result


def __formatting(records):
    """
        Приводит записи к формату, необходимому для UI мобилки
        :param records: список записей с сотрудниками
        :return: список записей сотрудников с необходимыми полями
    """
    result = []
    for record in records:
        employee = {}
        # Получаем простые поля
        employee['postName'] = record.get('ПодразделениеНазвание')
        employee['secondName'] = record.get('Фамилия')
        employee['id'] = record.get('Лицо')
        employee['name'] = record.get('Имя')
        # Получаем информацию о фото
        photo_info = record.get('PhotoData')
        photo_url = photo_info.get('url', '')
        if photo_url:
            photo_url = urlparse.urljoin(Configuration.app_config['SABY']['site'], photo_url)
        employee['photoUrl'] = photo_url
        result.append(employee)
    return result
