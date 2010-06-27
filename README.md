django-phased
=============

A simple two-phase template rendering application useful for caching of authenticated requests.

How it works
------------

This technique has been desribed by Adrian Holovaty
[in this blog post](http://www.holovaty.com/writing/django-two-phased-rendering/)
and previously by Honza Kral. The idea is to first render the template with
certain blocks denoted as "phased," such that they will not be rendered, and
will remain valid template code that can be rendered with a second pass.

The second pass fetches the partially-rendered template from the cache and
performs a second render on it, using RequestContext to provide user-specific
context to the template. This enables very fast generation of pages that have
user-specific content, by bypassing the need to use the
``CACHE_MIDDLEWARE_ANONYMOUS_ONLY`` setting.

This implementation uses a secret delimiter that makes it safe against the
possibility of template code injection vulnerabilities, as it only passes any
given text through the template parser once. The phased blocks can also contain
cached context.

Basic Implementation
--------------------

django-phased contains a templatetag, ``phased``, which defines blocks that
are to be parsed during the second phase. A middleware class,
PhasedRenderMiddleware, processes the response to render the parts that were
skipped during the first rendering.

A special subclass of UpdateCacheMiddleware that drops the "Vary: Cookie"
header from response when it updates the cache is also included, which, if
used in place of the standard UpdateCacheMiddleware will prevent the cache
middleware from varying the cache key based on cookies, thus enabling caching
of pages in authenticated sessions.

Documentation lives in the ``docs`` directory as Sphinx documentation or
[in HTML rendered form here](http://codysoyland.com/projects/django-phased/documentation/).
