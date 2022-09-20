class LightError(Exception):
    """Применяется для ошибок, о которых не нужно уведомлять в Telegram."""

    pass


class KeyLightError(LightError, KeyError):
    """Применяется для ошибок, о которых не нужно уведомлять в Telegram."""

    pass
