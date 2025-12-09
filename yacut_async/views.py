from flask import abort, flash, redirect, render_template, request, url_for

from yacut_async import app, db
from yacut_async.constants import FILES_ENDPOINT
from yacut_async.forms import FilesUploadForm, LinkForm
from yacut_async.models import URLMap
from yacut_async.utils import get_unique_short_id
from yacut_async.yandex_disk import upload_files, YandexDiskError


@app.route('/', methods=['GET', 'POST'])
def index():
    """Обрабатывает форму создания коротких ссылок на длинные URL."""
    form = LinkForm()
    short_link = None

    if form.validate_on_submit():
        original_link = form.original_link.data
        custom_id = form.custom_id.data or get_unique_short_id()

        if custom_id == FILES_ENDPOINT:
            flash('Предложенный вариант короткой ссылки уже существует.')
            return render_template('index.html', form=form)

        if URLMap.query.filter_by(short=custom_id).first() is not None:
            flash('Предложенный вариант короткой ссылки уже существует.')
            return render_template('index.html', form=form)

        url_map = URLMap(original=original_link, short=custom_id)
        db.session.add(url_map)
        db.session.commit()

        short_link = request.host_url + url_map.short

    return render_template('index.html', form=form, short_link=short_link)


@app.route('/files', methods=['GET', 'POST'])
def files():
    """Обрабатывает загрузку файлов на Яндекс Диск."""
    form = FilesUploadForm()
    uploaded_files = []

    if form.validate_on_submit():
        files_list = form.files.data
        try:
            # загружаем файлы на Яндекс Диск (асинхронно внутри)
            disk_paths = upload_files(files_list)
            for disk_path in disk_paths:
                short_id = get_unique_short_id()
                url_map = URLMap(
                    original=f'https://disk.yandex.ru/d{disk_path}',
                    short=short_id,
                )
                db.session.add(url_map)
                uploaded_files.append(
                    {
                        'filename': disk_path.rsplit('/', 1)[-1],
                        'short_url': url_for(
                            'redirect_to_original',
                            short=short_id,
                            _external=True,
                        ),
                    }
                )
            db.session.commit()
            flash('Файлы успешно загружены на Яндекс Диск.', 'success')
        except YandexDiskError as e:
            app.logger.exception('Ошибка при работе с Яндекс Диском: %s', e)
            flash(
                'Произошла ошибка при загрузке файлов на Яндекс Диск.',
                'danger',
            )

    return render_template(
        'files.html',
        form=form,
        uploaded_files=uploaded_files,
    )


@app.route('/<string:short>')
def redirect_to_original(short: str):
    """Переадресует по короткой ссылке на исходный адрес или скачивание файла."""
    url_map = URLMap.query.filter_by(short=short).first()
    if url_map is None:
        abort(404)
    return redirect(url_map.original)
