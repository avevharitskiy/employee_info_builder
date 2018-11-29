import urllib.parse as urlparse
from datetime import timedelta
from scipy.cluster.vq import kmeans

from api import mine_user_info
from helpers import Configuration, Database
from saby_invoker import SabyFormatsBuilder, SabyInvoker


#   + Public methods
def get_user_info(user_id: int, sid: str = None) -> dict:
    mined_users = [row["UserID"] for row in Database.query('SELECT * FROM "MinedUsers"')]

    if user_id not in mined_users:
        mine_user_info(user_id, sid)

    # get user days count in dataset (except weekends)
    total_days = Database.query_row(
        'select "TotalDays" from  "MinedUsers" where "UserID" = %s',
        (user_id,)
    )['TotalDays']

    result = {}

    result['user_responsibility'] = __calculate_user_responsibility(user_id)
    result['user_sociability'] = __calculate_user_sociability(user_id, total_days)
    result['user_procrastination'] = __calculate_user_procrastination(user_id, total_days)
    result['user_often_leaving'] = __calculate_user_leaving(user_id)
    result['user_punctuality'] = __calculate_user_punctuality(user_id)

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
def __calculate_user_punctuality(user_id: int) -> int:
    # !Settings
    # max deviation minutes per day (setting)
    MAX_DEVIATION = 30

    user_incoming = Database.query(
        """
        With "Dates" as (
            select "DateTime"::date as "Date"
            from "UserLocation"
            Where "UserID" = %s and "Status" = 1
            group by "Date"
        )
        select dates."Date", min(main."DateTime"::time) as "ComingTime"
        from "UserLocation" as main
        inner join "Dates" as dates
            on dates."Date" = main."DateTime"::date
        group by dates."Date"
        order by dates."Date"
        """,
        (user_id,)
    )
    if user_incoming:
        # get user incoming times as seconds
        timelist = [row['ComingTime'] for row in user_incoming]
        timelist = [timedelta(hours=x.hour, minutes=x.minute, seconds=x.second).total_seconds() for x in timelist]

        # convert max deviation to seconds
        time_max_deviation = timedelta(minutes=MAX_DEVIATION).total_seconds()

        # calculate average tive with deviation
        k_mean = kmeans(timelist, 1)[0][0]
        max_time = k_mean + time_max_deviation
        min_time = k_mean - time_max_deviation

        # find punctual points
        punctual = [time for time in timelist if time > min_time and time < max_time]
        return int(len(punctual) / len(timelist) * 10)

    return -1

def __calculate_user_leaving(user_id: int) -> bool:
    '''
    Расчитывает флаг часто ли пользователь уходит из офиса

    :param user_id: идентификатор пользователя
    :type user_id: int
    :return: флаг частого покидания офиса
    :rtype: bool
    '''

    # !Settings
    # max user leavings per day (setting)
    MAX_LEAVING = 3

    user_leavings = Database.query_row(
        """
        select avg("LeavingCount") as "AvgLeavings"
        from (
            select "DateTime"::date as "Date" , count("Status") as "LeavingCount"
            from "UserLocation"
            where "UserID" = %s and "Status" = 0
            group by "Date"
        ) as "LeavingPerDay"
        """,
        (user_id,)
    )
    if user_leavings:
        return True if int(user_leavings["AvgLeavings"]) > MAX_LEAVING else False
    else:
        return None


def __calculate_user_procrastination(user_id: int, total_days: int) -> int:
    '''
    Расчитывает показатель прокрастенации пользователя

    :param user_id: идентификатор пользователя
    :type user_id: int
    :param total_days: кол-во дней по которым собрана статистика на пользователя
    :type total_days: int
    :return: [показатель прокрастенации пользователя
    :rtype: int
    '''

    # !Settings
    # max user procrastination minutes per day (setting)
    MAX_PROCRASTINATION = 45

    user_procrastination = Database.query_row(
        """
        select sum("WastedTime") as "WastedTime" from "UserActivity"
        where "UserID" = %s and "Useful" = -1
        """,
        (user_id,)
    )['WastedTime']
    if user_procrastination:
        total_procrastenation = timedelta(minutes=MAX_PROCRASTINATION * total_days)
        result = int(user_procrastination.total_seconds() / total_procrastenation.total_seconds() * 10)

        return 10 if result > 10 else result

    else:
        return 0


def __calculate_user_sociability(user_id: int, total_days: int) -> int:
    """
    Расчитывает показатель комуникабельности человека

    :param user_id: идентификатор пользователя
    :type user_id: int
    :param total_days: кол-во дней по которым собрана статистика на пользователя
    :type total_days: int
    :return: аоказатель коммуникабельности
    :rtype: int
    """

    # !Settings
    # max user not work communication minutes per day (setting)
    MAX_COMMUNICATION = 15

    user_communication = Database.query_row(
        """
        select sum("WastedTime") as "WastedTime"
        from  "UserActivity"
        where "UserID" = %s and "Category" like 'Обмен сообщениями %%'
        """,
        (user_id,)
    )

    if user_communication:
        max_user_communication = timedelta(minutes=MAX_COMMUNICATION * total_days)
        result = int(user_communication['WastedTime'].total_seconds() / max_user_communication.total_seconds() * 10)
        return 10 if result > 10 else result
    else:
        return -1


def __calculate_user_responsibility(user_id: int) -> int:
    '''
    Расчитывает показатель ответственности человека

    :param user_id: идентификатор пользователя
    :type user_id: int
    :return: показатель ответственности человека
    :rtype: int
    '''

    # !Settings
    # max overwork hours per day (setting)
    MAX_OVERWORK = 2

    # get user plan percent
    user_plan_percent = Database.query_row(
        'SELECT "PlanPercent" from "UserPlanPercent" WHERE "UserID" = %s LIMIT 1',
        (user_id,)
        )

    if user_plan_percent:
        user_plan_percent = user_plan_percent["PlanPercent"]

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
        return int(user_plan_percent / 10)

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
