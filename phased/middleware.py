from django.middleware.cache import UpdateCacheMiddleware
from django.template.context import RequestContext
from django.utils.cache import patch_vary_headers
from phased import settings
from phased.utils import second_pass_render, drop_vary_headers, unpickle_context


class PhasedRenderMiddleware(object):
    def process_response(self, request, response):
        if not response['content-type'].startswith("text/html"):
            return response
        context = None
        if settings.KEEP_CONTEXT:
            context = unpickle_context(response.content)
        response.content = second_pass_render(response.content, context,
            context_instance=RequestContext(request))
        response['Content-Length'] = str(len(response.content))
        return response


class PatchedVaryUpdateCacheMiddleware(UpdateCacheMiddleware):
    def process_response(self, request, response):
        # If "Vary: Cookie" is set in the response object, Django's cache
        # middleware will vary the cache key based on the value of the cookie.
        # This removes that header.
        drop_vary_headers(response, ['Cookie'])

        response = super(PatchedVaryUpdateCacheMiddleware, self).process_response(request, response)

        # This re-adds the header that was dropped above, so browsers still
        # know to vary on cookies.
        patch_vary_headers(response, ['Cookie'])

        return response
