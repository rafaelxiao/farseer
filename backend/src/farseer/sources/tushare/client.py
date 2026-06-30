"""Tushare API helper — returns a configured pro instance."""

import tushare as ts
from farseer.config import settings


def get_tushare_pro():
    """Get configured tushare pro_api instance.

    Supports both official tushare.pro and third-party mirrors.
    If TUSHARE_API_URL is set in .env, uses that as the API endpoint.
    Must pass token directly (not via set_token) for third-party mirrors.
    """
    pro = ts.pro_api(settings.tushare_token)

    if settings.tushare_api_url:
        pro._DataApi__http_url = settings.tushare_api_url

    return pro
