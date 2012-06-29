import codecs
import re
from os import path
from setuptools import setup


def read(*parts):
    file_path = path.join(path.dirname(__file__), *parts)
    return codecs.open(file_path).read()


def find_version(*parts):
    version_file = read(*parts)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

setup(
    name="django-phased",
    version=find_version('phased', '__init__.py'),
    url='http://github.com/codysoyland/django-phased',
    license='BSD',
    description="Simple two-phase template rendering application useful for caching of authenticated requests.",
    long_description=read('README.rst'),
    author='Cody Soyland',
    author_email='codysoyland@gmail.com',
    packages=[
        'phased',
        'phased.templatetags',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
