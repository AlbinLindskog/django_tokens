from django.test import TestCase, override_settings

from django_tokens import HMACToken, CacheToken


class TestHMACToken(HMACToken):
    salt = 'test'

    def check_validity(self):
        pass


class SingleUseTestHMACToken(HMACToken):
    salt = 'single-use'
    used = False

    def check_validity(self):
        if SingleUseTestHMACToken.used:
            raise self.AlreadyUsed
        else:
            SingleUseTestHMACToken.used = True


class CustomInitHMACToken(HMACToken):
    """
    Here we just reverse the input, it's a stand-in for some more complex data
    handling, .e.g. storing a database id and the fetching it from the database
    once the token has been recreated.
    """
    salt = 'custom-init'

    def __init__(self, *, username):
        super().__init__(rev=username[::-1])

    @property
    def username(self):
        return self.rev[::-1]

    def check_validity(self):
        pass


class TestCacheToken(CacheToken):
    key_length = 10


class CustomInitCacheToken(CacheToken):
    """
    See CustomInitHMACToken.
    """

    def __init__(self, *, username):
        super().__init__(rev=username[::-1])

    @property
    def username(self):
        return self.rev[::-1]


class HMACTokenTestCase(TestCase):

    def test_attribute_access(self):
        email = 'hej@mail.com'
        token = TestHMACToken(email=email)
        self.assertEqual(token.email, email)

    def test_key_format(self):
        key = TestHMACToken(year=2019).key
        self.assertRegex(key, r'^[A-z0-9]{18}:[A-z0-9]{6}:[A-z0-9-_=]{27}$')

    def test_recreate_from_key(self):
        token = TestHMACToken(user_id=1294)
        re_token = TestHMACToken.from_key(token.key)
        self.assertEqual(token._data, re_token._data)

    def test_settings_priority(self):
        # First we check the default setting:
        self.assertEqual(TestHMACToken.get_max_age(), 300)

        # The we apply user provided django settings
        with self.settings(HMAC_TOKEN_MAX_AGE=120, HMAC_TOKEN_SALT='hej'):
            self.assertEqual(TestHMACToken.get_max_age(), 120)

            # Which are still overriden by class attributes
            self.assertEqual(TestHMACToken.get_salt(), 'test')

    def test_invalid_key(self):
        key = 'invalid'
        with self.assertRaises(TestHMACToken.DoesNotExist):
            TestHMACToken.from_key(key)

    def test_expired_key(self):
        """
        Ensure that an expired key is treated the same as an invalid key.
        """
        key = TestHMACToken(email='hej@mail.com').key
        with self.settings(HMAC_TOKEN_MAX_AGE=0):
            with self.assertRaises(TestHMACToken.DoesNotExist):
                TestHMACToken.from_key(key)

    def test_single_use_with_check_validity_override(self):
        """
        Ensure that it is possible to create single user HMACTokens by
        overriding check_validity.
        """
        key = SingleUseTestHMACToken(email='hej@mail.com').key

        token = SingleUseTestHMACToken.from_key(key)
        with self.assertRaises(SingleUseTestHMACToken.DoesNotExist):
            token = SingleUseTestHMACToken.from_key(key)

    def test_warnings(self):
        """
        Ensure that the HMACToken warns about the unideal defaults.
        """
        token = HMACToken(username='dharoc')

        with self.assertWarns(Warning) as cm:
            key = token.key
        self.assertEqual(
            str(cm.warnings[0].message),
            'Leaving the HMACToken salt as the '
            'default value is a security risk.'
        )

        with self.assertWarns(Warning) as cm:
            re_token = HMACToken.from_key(key)
        self.assertEqual(
            str(cm.warnings[1].message),
            "'check_validity' method not overridden for HMACToken. "
            "Tokens will not be single use."
        )

    def test_custom_init_methods(self):
        """
        Make sure we can still recreate the token when you subclass it and
        write a custom __init__ method.
        """
        username = 'dharoc'
        key = CustomInitHMACToken(username=username).key
        token = CustomInitHMACToken.from_key(key)
        self.assertEqual(token.username, username)
        self.assertEqual(token.rev, username[::-1])


class CacheTokenTestCase(TestCase):

    def test_attribute_access(self):
        email = 'hej@mail.com'
        token = TestCacheToken(email=email)
        self.assertEqual(token.email, email)
    
    def test_key_format(self):
        token = TestCacheToken(year=2019)
        key = TestCacheToken(year=2019).key
        self.assertRegex(key, r'^[A-z0-9]{10}$')

    def test_recreate_from_key(self):
        token = TestCacheToken(user_id=1294)
        re_token = TestCacheToken.from_key(token.key)
        self.assertEqual(token._data, re_token._data)

    def test_settings_priority(self):
        # First we check the default setting:
        self.assertEqual(TestCacheToken.get_max_age(), 300)

        # The we apply user provided django settings
        with self.settings(CACHE_TOKEN_MAX_AGE=120, CACHE_TOKEN_KEY_LENGTH=10):
            self.assertEqual(TestCacheToken.get_max_age(), 120)

            # Which are still overriden by class attributes
            self.assertEqual(TestCacheToken.get_key_length(), 10)

    def test_invalid_key(self):
        key = 'invalid'
        with self.assertRaises(TestCacheToken.DoesNotExist):
            TestCacheToken.from_key(key)

    def test_expired_key(self):
        """
        Ensure that an expired key is treated the same as an invalid key.
        """
        with self.settings(CACHE_TOKEN_MAX_AGE=0):
            key = TestCacheToken(email='hej@mail.com').key
            with self.assertRaises(TestCacheToken.DoesNotExist):
                TestCacheToken.from_key(key)

    def test_single_user(self):
        key = TestCacheToken(email='hej@mail.com').key

        token = TestCacheToken.from_key(key)
        with self.assertRaises(TestCacheToken.DoesNotExist):
            token = TestCacheToken.from_key(key)

    def test_custom_init_methods(self):
        """
        Make sure we can still recreate the token when you subclass it and
        write a custom __init__ method.
        """
        username = 'dharoc'
        key = CustomInitCacheToken(username=username).key
        token = CustomInitCacheToken.from_key(key)
        self.assertEqual(token.username, username)
        self.assertEqual(token.rev, username[::-1])
