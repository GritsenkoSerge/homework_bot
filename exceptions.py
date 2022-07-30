class GetAPIRequestError(Exception):
    """Ошибка выполнения запроса к API."""

    pass


class EmptyAPIResponseError(Exception):
    """Пустой ответ от API."""

    pass


class StatusAPIResponseError(Exception):
    """Ошибка статуса ответа от API."""

    pass


class JSONAPIResponseError(Exception):
    """Ошибка преобразования в JSON ответа от API."""

    pass


class UnknownHomeworkStatusError(Exception):
    """Недокументированный статус проверки работы."""

    pass
