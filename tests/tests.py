from django.test import TestCase, override_settings

from django_tokens import HMACToken, CacheToken


class TestHMACToken(HMACToken):
    salt = 'test'

    @classmethod
    def check_data(cls, data):
        return data


class SingleUseTestHMACToken(HMACToken):
    salt = 'single-use'
    used = False

    @classmethod
    def check_data(cls, data):
        if cls.used:
            raise cls.AlreadyUsed
        else:
            cls.used = True
        return data


class TestCacheToken(CacheToken):
    key_length = 10


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
        self.assertEqual(TestHMACToken._max_age, 300)

        # The we apply user provided django settings
        with self.settings(HMAC_TOKEN_MAX_AGE=120, HMAC_TOKEN_SALT='hej'):
            self.assertEqual(TestHMACToken._max_age, 120)

            # Which are still overriden by class attributes
            self.assertEqual(TestHMACToken._salt, 'test')

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

    def test_single_use_with_check_data_override(self):
        """
        Ensure that it is possible to create single user HMACTokens by
        overriding check_data.
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
            "'check_data' method not overridden for HMACToken. "
            "Tokens will not be single use."
        )


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
        self.assertEqual(TestCacheToken._max_age, 300)

        # The we apply user provided django settings
        with self.settings(CACHE_TOKEN_MAX_AGE=120, CACHE_TOKEN_KEY_LENGTH=10):
            self.assertEqual(TestCacheToken._max_age, 120)

            # Which are still overriden by class attributes
            self.assertEqual(TestCacheToken._key_length, 10)

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