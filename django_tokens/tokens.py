import warnings

from django.core import signing
from django.core.cache import caches
from django.core.exceptions import ObjectDoesNotExist
from django.utils.crypto import get_random_string

from .exceptions import ObjectAlreadyUsed
from .settings import settings, default_settings, setting


class HMACToken:
    """
    Stateless token used to safely pass data through an untrusted medium,
    i.e. the user.

    The data is stored as a URL-safe, hmac/SHA1 signed base64 compressed
    JSON string.

    Note:
        In order for HMACTokens to be single use you must subclass it and
        override the check_validity method to check if you have already acted
        on it. Raise self.AlreadyUsed if you have already acted on the token.
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
        """
        Every key-value pair in data will be available as attributes of the
        token. Any attributes other set in the __init__ method will not be
        available when the token is recreated from its key.
        """
        self._data = data

    def __getattr__(self, attr):
        """
        If an attribute does not exist on this instance, we also attempt to
        retrieve it from the underlying data store.

        This approach creates nontransparent AttributeErrors in @properties,
        but it is preferable to the alternative; adding data to self.__dict__
        to dynamically set the attributes, as that leads to all attributes
        on the instance being stored when creating the key, not just those
        explicitly passed as data.
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
            data = signing.loads(
                key, max_age=cls.get_max_age(), salt=cls.get_salt()
            )
            # Initialize without calling __init__ to allow subclasses of
            # HMACToken to have custom __init__ call signature.
            self = self = cls.__new__(cls)
            self._data = data

            self.check_validity()
        except (TypeError, ObjectAlreadyUsed,
                signing.SignatureExpired,
                signing.BadSignature) as e:
            raise cls.DoesNotExist from e
        else:
            return self

    @property
    def key(self):
        return signing.dumps(
            obj=self._data,
            salt=self.get_salt(),
            serializer=self.get_serializer(),
            compress=self.get_compress()
        )

    def check_validity(self):
        cls_name = self.__class__.__name__
        warnings.warn(
            f"'check_validity' method not overridden for {cls_name}. "
            f"Tokens will not be single use.")

    @classmethod
    def get_serializer(cls):
        return setting(cls.serializer, settings.HMAC_TOKEN_SERIALIZER)

    @classmethod
    def get_compress(cls):
        return setting(cls.compress, settings.HMAC_TOKEN_COMPRESS)

    @classmethod
    def get_salt(cls):
        salt = setting(cls.salt, settings.HMAC_TOKEN_SALT)
        if salt == default_settings.HMAC_TOKEN_SALT:
            warnings.warn(
                'Leaving the HMACToken salt as the '
                'default value is a security risk.'
             )
        return salt

    @classmethod
    def get_max_age(cls):
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
    _key = None

    def __init__(self, **data):
        """
        Every key-value pair in data will be available as attributes of the
        token. Any attributes other set in the __init__ method will not be
        available when the token is recreated from its key.
        """
        self._data = data

    def __getattr__(self, attr):
        """
        If an attribute does not exist on this instance, we also attempt to
        retrieve it from the underlying data store.

        This approach creates nontransparent AttributeErrors in @properties,
        but it is preferable to the alternative; adding data to self.__dict__
        to dynamically set the attributes, as that leads to all attributes
        on the instance being stored when creating the key, not just those
        explicitly passed as data.
        """
        try:
            return self._data[attr]
        except KeyError as e:
            raise AttributeError(
                f"'{self.__class__.__name__}' has no attribute '{attr}'"
            ) from e

    @classmethod
    def from_key(cls, key):
        data = cls.get_cache().get(key, None)
        if data is None:
            raise cls.DoesNotExist
        else:
            cls.get_cache().delete(key)
            # Initialize without calling __init__ to allow subclasses of
            # CacheToken to have custom __init__ call signature.
            self = cls.__new__(cls)
            self._data = data
            return self

    @property
    def key(self):
        if not self._key:
            self._key = get_random_string(length=self.get_key_length())
            self.get_cache().set(self._key, self._data, timeout=self.get_max_age())
        return self._key

    @classmethod
    def get_cache(cls):
        cache_name = setting(cls.cache_name, settings.CACHE_TOKEN_CACHE_NAME)
        return caches[cache_name]

    @classmethod
    def get_key_length(cls):
        return setting(cls.key_length, settings.CACHE_TOKEN_KEY_LENGTH)

    @classmethod
    def get_max_age(cls):
        return setting(cls.max_age, settings.CACHE_TOKEN_MAX_AGE)
