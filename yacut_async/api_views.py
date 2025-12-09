from http import HTTPStatus

from flask import jsonify, request

from yacut_async import app, db
from yacut_async.constants import MAX_SHORT_ID_LENGTH, FILES_ENDPOINT
from yacut_async.error_handlers import InvalidAPIUsage
from yacut_async.models import URLMap
from yacut_async.utils import get_unique_short_id, is_valid_short_id


@app.route('/api/id/', methods=['POST'])
def create_short_url():
    """Создаёт новую короткую ссылку через API."""

    data = request.get_json(silent=True)
    if data is None:
        raise InvalidAPIUsage('Отсутствует тело запроса')

    original = data.get('url')
    if not original:
        raise InvalidAPIUsage('"url" является обязательным полем!')

    custom_id = data.get('custom_id')
    if custom_id:
        if custom_id == FILES_ENDPOINT:
            raise InvalidAPIUsage('Предложенный вариант короткой ссылки уже существует.')
        if len(custom_id) > MAX_SHORT_ID_LENGTH or not is_valid_short_id(
            custom_id
        ):
            raise InvalidAPIUsage('Указано недопустимое имя для короткой ссылки')
        if URLMap.query.filter_by(short=custom_id).first() is not None:
            raise InvalidAPIUsage('Предложенный вариант короткой ссылки уже существует.')
    else:
        custom_id = get_unique_short_id()

    url_map = URLMap(original=original, short=custom_id)
    db.session.add(url_map)
    db.session.commit()

    return (
        jsonify(
            {
                'url': url_map.original,
                'short_link': request.host_url + url_map.short,
            }
        ),
        HTTPStatus.CREATED,
    )


@app.route('/api/id/<string:short_id>/', methods=['GET'])
def get_original_url(short_id: str):
    """Возвращает оригинальный URL по короткому идентификатору."""

    url_map = URLMap.query.filter_by(short=short_id).first()
    if url_map is None:
        raise InvalidAPIUsage('Указанный id не найден', HTTPStatus.NOT_FOUND)

    return jsonify({'url': url_map.original}), HTTPStatus.OK
