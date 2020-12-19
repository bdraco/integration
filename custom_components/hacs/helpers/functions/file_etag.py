# pylint: disable=missing-class-docstring,missing-module-docstring,missing-function-docstring,no-member
import os

from custom_components.hacs.share import get_hacs
from pathlib import Path


def get_etag(path) -> bool:
    file_path = Path(path)
    if not file_path.exists():
        return None
    return hash(file_path.read_bytes())


async def async_get_etag(path) -> bool:
    hass = get_hacs().hass
    etag = await hass.async_add_executor_job(get_etag, path)
    if etag is None:
        return None
    return '"' + str(hex(etag)) + '"'
