Changelog
=========

0.6 (2012-06-29)
----------------

- **backwards-incompatible change**

  Starting in 0.6 django-phased now requires loading template tag
  libraries inside the ``phased`` block again. This was done to
  improve compatibility with Django 1.4 and future versions.

- Started to use Travis CI for testing:

  http://travis-ci.org/codysoyland/django-phased
