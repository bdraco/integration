import mimetypes

from aiohttp import web

from custom_components.hacs.helpers.functions.file_etag import async_get_etag
from custom_components.hacs.helpers.functions.logger import getLogger
from custom_components.hacs.helpers.functions.path_exsist import async_path_exsist
from custom_components.hacs.share import get_hacs

_LOGGER = getLogger()

LONG_LIVE_CACHE_CONTROL = "public, max-age=2678400"
REVALIDATE_CACHE_CONTROL = "no-cache"


async def async_serve_category_file(request, requested_file):
    hacs = get_hacs()
    response = None

    try:
        if requested_file.startswith("themes/"):
            servefile = f"{hacs.core.config_path}/{requested_file}"
            cache_header = LONG_LIVE_CACHE_CONTROL
        else:
            servefile = f"{hacs.core.config_path}/www/community/{requested_file}"
            cache_header = LONG_LIVE_CACHE_CONTROL
        response = await async_serve_static_file_with_cache_header(
            request, servefile, requested_file, cache_header
        )
    except (Exception, BaseException):
        _LOGGER.exception("Error trying to serve %s", requested_file)

    if response is not None:
        return response

    return web.Response(status=404)


async def async_serve_static_file_with_cache_header(
    request, servefile, requested_file, cache_header
):
    """Serve a static file without an etag."""
    if await async_path_exsist(servefile):
        _LOGGER.error(
            "%s tried to request '%s' but the file does not exist",
            request.remote,
            servefile,
        )
        return None

    _LOGGER.debug("Serving %s from %s", requested_file, servefile)
    response = web.FileResponse(servefile)
    response.headers["Cache-Control"] = cache_header
    return response
