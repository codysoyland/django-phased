.. _ref-tutorial:

==========
Quickstart
==========

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

* Check out django-phased from GitHub_ and run ``python setup.py install``
  in the source checkout

  or

* Run ``pip install django-phased``.

.. _GitHub: http://github.com/codysoyland/django-phased
.. _PyPI: http://pypi.python.org/


Setup
=====

To make django-phased tags available to your templates, add ``'phased'`` to
your ``INSTALLED_APPS``.

You can either use ``phased`` via the
:ref:`PhasedRenderMiddleware <ref-middleware>` middleware or the
:attr:`~phased.templatetags.phased_tags.phasedcache` template tag.

Usage
=====

Middleware
----------

Install the :class:`~phased.middleware.PhasedRenderMiddleware` to enable
second-phase rendering of templates.

If using Django's caching middleware, use
:class:`~phased.middleware.PatchedVaryUpdateCacheMiddleware` to bypass the
``Vary: Cookie`` behavior of that middleware.

A common setup for middleware classes would be this:

.. code-block:: python

    MIDDLEWARE_CLASSES = (
        'phased.middleware.PhasedRenderMiddleware',
        'phased.middleware.PatchedVaryUpdateCacheMiddleware',
        ...
        'django.middleware.cache.FetchFromCacheMiddleware',
    )

See :doc:`settings` for additional settings.

Template Tag
------------

In order to use the ``phasedcache`` template tag you need to add
``'django.core.context_processors.request'`` to the
``TEMPLATE_CONTEXT_PROCESSORS`` settings variable and use ``RequestContext``
when you render your templates. See the Django docs on
`how to use RequestContext`_ in your views.

The ``phasedcache`` template tag works exactly like Django's
`cache template tag`_ except that it will run a second render pass using the
:attr:`~phased.utils.second_pass_render` function with value returned
from the cache.

See :attr:`~phased.templatetags.phased_tags.phasedcache` for details.

.. _`how to use RequestContext`: https://docs.djangoproject.com/en/dev/ref/templates/api/#django.template.RequestContext
.. _`cache template tag`: https://docs.djangoproject.com/en/dev/topics/cache/#template-fragment-caching
