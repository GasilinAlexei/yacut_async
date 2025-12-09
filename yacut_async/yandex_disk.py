import asyncio
import os
from typing import Iterable, List

import aiohttp
from dotenv import load_dotenv
from werkzeug.datastructures import FileStorage

API_HOST = 'https://cloud-api.yandex.net/'
API_VERSION = 'v1'

DISK_UPLOAD_URL = f'{API_HOST}{API_VERSION}/disk/resources/upload'
DISK_RESOURCES_URL = f'{API_HOST}{API_VERSION}/disk/resources'

load_dotenv()
DISK_TOKEN = os.getenv('DISK_TOKEN')


AUTH_HEADERS = {
    'Authorization': f'OAuth {DISK_TOKEN}',
}


class YandexDiskError(RuntimeError):
    """Ошибка при работе с Яндекс Диском."""


async def _ensure_folder_exists(
    session: aiohttp.ClientSession,
    base_folder: str,
) -> None:
    """Создаёт папку base_folder на Диске, если она ещё не существует."""

    folder_path = f'/{base_folder}'.rstrip('/')

    params = {'path': folder_path}
    async with session.put(DISK_RESOURCES_URL,
                           headers=AUTH_HEADERS,
                           params=params) as response:
        # 201 — папка создана,
        # 409 — такая папка уже существует.
        if response.status in (201, 409):
            return

        # Любой другой статус — считаем ошибкой.
        try:
            data = await response.json()
        except aiohttp.ContentTypeError:
            text = await response.text()
            data = {'raw': text}

        raise YandexDiskError(
            f'Не удалось создать папку {folder_path}: '
            f'status={response.status}, response={data}'
        )


async def _get_upload_href(
    session: aiohttp.ClientSession,
    disk_path: str,
) -> str:
    """Запрашивает у API Яндекс Диска URL для загрузки файла."""
    params = {
        'path': disk_path,
        'overwrite': 'true',
    }
    async with session.get(DISK_UPLOAD_URL,
                           headers=AUTH_HEADERS,
                           params=params) as response:
        try:
            data = await response.json()
        except aiohttp.ContentTypeError:
            text = await response.text()
            data = {'raw': text}

        if response.status != 200:
            raise YandexDiskError(
                f'Не удалось получить ссылку загрузки для {disk_path}: '
                f'status={response.status}, response={data}'
            )

        href = data.get('href')
        if not href:
            raise YandexDiskError(
                f'В ответе Яндекс Диска нет поля "href": {data}'
            )
        return href


async def _upload_single_file(
    session: aiohttp.ClientSession,
    file_storage: FileStorage,
    disk_path: str,
) -> str:
    """Загружает один файл FileStorage на Яндекс Диск по указанному пути."""
    upload_href = await _get_upload_href(session, disk_path)
    file_storage.stream.seek(0)
    file_bytes = file_storage.read()

    async with session.put(upload_href, data=file_bytes) as response:
        if response.status not in (200, 201, 202):
            text = await response.text()
            raise YandexDiskError(
                f'Ошибка загрузки файла {disk_path}: '
                f'status={response.status}, response={text}'
            )

    return disk_path


async def async_upload_files(
    files: Iterable[FileStorage],
    base_folder: str = 'yacut_uploads',
) -> List[str]:
    """
    Асинхронно загружает несколько файлов на Яндекс Диск.

    :param files: итерируемый объект с FileStorage (из формы Flask).
    :param base_folder: папка на Я.Диске, в которую складывать файлы.
    :return: список путей на Яндекс Диске для загруженных файлов.
    """
    async with aiohttp.ClientSession() as session:
        await _ensure_folder_exists(session, base_folder)

        tasks = []
        disk_paths: List[str] = []

        for file_storage in files:
            disk_path = f'/{base_folder}/{file_storage.filename}'
            disk_paths.append(disk_path)
            tasks.append(_upload_single_file(session, file_storage, disk_path))

        await asyncio.gather(*tasks)

    return disk_paths


def upload_files(
    files: Iterable[FileStorage],
    base_folder: str = 'yacut_uploads',
) -> List[str]:
    """
    Синхронная обёртка над async_upload_files() для вызова из Flask view.

    Flask у нас синхронный, поэтому из view-функции удобно вызывать
    именно эту функцию, а внутри неё уже запускать event loop.
    """
    return asyncio.run(async_upload_files(files, base_folder=base_folder))
