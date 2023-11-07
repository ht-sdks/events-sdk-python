import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
# Don't import htevents-python module here, since deps may not be installed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hightouch','htevents'))
from version import VERSION

long_description = '''
Events SDK Python for Hightouch event collection.

See https://github.com/ht-sdks/events-sdk-python for details.
'''

install_requires = [
    "requests~=2.7",
    "backoff~=2.1",
    "python-dateutil~=2.2",
]

tests_require = [
    "PyJWT~=2.8",
    "pyjwt[crypto]",
    "mock==2.0.0",
    "ruff==0.1.4",
]

setup(
    name='events-sdk-python',
    version=VERSION,
    url='https://github.com/ht-sdks/events-sdk-python',
    author='Hightouch',
    author_email='engineering@hightouch.com',
    maintainer='Hightouch',
    maintainer_email='engineering@hightouch.com',
    test_suite='hightouch.htevents.test.all',
    packages=['hightouch.htevents', 'hightouch.htevents.test'],
    python_requires='>=3.6.0',
    license='MIT License',
    install_requires=install_requires,
    extras_require={
        'test': tests_require
    },
    description='Events SDK Python',
    long_description=long_description,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
