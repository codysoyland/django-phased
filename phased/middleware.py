from django.http import HttpResponse
from django.template.context import RequestContext
from phased.utils import second_pass_render, drop_vary_headers

class PhasedRenderMiddleware(object):
    def process_response(self, request, response):
        if not response['content-type'].startswith("text/html"):
            return response
        content = second_pass_render(content=response.content,
            context=RequestContext(request))
        return HttpResponse(content, status=response.status_code, content_type=response['content-type'])

class DropVaryCookieHeaderMiddleware(object):
    """
    If "Vary: Cookie" is set in the response object, Django's cache middleware
    will vary the cache key based on the value of the cookie. This middleware
    removes that header.
    """
    def process_response(self, request, response):
        drop_vary_headers(response, ['Cookie'])
        return response
