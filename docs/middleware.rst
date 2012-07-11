.. _ref-middleware:

==========
Middleware
==========

django-phased provides two helpful middleware classes,
``PhasedRenderMiddleware`` and ``PatchedVaryUpdateCacheMiddleware``.

.. autoclass:: phased.middleware.PhasedRenderMiddleware
    :members: process_response

.. autoclass:: phased.middleware.PatchedVaryUpdateCacheMiddleware
    :members: process_response
