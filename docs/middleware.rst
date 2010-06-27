.. _ref-middleware:

==========
Middleware
==========

django-phased provides two helpful middleware classes, `PhasedRenderMiddleware`
and `PatchedVaryUpdateCacheMiddleware`.

PhasedRenderMiddleware
======================

.. autoclass:: phased.middleware.PhasedRenderMiddleware
    :members: process_response

PatchedVaryUpdateCacheMiddleware
================================

.. autoclass:: phased.middleware.PatchedVaryUpdateCacheMiddleware
    :members: process_response
