Django Tokens
-------------------------------------
Generic tokens for Django which allow you to safely pass data through an
untrusted medium (read: the user).

Includes the stateless HMAC signed tokens and stateful tokens. The stateful
tokens are backed by Django's cache framework and thus support in memory,
on file, in database, or dedicated cache system, e.g. redis, storage.

To use a Token simple instantiate it with the required data, pass the key
around, and when desired recreate the Token from the key.::

    from django_tokens import HMACToken

    >>> token = HMACToken(email='hello@mail.com', first_login=False)
    >>> key = token.key
    ... eyJlbWFpbCI6ImhlbGxvQG1haWwuY29tIn0:1je3sM:ocIxstvgcMZL2ZE1K_jA-W7UbTE
    >>> token = HMACToken.from_key(key)
    >>> token.email
    ... 'hello@mail.com'

An altered key or one that's already been used are invalid.::

    >>> token = HMACToken.from_key(key)
    ... django.core.exceptions.ObjectDoesNotExist


It is recommended that you create a subclass of the tokens with a explicit
name for each use case you have.

When defining a subclass with a specific __init__ call signature; all kwargs
passed to the parent's class __init__ method will be available as attributes
on the instance. Any attributes set in the __init__ method will not be
available when the token is recreated from its key.

Settings
^^^^^^^^
Django Tokens contains two types of Tokens, stateless HMACTokens and stateful
CacheTokens, each type have their own settings. The settings can be set either
as class level attributes or through Django settings, where the former takes
precedence over the latter.

HMACToken
~~~~~~~~~~
HMACToken.salt or settings.HMAC_TOKEN_SALT (str):
    Salt used in the signature. Defaults to 'django_tokens.salt'. Leaving this
    as the default or using the same salt for different applications of
    HMACTokens is a security risk.

MHACToken.serializer or settings.HMAC_TOKEN_SERIALISER (str):
    Import string of serializer class to use to serialize the provided data.
    The default is 'django.core.signing.JSONSerializer'. Custom serializers
    must define the 'dumps' and 'loads' methods.

MHACToken.compress or settings.HMAC_TOKEN_COMPRESS (bool):
    Denotes whether to try and compress the data using zlib, defaults to False.

MHACToken.max_age or settings.HMAC_TOKEN_MAX_AGE (int):
    The lifetime of the token in seconds before its key becomes invalid. The
    default is 300, i.e. 5 minutes.

CacheTokens
~~~~~~~~~~
CacheToken.cache_name or settings.CACHE_TOKEN_CACHE_NAME (str):
    Name of cache to store the data in. Point this to a cache backend that uses
    an appropriate storage for your use case. The default is the Django default
    cache 'default'.

CacheToken.key_length or settings.CACHE_TOKEN_KEY_LENGTH (int):
    The length of the generated key, the default is 20.

CacheToken.max_age or settings.CACHE_TOKEN_MAX_AGE (int):
    The lifetime of the token in seconds before its key becomes invalid. The
    default is 300, i.e. 5 minutes.

Development
^^^^^^^^^^^
To run the tests; clone the repository, setup the virtual environment, and run
the tests.::

    # Setup the virtual environment
    $ virtualenv test_env
    $ source test_env/bin/activate
    $ pip3 install -r test_requirements.txt

    # Run the tests
    $ cd tests
    $ python3 manage.py test
