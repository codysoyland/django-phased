import pickle
import re

from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.middleware.cache import FetchFromCacheMiddleware, UpdateCacheMiddleware
from django.utils.cache import patch_vary_headers
from django.template import (compile_string, Context,
    TemplateSyntaxError, RequestContext)
from django.test.client import RequestFactory
from django.test import TestCase

try:
    from override_settings import override_settings
except ImportError:
    from django.test.utils import override_settings  # noqa

from phased.utils import (second_pass_render, pickle_context,
    unpickle_context, flatten_context, drop_vary_headers, backup_csrf_token)
from phased.middleware import (PhasedRenderMiddleware,
    PatchedVaryUpdateCacheMiddleware)
from phased import utils


class PhasedTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        utils.get_pickle = lambda: pickle
        super(PhasedTestCase, self).setUp()


class TwoPhaseTestCase(PhasedTestCase):
    test_template = (
        "{% load phased_tags %}"
        "{% phased %}"
        "{% if 1 %}test{% endif %}"
        "{% endphased %}"
        "{{ test_var }}"
    )

    def test_phased(self):
        context = Context({'test_var': 'TEST'})
        first_render = compile_string(self.test_template, None).render(context)
        original_context = unpickle_context(first_render)
        self.assertNotEqual(flatten_context(context), original_context)
        pickled_context = pickle_context(Context({'csrf_token': 'NOTPROVIDED'}))
        self.assertEqual(first_render, '%(delimiter)s{%% if 1 %%}test{%% endif %%}%(pickled_context)s%(delimiter)sTEST' %
            dict(delimiter=settings.PHASED_SECRET_DELIMITER, pickled_context=pickled_context))

    def test_second_pass(self):
        request = self.factory.get('/')
        first_render = compile_string(self.test_template, None).render(Context({'test_var': 'TEST'}))
        second_render = second_pass_render(request, first_render)
        self.assertEqual(second_render, 'testTEST')

TwoPhaseTestCase = override_settings(PHASED_KEEP_CONTEXT=False)(TwoPhaseTestCase)


class FancyTwoPhaseTestCase(TwoPhaseTestCase):
    def test_phased(self):
        context = Context({'test_var': 'TEST'})
        first_render = compile_string(self.test_template, None).render(context)
        self.assertEqual(first_render, 'fancydelimiter{%% if 1 %%}test{%% endif %%}%sfancydelimiterTEST' % pickle_context(backup_csrf_token(context)))

    def test_second_pass(self):
        request = self.factory.get('/')
        first_render = compile_string(self.test_template, None).render(Context({'test_var': 'TEST'}))
        second_render = second_pass_render(request, first_render)
        self.assertEqual(second_render, 'testTEST')

FancyTwoPhaseTestCase = override_settings(PHASED_SECRET_DELIMITER="fancydelimiter")(FancyTwoPhaseTestCase)


class NestedTwoPhaseTestCase(TwoPhaseTestCase):
    test_template = (
        "{% load phased_tags %}"
        "{% phased %}"
        "{% load phased_tags %}"
        "{% phased %}"
        "{% if 1 %}first{% endif %}"
        "{% endphased %}"
        "{% if 1 %}second{% endif %}"
        "{% endphased %}"
        "{{ test_var }}"
    )

    def test_phased(self):
        context = Context({'test_var': 'TEST'})
        first_render = compile_string(self.test_template, None).render(context)
        self.assertEqual(first_render, '%(delimiter)s{%% load phased_tags %%}{%% phased %%}{%% if 1 %%}first{%% endif %%}{%% endphased %%}{%% if 1 %%}second{%% endif %%}%(pickled_context)s%(delimiter)sTEST' %
            dict(delimiter=settings.PHASED_SECRET_DELIMITER, pickled_context=pickle_context(backup_csrf_token(context))))

    def test_second_pass(self):
        request = self.factory.get('/')
        first_render = compile_string(self.test_template, None).render(Context({'test_var': 'TEST'}))
        second_render = second_pass_render(request, first_render)
        self.assertEqual(second_render, 'firstsecondTEST')


class StashedTestCase(TwoPhaseTestCase):
    test_template = (
        "{% load phased_tags %}"
        "{% phased %}"
        "{% if 1 %}test{% endif %}"
        "{% if test_condition %}"
        "stashed"
        "{% endif %}"
        "{% endphased %}"
        "{{ test_var }}"
        "{% phased %}"
        "{% if 1 %}test2{% endif %}"
        "{% if test_condition2 %}"
        "stashed"
        "{% endif %}"
        "{% endphased %}"
    )

    @override_settings(PHASED_KEEP_CONTEXT=True)
    def test_phased(self):
        context = Context({'test_var': 'TEST'})
        pickled_context = '{# stashed context: "gAJ9cQAoVQpjc3JmX3Rva2VucQFVC05PVFBST1ZJREVEcQJVCHRlc3RfdmFycQNVBFRFU1RxBHUu" #}'
        first_render = compile_string(self.test_template, None).render(context)
        self.assertEqual(first_render, '%(delimiter)s{%% if 1 %%}test{%% endif %%}{%% if test_condition %%}stashed{%% endif %%}%(pickled_context)s%(delimiter)sTEST%(delimiter)s{%% if 1 %%}test2{%% endif %%}{%% if test_condition2 %%}stashed{%% endif %%}%(pickled_context)s%(delimiter)s' %
            dict(delimiter=settings.PHASED_SECRET_DELIMITER, pickled_context=pickled_context))

    @override_settings(PHASED_KEEP_CONTEXT=True)
    def test_second_pass(self):
        request = self.factory.get('/')
        context = Context({
            'test_var': 'TEST',
            'test_condition': True,
            'test_condition2': True,
        })
        first_render = compile_string(self.test_template, None).render(context)
        second_render = second_pass_render(request, first_render)
        self.assertEqual(second_render, 'teststashedTESTtest2stashed')


class PickyStashedTestCase(StashedTestCase):
    test_template = (
        '{% load phased_tags %}'
        '{% phased with "test_var" test_condition %}'
        '{% if 1 %}test{% endif %}'
        '{% if test_condition %}'
        'stashed'
        '{% endif %}'
        '{% endphased %}'
        '{{ test_var }}'
    )

    def test_phased(self):
        context = Context({'test_var': 'TEST'})
        self.assertRaises(TemplateSyntaxError, compile_string(self.test_template, None).render, context)
        context = Context({
            'test_var': 'TEST',
            'test_condition': True,
        })
        first_render = compile_string(self.test_template, None).render(context)
        pickled_context = '{# stashed context: "gAJ9cQAoVQ50ZXN0X2NvbmRpdGlvbnEBiFUKY3NyZl90b2tlbnECVQtOT1RQUk9WSURFRHEDVQh0ZXN0X3ZhcnEEVQRURVNUcQV1Lg==" #}'
        self.assertEqual(first_render, '%(delimiter)s{%% if 1 %%}test{%% endif %%}{%% if test_condition %%}stashed{%% endif %%}%(pickled_context)s%(delimiter)sTEST' %
            dict(delimiter=settings.PHASED_SECRET_DELIMITER, pickled_context=pickled_context))

    def test_second_pass(self):
        request = self.factory.get('/')
        context = Context({
            'test_var': 'TEST',
            'test_var2': 'TEST2',
            'test_condition': True,
        })
        first_render = compile_string(self.test_template, None).render(context)
        original_context = unpickle_context(first_render)
        self.assertEqual(original_context.get('test_var'), 'TEST')
        second_render = second_pass_render(request, first_render)
        self.assertEqual(second_render, 'teststashedTEST')


class UtilsTestCase(PhasedTestCase):
    def test_flatten(self):
        context = Context({'test_var': 'TEST'})
        context.update({'test_var': 'TEST2', 'abc': 'def'})
        self.assertEqual(flatten_context(context), {'test_var': 'TEST2', 'abc': 'def'})

    def test_flatten_nested(self):
        context = Context({'test_var': 'TEST'})
        context.update(Context({'test_var': 'TEST2', 'abc': 'def'}))
        self.assertEqual(flatten_context(context), {'test_var': 'TEST2', 'abc': 'def'})

    def test_pickling(self):
        self.assertRaises(TemplateSyntaxError, pickle_context, {})
        self.assertEqual(pickle_context(Context()), '{# stashed context: "gAJ9cQAu" #}')
        context = Context({'test_var': 'TEST'})
        template = '<!-- better be careful %s yikes -->'
        self.assertEqual(pickle_context(context), '{# stashed context: "gAJ9cQBVCHRlc3RfdmFycQFVBFRFU1RxAnMu" #}')
        self.assertEqual(pickle_context(context, template), '<!-- better be careful gAJ9cQBVCHRlc3RfdmFycQFVBFRFU1RxAnMu yikes -->')

    def test_unpickling(self):
        self.assertEqual(unpickle_context(pickle_context(Context())), flatten_context(Context()))
        context = Context({'test_var': 'TEST'})
        pickled_context = pickle_context(context)
        unpickled_context = unpickle_context(pickled_context)
        self.assertEqual(flatten_context(context), unpickled_context)

    def test_unpickling_with_template_and_pattern(self):
        context = Context({'test_var': 'TEST'})
        template = '<!-- better be careful %s yikes -->'
        pattern = re.compile(r'.*<!-- better be careful (.*) yikes -->.*')
        pickled_context = pickle_context(context, template)
        unpickled_context = unpickle_context(pickled_context, pattern)
        self.assertEqual(flatten_context(context), unpickled_context)


class PhasedRenderMiddlewareTestCase(PhasedTestCase):
    template = (
        'before '
        '%(delimiter)s '
        'inside{# a comment #} '
        '%(delimiter)s '
        'after'
    )

    def test_basic(self):
        request = self.factory.get('/')
        response = HttpResponse(self.template %
            dict(delimiter=settings.PHASED_SECRET_DELIMITER))

        response = PhasedRenderMiddleware().process_response(request, response)

        self.assertEqual(response.content, 'before  inside  after')

    def test_not_html(self):
        request = self.factory.get('/')
        applied_delimiter = self.template % dict(delimiter=settings.PHASED_SECRET_DELIMITER)
        response = HttpResponse(applied_delimiter, mimetype='application/json')

        response = PhasedRenderMiddleware().process_response(request, response)
        self.assertEqual(response.content, applied_delimiter)


class PatchedVaryUpdateCacheMiddlewareTestCase(PhasedTestCase):

    def setUp(self):
        super(PatchedVaryUpdateCacheMiddlewareTestCase, self).setUp()
        cache.clear()

    def test_no_vary(self):
        """
        Ensure basic caching works.
        """
        request = self.factory.get('/test/no-vary')
        response = HttpResponse()

        SessionMiddleware().process_request(request)
        AuthenticationMiddleware().process_request(request)

        cache_hit = FetchFromCacheMiddleware().process_request(request)
        self.assertEqual(cache_hit, None)

        response = PatchedVaryUpdateCacheMiddleware().process_response(request, response)
        cache_hit = FetchFromCacheMiddleware().process_request(request)

        self.assertTrue(isinstance(cache_hit, HttpResponse))

    def test_vary(self):
        """
        Ensure caching works even when cookies are present and `Vary: Cookie` is on.
        """
        request = self.factory.get('/test/vary')
        request.COOKIES = {'test': 'foo'}
        request.META['HTTP_COOKIE'] = 'test=foo'

        response = HttpResponse()
        patch_vary_headers(response, ['Cookie'])
        response.set_cookie('test', 'foo')

        SessionMiddleware().process_request(request)
        AuthenticationMiddleware().process_request(request)

        cache_hit = FetchFromCacheMiddleware().process_request(request)
        self.assertTrue(cache_hit is None)

        response = PatchedVaryUpdateCacheMiddleware().process_response(request, response)
        cache_hit = FetchFromCacheMiddleware().process_request(request)

        self.assertTrue(isinstance(cache_hit, HttpResponse))

        new_request = self.factory.get('/test/vary')
        # note: not using cookies here. this demonstrates that cookies don't
        # affect the cache key
        cache_hit = FetchFromCacheMiddleware().process_request(new_request)
        self.assertTrue(isinstance(cache_hit, HttpResponse))

    def test_vary_with_original_update_cache_middleware(self):
        """
        Mainly to demonstrate the need to remove the Vary: Cookie header
        during caching. Same basic test as test_vary() but with django's
        UpdateCacheMiddleware instead of PatchedVaryUpdateCacheMiddleware.
        This does not get a cache hit if the cookies are not the same.
        """
        request = self.factory.get('/')
        request.method = 'GET'
        request.COOKIES = {'test': 'foo'}
        request.META['HTTP_COOKIE'] = 'test=foo'

        response = HttpResponse()
        patch_vary_headers(response, ['Cookie'])
        response.set_cookie('test', 'foo')

        SessionMiddleware().process_request(request)
        AuthenticationMiddleware().process_request(request)

        cache_hit = FetchFromCacheMiddleware().process_request(request)
        self.assertEqual(cache_hit, None)

        response = UpdateCacheMiddleware().process_response(request, response)
        cache_hit = FetchFromCacheMiddleware().process_request(request)

        self.assertTrue(isinstance(cache_hit, HttpResponse))

        new_request = self.factory.get('/')
        new_request.method = 'GET'
        # note: not using cookies here. this demonstrates that cookies don't
        # affect the cache key
        cache_hit = FetchFromCacheMiddleware().process_request(new_request)
        self.assertEqual(cache_hit, None)

    def test_drop_vary_headers(self):
        response = HttpResponse()

        self.assertFalse(response.has_header('Vary'))
        patch_vary_headers(response, ['Cookie'])
        self.assertTrue(response.has_header('Vary'))
        self.assertEqual(response['Vary'], 'Cookie')
        patch_vary_headers(response, ['Nomnomnom'])
        self.assertEqual(response['Vary'], 'Cookie, Nomnomnom')
        drop_vary_headers(response, ['Cookie'])
        self.assertEqual(response['Vary'], 'Nomnomnom')
        drop_vary_headers(response, ['Nomnomnom'])
        self.assertFalse(response.has_header('Vary'))


class PhasedCacheTemplateTagTest(PhasedTestCase):
    test_template = (
        "{% load phased_tags %}"
        "OtherPart"
        "{% phasedcache 10000 phased_test %}"
        "{{ test_var }}"
        "{% phased %}"
        "{{ request.path }}"
        "{% endphased %}"
        "{% endphasedcache %}"
        "TEST"
    )

    def setUp(self):
        super(PhasedCacheTemplateTagTest, self).setUp()
        cache.clear()

    def test_phasedcache(self):
        self.assertEqual(len(cache._cache.keys()), 0)
        request = self.factory.get('/')
        context = RequestContext(request, {'test_var': 'Testing'})
        rendering = compile_string(self.test_template, None).render(context)
        self.assertEqual(rendering, 'OtherPartTesting/TEST')
        self.assertEqual(len(cache._cache.keys()), 1)
        cached_value = cache.get('template.cache.phased_test.d41d8cd98f00b204e9800998ecf8427e')
        self.assertIsNotNone(cached_value)
        self.assertTrue(cached_value.startswith('Testing'))
        request = self.factory.get('/path/')
        # Do not make test_var available, should be in cache
        context = RequestContext(request)
        rendering = compile_string(self.test_template, None).render(context)
        self.assertEqual(rendering, 'OtherPartTesting/path/TEST')
