from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired
from wtforms import StringField, SubmitField, MultipleFileField, StringField
from wtforms.validators import (
    DataRequired, Length, Optional, URL, ValidationError
)

from yacut_async.constants import (
    MAX_ORIGINAL_LINK_LENGTH, MAX_SHORT_ID_LENGTH, FILES_ENDPOINT
)
from yacut_async.utils import is_valid_short_id


class LinkForm(FlaskForm):
    """Форма для ввода оригинальной и короткой ссылки."""

    original_link = StringField(
        'Длинная ссылка',
        validators=[DataRequired(),
                    URL(),
                    Length(max=MAX_ORIGINAL_LINK_LENGTH)]
    )
    custom_id = StringField(
        'Ваш вариант короткой ссылки',
        validators=[Optional(), Length(max=MAX_SHORT_ID_LENGTH)]
    )
    submit = SubmitField('Создать')

    def validate_custom_id(self, field):
        """Проверяет идентификатор на корректность и зарезервированный путь."""

        custom_id = field.data
        if not custom_id:
            return
        if custom_id == FILES_ENDPOINT:
            raise ValidationError(
                'Предложенный вариант короткой ссылки уже существует.'
            )
        if not is_valid_short_id(custom_id):
            raise ValidationError(
                'Указано недопустимое имя для короткой ссылки.'
            )


class FilesUploadForm(FlaskForm):
    """Форма для загрузки нескольких файлов на Яндекс Диск."""

    files = MultipleFileField(
        'Выберите файлы',
        validators=[
            FileRequired('Нужно выбрать хотя бы один файл.'),
            FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'bmp'],
                        'Допустимы только файлы изображений.'),
        ],
    )
