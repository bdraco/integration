import mimetypes

from aiohttp import web

from custom_components.hacs.helpers.functions.file_etag import async_get_etag
from custom_components.hacs.helpers.functions.logger import getLogger
from custom_components.hacs.helpers.functions.path_exsist import async_path_exsist
from custom_components.hacs.share import get_hacs

_LOGGER = getLogger()


async def async_serve_category_file(request, requested_file):
    hacs = get_hacs()
    response = None

    try:
        if requested_file.startswith("themes/"):
            servefile = f"{hacs.core.config_path}/{requested_file}"
            response = await async_serve_static_file(request, servefile, requested_file)
        else:
            servefile = f"{hacs.core.config_path}/www/community/{requested_file}"
            response = await async_serve_static_file_with_etag(
                request, servefile, requested_file
            )
    except (Exception, BaseException):
        _LOGGER.exception("Error trying to serve %s", requested_file)

    if response is not None:
        return response

    return web.Response(status=404)


async def async_serve_static_file(request, servefile, requested_file):
    """Serve a static file without an etag."""
    if await async_path_exsist(servefile):
        _LOGGER.debug("Serving %s from %s", requested_file, servefile)
        response = web.FileResponse(servefile)
        response.headers["Cache-Control"] = "public, max-age=2678400"
        return response

    _LOGGER.error(
        "%s tried to request '%s' but the file does not exist",
        request.remote,
        servefile,
    )
    return None


async def async_serve_static_file_with_etag(request, servefile, requested_file):
    """Serve a static file with an etag."""
    etag = await async_get_etag(servefile)
    if_none_match_header = request.headers.get("if-none-match")

    if (
        etag is not None
        and if_none_match_header is not None
        and _match_etag(etag, if_none_match_header)
    ):

        response = web.StreamResponse(status=304)
        # If we do not set a content-type, aiohttp
        # will default to "application/octet-stream" which
        # is likely not what we want
        content_type, _ = mimetypes.guess_type(servefile)
        response.content_type = content_type or "application/octet-stream"
        response.content_length = None

        _LOGGER.debug(
            "Serving %s from %s with etag %s (not-modified)",
            requested_file,
            servefile,
            etag,
        )
        return response

    if etag is not None:
        response = web.FileResponse(servefile)
        response.headers["Cache-Control"] = "no-cache"
        response.headers["Etag"] = etag

        _LOGGER.debug(
            "Serving %s from %s with etag %s (not cached)",
            requested_file,
            servefile,
            etag,
        )
        return response

    _LOGGER.error(
        "%s tried to request '%s' but the file does not exist",
        request.remote,
        servefile,
    )
    return None


def _match_etag(etag, if_none_match_header):
    """Check to see if an etag matches."""
    for if_none_match_ele in if_none_match_header.split(","):
        if if_none_match_ele.strip() == etag:
            return True
    return False
