from distutils.core import setup

setup(
    name='Django tokens',
    version='0.0.2',
    description='Tokens used to safely pass data through an untrusted medium.',
    long_description=open('README.rst').read(),
    install_requires=[],
    packages=['django_tokens'],
    author='Albin Lindskog',
    author_email='albin@zerebra.com',
    url='https://github.com/albinlindskog/django_tokens',
    zip_safe=True,
)
