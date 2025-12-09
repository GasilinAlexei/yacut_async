import random
import string

from yacut_async.models import URLMap
from yacut_async.constants import DEFAULT_SHORT_ID_LENGTH


ALLOWED_SHORT_CHARS = string.ascii_letters + string.digits


def is_valid_short_id(short_id: str) -> bool:
    """Проверяет, что идентификатор состоит только из разрешённых символов."""

    return (
        isinstance(short_id, str)
        and bool(short_id)
        and all(char in ALLOWED_SHORT_CHARS for char in short_id)
    )


def get_unique_short_id(length=DEFAULT_SHORT_ID_LENGTH):
    """Генерирует уникальный короткий идентификатор заданной длины."""
    characters = string.ascii_letters + string.digits
    while True:
        short_id = ''.join(random.choices(characters, k=length))
        if not URLMap.query.filter_by(short=short_id).first():
            return short_id
