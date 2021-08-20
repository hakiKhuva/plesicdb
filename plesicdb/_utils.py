import datetime

def date(object,use_date=False):
    """
        Function to convert datetime.date and datetime.datetime object to dict so it can store in JSON format.

        Args:
            object : datetime.date or datetime.datetime or dict object
            use_date : True for datetime.date or False for datetime.datetime object

        Returns:
            return datetime.date or datetime.datetime or dict object
    """
    if type(object) not in (datetime.datetime, datetime.date, dict):
        raise ValueError(
            f"Acceptable object types : [datetime.datetime, datetime.date, dict], got {type(object).__name__}"
        )

    if type(object) == dict:
        if use_date:
            return datetime.date(object.get("year"),object.get("month"),object.get("day"))
        return datetime.datetime(object.get("year"),object.get("month"),object.get("day"),object.get("hour",0),object.get("minute",0),object.get("second",0),object.get("m_second",0))

    r_data = {}
    try:
        r_data["year"] = object.year
    except AttributeError:
        pass
    try:
        r_data["month"] = object.month
    except AttributeError:
        pass
    try:
        r_data["day"] = object.day
    except AttributeError:
        pass
    try:
        r_data["hour"] = object.hour
    except AttributeError:
        pass
    try:
        r_data["minute"] = object.minute
    except AttributeError:
        pass
    try:
        r_data["second"] = object.second
    except AttributeError:
        pass
    try:
        r_data["m_second"] = object.microsecond
    except AttributeError:
        pass

    return r_data
