from django.conf import settings
from django.utils.module_loading import import_string


class DEFAULTS:
    HMAC_TOKEN_SERIALIZER = 'django.core.signing.JSONSerializer'
    HMAC_TOKEN_COMPRESS = False
    HMAC_TOKEN_SALT = 'django_tokens.salt'
    HMAC_TOKEN_MAX_AGE = 300

    CACHE_TOKEN_CACHE_NAME = 'default'
    CACHE_TOKEN_KEY_LENGTH = 20
    CACHE_TOKEN_MAX_AGE = 300


IMPORT_STRINGS = (
    'HMAC_TOKEN_SERIALIZER'
)


class TokenSettings:
    """
    Custom settings module for django_tokens. Checks if the requested setting
    is present in the user provided django settings module, if not it fall
    backs to the projects default settings.

    All settings are resolved when needed, there is no caching, as it's rare
    to instantiate more then one Token per request, so let's keep it simple.
    """

    def __init__(self, user_settings=None, defaults=None, import_strings=None):
        self._user_settings = user_settings
        self._defaults = defaults
        self._import_strings = import_strings

    def __getattr__(self, attr):
        fallback = getattr(self._defaults, attr)
        val = getattr(self._user_settings, attr, fallback)

        if attr in self._import_strings:
            val = import_string(val)

        return val


settings = TokenSettings(settings, DEFAULTS(), IMPORT_STRINGS)


default_settings = DEFAULTS()


def setting(val, default):
    return val if val is not None else default
