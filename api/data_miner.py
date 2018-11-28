import re
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from dateutil.rrule import DAILY, rrule, MO, TU, WE, TH, FR
from functools import lru_cache

from helpers import Database
from saby_invoker import SabyFormatsBuilder, SabyInvoker


def __convert_magic_string(magic_string: str) -> str:
    """
    Преобразует магическую строку СБИС в понятную строку временного интервала

    :param magic_string: магическая строка полученная от СБИС
    :type magic_string: str
    :return: строка временного интервала
    :rtype: str
    """
    time_regexp = re.compile(r"P(?P<days>[\d]+)DT(?P<hours>[\d]+)H(?P<minutes>[\d]+)M(?P<seconds>[\d]+)S")

    duration_regexp_dict = time_regexp.match(magic_string).groupdict()
    duration_dict = {key: int(val) if val else 0 for key, val in duration_regexp_dict.items()}

    return timedelta(
                days=duration_dict['days'],
                hours=duration_dict['hours'],
                minutes=duration_dict['minutes'],
                seconds=duration_dict['seconds']
    )


@lru_cache()
def __get_date_range(start_date: date, day_count: int = 90) -> list:
    """
    Возвращает список дат, назад во времени от указанной даты

    :param start_date: дата с которой следует начать отсчет
    :type start_date: date
    :param day_count: кол-во дней которое нужно сгенерировать, defaults to 90
    :param day_count: int, optional
    :return: список дат, назад во времени от указанной даты
    :rtype: list
    """
    end_date = start_date - relativedelta(days=day_count)
    return [str(date) for date in rrule(DAILY, dtstart=end_date, until=start_date, byweekday=(MO, TU, WE, TH, FR))]


def __get_user_location_and_overwork(user_id: int):
    """
    Получает данные местонахождения пользователя и сохраняет их в базу.

    :param user_id: идентификатор пользователя, по которому необходимо собрать статистику
    :type user_id: int
    """
    datelist = __get_date_range(date.today())

    for cur_date in datelist:

        rpc_result = SabyInvoker.invoke(
            'Местоположение.СводкаЗаДень',
            ЧастноеЛицо=user_id,
            Дата=cur_date,
            Опции={
                "СогласованныеДокументы": True,
                "ТолькоОсновнаяАктивность": True,
                "UnproductiveTime": True
            }
        )

        entrances = [entity for entity in rpc_result['activity_detail']['rec'] if entity['Описание'] == 'entrance']

        for entrance in entrances:
            #   TODO: think about "come_in" and "get_away" values
            Database.query(
                """
                INSERT INTO "UserLocation" ("UserID", "DateTime", "Status")
                VALUES (%s, %s, %s);
                """,
                (user_id, entrance["ВремяНачало"], entrance["Действие"])
            )

        overwork = rpc_result['unproductive_time']

        Database.query(
            """
            INSERT INTO "UserOverwork" ("UserID", "Date", "Overwork")
            VALUES (%s, %s, %s);
            """,
            (
                user_id,
                cur_date,
                __convert_magic_string(overwork['UsefulTime']) if overwork and overwork['UsefulTime'] else timedelta()
            )
        )


def __get_user_activity(user_id: int):
    """
    Получает данные активности пользователя и сохраняет их в базу.

    :param user_id: идентификатор пользователя, по которому необходимо собрать статистику
    :type user_id: int
    """
    datelist = __get_date_range(date(2018, 8, 21))

    for cur_date in datelist:

        rpc_result = SabyInvoker.invoke(
            'Report.PersonProductivityStatistic',
            Фильтр=SabyFormatsBuilder.build_record({"Date": cur_date, "Person": user_id}),
            Сортировка=None,
            Навигация=None,
            ДопПоля=[]
        )

        person_activities = [activity for activity in rpc_result['rec'] if activity['Parent@']] if rpc_result else []

        for activity in person_activities:
            # write user activity
            Database.query(
                """
                INSERT INTO "UserActivity"("UserID", "Date", "Category", "WastedTime")
                VALUES (%s, %s, %s, %s);
                """,
                (user_id, cur_date, activity['Name'], __convert_magic_string(activity['Duration']))
            )


def __get_user_plan_percent(user_id, month_count: int = 3):
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


def mine_user_info(user_id: int):
    # Get user location and overwork
    __get_user_location_and_overwork(user_id)

    # Get user activity
    __get_user_activity(user_id)

    # Get user plan percent
    __get_user_plan_percent(user_id)

    # Add user id in mined persons
    Database.query(
        """
            INSERT INTO "MinedUsers"("UserID")
            VALUES (%s);
        """,
        (user_id,)
    )

    # Apply database changes
    Database.commit_changes()