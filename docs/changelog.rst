Changelog
=========

0.6.1 (2012-07-11)
------------------

- Moved docs to Read The Docs and extended the tutorial section:

  http://django-phased.readthedocs.org/

- Added :attr:`~phased.templatetags.phased_tags.phasedcache` template
  tag for two-phase fragment caching.

0.6 (2012-06-29)
----------------

- **backwards-incompatible change**

  Starting in 0.6 django-phased now requires loading template tag
  libraries inside the ``phased`` block again. This was done to
  improve compatibility with Django 1.4 and future versions.

- Started to use Travis CI for testing:

  http://travis-ci.org/codysoyland/django-phased
