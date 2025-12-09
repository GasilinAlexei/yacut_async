from datetime import datetime

from yacut_async import db

from yacut_async.constants import MAX_ORIGINAL_LINK_LENGTH, MAX_SHORT_ID_LENGTH


class URLMap(db.Model):
    """Модель для хранения оригинальной и короткой ссылки."""

    id = db.Column(db.Integer, primary_key=True)
    original = db.Column(db.String(MAX_ORIGINAL_LINK_LENGTH),
                         nullable=False)
    short = db.Column(db.String(MAX_SHORT_ID_LENGTH),
                      unique=True,
                      nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
