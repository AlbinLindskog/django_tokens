import warnings

from django.core import signing
from django.core.cache import caches
from django.core.exceptions import ObjectDoesNotExist
from django.utils.crypto import get_random_string

from .exceptions import ObjectAlreadyUsed
from .settings import settings, default_settings, setting
from .utils import classproperty


class HMACToken:
    """
    Stateless token used to safely pass data through an untrusted medium,
    i.e. the user.

    The data is stored as a URL-safe, hmac/SHA1 signed base64 compressed
    JSON string.

    Note:
        In order for HMACTokens to be single use you must subclass it and
        override the check_data to check if you have already acted on it.
        How to implement that check will depend on your use case. In a single
        use login token you could include a last login timestamp in the token
        data and compare it the users current last login, for example.

    Attributes:
        salt (str): Salt used in the signature. Defaults to
            'django_tokens.salt'. Leaving this as the default or using the same
            salt for different applications of HMACTokens is a security risk.

        serializer (str): Import string of serializer class to use to serialize
            the provided data. Default: 'django.core.signing.JSONSerializer'.
            Custom serializers must define the  must define the 'dumps' and
            'loads' methods.

        compress (bool): Denotes whether to try and compress the data using
            zlib, defaults to False.

        max_age (int): The lifetime of the token in seconds before its key
            becomes invalid. The default is 300, i.e. 5 minutes.
    """

    AlreadyUsed = ObjectAlreadyUsed
    DoesNotExist = ObjectDoesNotExist
    salt = None
    serializer = None
    compress = None
    max_age = None

    def __init__(self, **data):
        self._data = data

    def __getattr__(self, attr):
        """
        If an attribute does not exist on this instance, we also attempt to
        retrieve it from the underlying data store.
        """
        try:
            return self._data[attr]
        except KeyError as e:
            raise AttributeError(
                f"'{self.__class__.__name__}' has no attribute '{attr}'"
            ) from e

    @classmethod
    def from_key(cls, key):
        """
        Recreate a HMACToken from its key.

        If the signing is invalid, expired or if the token has already been
        used: raise HMACToken.DoesNotExist.
        """
        try:
            data = signing.loads(key, max_age=cls._max_age, salt=cls._salt)
            data = cls.check_data(data)
        except (TypeError, ObjectAlreadyUsed,
                signing.SignatureExpired,
                signing.BadSignature) as e:
            raise cls.DoesNotExist from e
        else:
            return HMACToken(**data)

    @property
    def key(self):
        return signing.dumps(
            obj=self._data,
            salt=self._salt,
            serializer=self._serializer,
            compress=self._compress
        )

    @classmethod
    def check_data(cls, data):
        warnings.warn(
            f"'check_data' method not overridden for {cls.__name__}. "
            f"Tokens will not be single use.")
        return data

    @classproperty
    def _serializer(cls):
        return setting(cls.serializer, settings.HMAC_TOKEN_SERIALIZER)

    @classproperty
    def _compress(cls):
        return setting(cls.compress, settings.HMAC_TOKEN_COMPRESS)

    @classproperty
    def _salt(cls):
        salt = setting(cls.salt, settings.HMAC_TOKEN_SALT)
        if salt == default_settings.HMAC_TOKEN_SALT:
            warnings.warn(
                'Leaving the HMACToken salt as the '
                'default value is a security risk.'
             )
        return salt

    @classproperty
    def _max_age(cls):
        return setting(cls.max_age, settings.HMAC_TOKEN_MAX_AGE)


class CacheToken:
    """
    Statefull token used to safely pass data through an untrusted medium,
    i.e. the user.

    The data is stored in a cache backend and thus supports in memory,
    on file, in database, or dedicated cache system, e.g. redis.

    Attributes:
        cache_name (str): Name of cache to store the data in. Point this to a
            cache backend that uses an appropriate storage for your use case.
            The default is the Django default cache 'default'.

        key_length (int): The length of the generated key, the default is 20.

        max_age (int): The lifetime of the token in seconds before its key
            becomes invalid. The default is 300, i.e. 5 minutes.
    """
    DoesNotExist = ObjectDoesNotExist
    cache_name = None
    key_length = None
    max_age = None

    def __init__(self, **data):
        self._data = data
        self._key = None

    def __getattr__(self, attr):
        """
        If an attribute does not exist on this instance, we also attempt to
        retrieve it from the underlying data store.
        """
        try:
            return self._data[attr]
        except KeyError as e:
            raise AttributeError(
                f"'{self.__class__.__name__}' has no attribute '{attr}'"
            ) from e

    @classmethod
    def from_key(cls, key):
        data = cls._cache.get(key, None)
        if data is None:
            raise cls.DoesNotExist
        else:
            cls._cache.delete(key)
            return cls(**data)

    @property
    def key(self):
        if not self._key:
            self._key = get_random_string(length=self._key_length)
            self._cache.set(self._key, self._data, timeout=self._max_age)
        return self._key

    @classproperty
    def _cache(cls):
        cache_name = setting(cls.cache_name, settings.CACHE_TOKEN_CACHE_NAME)
        return caches[cache_name]

    @classproperty
    def _key_length(cls):
        return setting(cls.key_length, settings.CACHE_TOKEN_KEY_LENGTH)

    @classproperty
    def _max_age(cls):
        return setting(cls.max_age, settings.CACHE_TOKEN_MAX_AGE)