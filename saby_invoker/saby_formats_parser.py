def __parse_default(dictionary: dict) -> dict:
    return dictionary


def __get_keys(dictionary: dict) -> list:
    """
    Get keys for Record and RecordSet

    :param dictionary: SABY Record or RecordSet format
    :type dictionary: dict
    :return: list of Record or RecordSet keys
    :rtype: list
    """

    return [x['n'] for x in dictionary['s']]


def __parse_recordset(recordset_dict: dict) -> list:
    """
    Parse SABY RecordSet to python list of dicts

    :param recordset_dict: SABY RecordSet format
    :type recordset_dict: dict
    :return: SABY RecordSet converted to list of dicts
    :rtype: list
    """

    keys = __get_keys(recordset_dict)
    return [__parse_record({'d': row}, keys) for row in recordset_dict['d']]


def __parse_record(record_dict: dict, keys: list=None) -> dict:
    """
    Parse SABY Record to python dictionary

    :param record_dict: SABY Record format
    :type record_dict: dict
    :param keys: list of RecordSet keys (for SABY RecordSet subparsing), defaults to None
    :param keys: list, optional
    :return: SABY Record converted to dict
    :rtype: dict
    """

    keys = keys if keys else __get_keys(record_dict)
    return {keys[ind]: record_dict['d'][ind] for ind in range(len(keys))}


def parse_result(result):
    """
    Parse SABY method result to python types

    :param result: SABY method result
    :return: SABY method result converted to python types
    """

    if type(result) is not dict:
        return result

    available_types = {
        'recordset': __parse_recordset,
        'record': __parse_record,
    }

    saby_type = result.get('_type', None)
    return available_types.get(saby_type, __parse_default)(result)