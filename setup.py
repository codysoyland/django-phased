import os
from distutils.core import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

README = read('README.md')

setup(
    name = "django-phased",
    version = "0.5.1",
    url = 'http://github.com/codysoyland/django-phased',
    license = 'BSD',
    description = "Simple two-phase template rendering application useful for caching of authenticated requests.",
    long_description = README,
    author = 'Cody Soyland',
    author_email = 'codysoyland@gmail.com',
    packages = [
        'phased',
        'phased.templatetags',
    ],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
