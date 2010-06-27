.. _ref-tutorial:

==================================
Getting Started with django-phased
==================================

django-phased is an implementation of a two-phase template rendering system
to allow caching of pages that otherwise would be uncachable due to
user-specific content that needs to be rendered (such as a signed-in notice
in the corner of the page). This technique has been described in detail by
Adrian Holovaty in `this blog post
<http://www.holovaty.com/writing/django-two-phased-rendering/>`_.

Installation
============

To install django-phased, either check out the source from Github or install
from PyPI_:

  * Check out django-phased from GitHub_ and run `python setup.py install`
    in the source checkout, or

  * Run ``pip install django-phased``.

.. _GitHub: http://github.com/codysoyland/django-phased
.. _PyPI: http://pypi.python.org/


Configuration
=============

To make django-phased tags available to your templates, add ``'phased'`` to
your ``INSTALLED_APPS``.

Install :class:`phased.middleware.PhasedRenderMiddleware` to enable
second-phase rendering of templates.

If using Django's caching middleware, use
:class:`phased.middleware.PatchedVaryUpdateCacheMiddleware` to bypass the
Vary: Cookie behavior of that middleware.

A common setup for middleware classes would be this::

    MIDDLEWARE_CLASSES = (
        'phased.middleware.PhasedRenderMiddleware',
        'phased.middleware.PatchedVaryUpdateCacheMiddleware',
        ...
        'django.middleware.cache.FetchFromCacheMiddleware',
    )

See :doc:`settings` for additional settings.
