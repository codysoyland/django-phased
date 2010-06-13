django-phased
=============

A simple two-phase template rendering application useful for caching of authenticated requests.

django-phased contains a templatetag, ``literal``, which defines blocks that
are to be parsed during the second phase. A middleware class,
PhasedRenderMiddleware, processes the response to render the parts that were
skipped during the first rendering.

A special middleware for dropping the "Vary: Cookie" headers from response is
also included, which, if placed after FetchFromCacheMiddleware, will prevent
the cache middleware from varying the cache key based on cookies, thus enabling
caching of pages in authenticated sessions.

**More documentation coming soon. For now, please look at the example application.**
