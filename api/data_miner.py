import re
from datetime import date, datetime, timedelta
from functools import lru_cache

from dateutil.relativedelta import relativedelta
from dateutil.rrule import DAILY, FR, MO, TH, TU, WE, rrule
from scipy.cluster.vq import kmeans

from helpers import Database
from saby_invoker import SabyFormatsBuilder, SabyInvoker


def __get_user_day_location(user_id: int, day: str, sid: str) ->dict:
    return SabyInvoker.invoke(
            'Местоположение.СводкаЗаДень',
            sid,
            ЧастноеЛицо=user_id,
            Дата=day,
            Опции={
                "СогласованныеДокументы": True,
                "ТолькоОсновнаяАктивность": True,
                "UnproductiveTime": True
            }
    )


def __get_user_out_calls(user_id: int, day: str, sid: str) -> dict:
    rpc_result = SabyInvoker.invoke(
            "CallInfo.GetCountByFaceId",
            sid,
            person=str(user_id),
            ДатаС="{day}T00:00:00.000Z".format(day=day),
            ДатаПо="{day}T23:59:59.000Z".format(day=day)
        )
    result = {'count': 0.0, 'duration': timedelta()}

    if rpc_result:
        result['count'] = float(rpc_result.get("call_count_out", 0))
        result['duration'] = __convert_magic_string(rpc_result.get("call_time_out", "P0DT0H0M0S") or "P0DT0H0M0S")

    return result


def __calculate_overwork(need_datetime_str, fact_datetime_str):
    """
    Возвращает время переработки. В случае недоработки возаращает нулевую дельту
    :param need_datetime: необходимое время работы в формате: '%H:%M:%S'
    :param fact_datetime: фактическое время работы в формате: '%H:%M:%S'
    :return: timedelta переработки. В случае недоработки возвращает нулевую timedelta
    """
    need_datetime = None
    fact_datetime = None
    result = timedelta()

    # Получаем необходимое время рабоы
    if not need_datetime_str:
        need_datetime_str = '00:00:00'
    need_datetime = datetime.strptime(need_datetime_str, '%H:%M:%S')

    # получаем фактическое время работы
    if not fact_datetime_str:
        fact_datetime_str = '00:00:00'
    fact_datetime = datetime.strptime(fact_datetime_str, '%H:%M:%S')

    if fact_datetime > need_datetime:
        result = fact_datetime - need_datetime

    return result


def __convert_magic_string(magic_string: str) -> timedelta:
    """
    Преобразует магическую строку СБИС в понятную строку временного интервала

    :param magic_string: магическая строка полученная от СБИС
    :type magic_string: str
    :return: строка временного интервала
    :rtype: timedelta
    """
    time_regexp = re.compile(r"P(?P<days>[\d]+)DT(?P<hours>[\d]+)H(?P<minutes>[\d]+)M(?P<seconds>[\d\.]+)S")

    duration_regexp_dict = time_regexp.match(magic_string).groupdict()
    duration_dict = {key: int(float(val)) if val else 0 for key, val in duration_regexp_dict.items()}

    return timedelta(
                days=duration_dict['days'],
                hours=duration_dict['hours'],
                minutes=duration_dict['minutes'],
                seconds=duration_dict['seconds']
    )


@lru_cache()
def __get_date_range(start_date: date, months_count: int = 3) -> list:
    """
    Возвращает список дат, назад во времени от указанной даты

    :param start_date: дата с которой следует начать отсчет
    :type start_date: date
    :param months_count: кол-во месяцев которое нужно сгенерировать, defaults to 3
    :param months_count: int
    :return: список дат, назад во времени от указанной даты
    :rtype: list
    """
    end_date = start_date - relativedelta(months=months_count)
    return [str(day.date()) for day in rrule(DAILY, dtstart=end_date, until=start_date, byweekday=(MO, TU, WE, TH, FR))]


def __get_user_location_and_overwork(user_id: int, sid: str, datelist: list = None):
    """
    Получает данные местонахождения пользователя и сохраняет их в базу.

    :param user_id: идентификатор пользователя, по которому необходимо собрать статистику
    :type user_id: int
    :param datelist: список дат по которым необходимо собрать статистику, defaults to None
    :param datelist: list, optional
    """
    if not datelist:
        datelist = __get_date_range(date.today())

    for cur_date in datelist:

        rpc_result = __get_user_day_location(user_id, cur_date, sid)
        entrances = [entity for entity in rpc_result['activity_detail']['rec'] if entity['Описание'] == 'entrance']

        for entrance in entrances:
            Database.query(
                """
                INSERT INTO "UserLocation" ("UserID", "DateTime", "Status")
                VALUES (%s, %s, %s);
                """,
                (user_id, entrance["ВремяНачало"], entrance["Действие"])
            )

        # Смотрим всю активность
        activity_summary = rpc_result.get('activity_summary')

        # Выбираем необходимое время работы
        need_time_str = activity_summary.get('ВремяРаботыГрафик', '00:00:00')
        # Выбираем фактически сколько сотрудник отработал
        fact_time_str = activity_summary.get('ВремяРаботы', '00:00:00')

        Database.query(
            """
            INSERT INTO "UserOverwork" ("UserID", "Date", "Overwork")
            VALUES (%s, %s, %s);
            """,
            (
                user_id,
                cur_date,
                __calculate_overwork(need_time_str, fact_time_str)
            )
        )


def __get_user_activity(user_id: int, sid: str, datelist: list = None):
    """
    Получает данные активности пользователя и сохраняет их в базу.

    :param user_id: идентификатор пользователя, по которому необходимо собрать статистику
    :type user_id: int
    :param datelist: список дат по которым необходимо собрать статистику, defaults to None
    :param datelist: list, optional
    """

    insert_query = """
        INSERT INTO "UserActivity"("UserID", "Date", "Category", "Useful", "WastedTime")
        VALUES (%s, %s, %s, %s, %s);
    """
    if not datelist:
        datelist = __get_date_range(date.today())

    for cur_date in datelist:

        rpc_result = SabyInvoker.invoke(
            'Report.PersonProductivityStatistic',
            sid,
            Фильтр=SabyFormatsBuilder.build_record({"Date": cur_date, "Person": user_id}),
            Сортировка=None,
            Навигация=None,
            ДопПоля=[]
        )

        person_activities = [activity for activity in rpc_result['rec'] if activity['Parent@']] if rpc_result else []

        for activity in person_activities:
            # write user activity
            Database.query(
                insert_query,
                (user_id, cur_date, activity['Name'], activity['Useful'], __convert_magic_string(activity['Duration']))
            )

        # get user calls
        out_calls = __get_user_out_calls(user_id, cur_date, sid)

        Database.query(
            insert_query,
            (user_id, cur_date, "Звонки СБИС", 0, out_calls['duration'])
        )


def __get_user_plan_percent(user_id: int, sid: str, month_count: int = 3):
    """
    Получает данные по выполнению плана за указанный период и сохраняет их в базу.

    :param user_id: идентификатор пользователя, по которому необходимо собрать статистику
    :type user_id: int
    :param month_count: кол-во месяцев за которое надо собрать статистику, defaults to 3
    :type user_id: int, optional
    """
    today = date.today()
    start_date = date(year=today.year, month=today.month, day=1) - relativedelta(months=month_count)
    end_date = date(year=today.year, month=today.month, day=1) - relativedelta(days=1)

    rpc_result = SabyInvoker.invoke(
            'ПланРабот.ПунктыНаКарточкеСотрудника',
            sid,
            Фильтр=SabyFormatsBuilder.build_record({
                "ДатаНачала": str(start_date),
                "ДатаОкончания": str(end_date),
                "ФильтрПериод": "Период",
                "ЧастноеЛицо": user_id
            }),
            Сортировка=None,
            Навигация=None,
            ДопПоля=[]
        )
    percent_structure = rpc_result.get('outcome', None) if rpc_result else None

    if percent_structure:
        Database.query(
                """
                INSERT INTO "UserPlanPercent"("UserID", "PlanPercent")
                VALUES (%s, %s);
                """,
                (user_id, percent_structure['Процент'])
            )


def __get_user_overwork(user_id: int, days: list, sid: str) -> list:
    overwork = []

    for day in days:
        location_data = __get_user_day_location(user_id, day, sid)

        activity_summary = location_data.get('activity_summary')

        # Выбираем необходимое время работы
        need_time_str = activity_summary.get('ВремяРаботыГрафик', '00:00:00')
        # Выбираем фактически сколько сотрудник отработал
        fact_time_str = activity_summary.get('ВремяРаботы', '00:00:00')

        overwork.append(__calculate_overwork(need_time_str, fact_time_str).total_seconds())

    return kmeans(overwork, 1)[0][0]


def __get_user_calls(user_id: int, days: list, sid: str) -> list:
    call_count = []
    call_time = []

    for day in days:
        call_data = __get_user_out_calls(user_id, day, sid)

        call_count.append(call_data['count'])
        call_time.append(call_data['duration'].total_seconds())

    k_mean_count = kmeans(call_count, 1)[0][0]
    k_mean_time = kmeans(call_time, 1)[0][0]

    return k_mean_count, k_mean_time


def __get_user_neural_data(user_id: int, sid: str):
    # get data from last month
    last_days_range = __get_date_range(date.today(), 1)
    last_count, last_time = __get_user_calls(user_id, last_days_range, sid)
    last_overwork = __get_user_overwork(user_id, last_days_range, sid)
    # get data from first 2 months
    first_start_day = date.today() - relativedelta(months=1)
    first_days_range = __get_date_range(first_start_day, 2)
    first_count, first_time = __get_user_calls(user_id, first_days_range, sid)
    first_overwork = __get_user_overwork(user_id, first_days_range, sid)

    Database.query(
        """
        INSERT INTO "UsersNeuralData"(
            "UserID", "UserFirstCalls", "UserLastCalls", "UserFirstDuration", "UserLastDuration", "UserFirstOverwork", "UserLastOverwork"
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        """,
        (user_id, first_count, last_count, first_time, last_time, first_overwork, last_overwork)
    )


def mine_user_info(user_id: int, sid: str):
    dates = __get_date_range(date.today())
    # Get user location and overwork
    __get_user_location_and_overwork(user_id, sid, dates)

    # Get user activity
    __get_user_activity(user_id, sid, dates)

    # Get user plan percent
    __get_user_plan_percent(user_id, sid)

    # Prepare neural dataset
    __get_user_neural_data(user_id, sid)
    # Add user id in mined persons
    Database.query(
        """
            INSERT INTO "MinedUsers"("UserID", "TotalDays")
            VALUES (%s, %s);
        """,
        (user_id, len(dates))
    )

    # Apply database changes
    Database.commit_changes()
