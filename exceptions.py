class EasyError(Exception):
    """Применяется для ошибок, о которых не нужно уведомлять в Telegram."""

    pass


class EmptyKeyError(Exception):
    """Ошибка пустого поля"""

    pass
