import unittest
from django.template import compile_string, Context

from phased.utils import second_pass_render, pickle_context, unpickle_context, flatten_context
from phased import settings

class TwoPhaseTestCase(unittest.TestCase):

    test_template = (
        "{% load phased_tags %}"
        "{% literal %}"
        "{% if 1 %}test{% endif %}"
        "{% endliteral %}"
        "{{ test_var }}"
    )
    def setUp(self):
        self.old_keep_context = settings.KEEP_CONTEXT
        settings.KEEP_CONTEXT = False

    def tearDown(self):
        settings.KEEP_CONTEXT = self.old_keep_context

    def test_literal(self):
        context = Context({'test_var': 'TEST'})
        first_render = compile_string(self.test_template, None).render(context)
        self.assertEqual(first_render, '%s{%% if 1 %%}test{%% endif %%}%sTEST' % (settings.LITERAL_DELIMITER, settings.LITERAL_DELIMITER))

    def test_second_pass(self):
        first_render = compile_string(self.test_template, None).render(Context({'test_var': 'TEST'}))
        second_render = second_pass_render(first_render, context_instance=Context())
        self.assertEqual(second_render, 'testTEST')


class StashedTwoPhaseTestCase(TwoPhaseTestCase):
    test_template = (
        "{% load phased_tags %}"
        "{% literal %}"
        "{% if 1 %}test{% endif %}"
        "{% if test_condition %}"
        "stashed"
        "{% endif %}"
        "{% endliteral %}"
        "{{ test_var }}"
        "{% literal %}"
        "{% if 1 %}test2{% endif %}"
        "{% if test_condition2 %}"
        "stashed"
        "{% endif %}"
        "{% endliteral %}"
    )
    def setUp(self):
        self.old_keep_context = settings.KEEP_CONTEXT
        settings.KEEP_CONTEXT = True

    def tearDown(self):
        settings.KEEP_CONTEXT = self.old_keep_context

    def test_unpickling(self):
        context = Context({'test_var': 'TEST'})
        pickled_context = pickle_context(context)
        unpickled_context = unpickle_context(pickled_context)
        # compare dicts attribute here, instead of instances
        self.assertEqual(flatten_context(context), unpickle_context(pickled_context))

    def test_literal(self):
        context = Context({'test_var': 'TEST'})
        pickled_context = pickle_context(context)
        first_render = compile_string(self.test_template, None).render(context)
        self.assertEqual(first_render, '%(delimiter)s%(pickled_context)s{%% if 1 %%}test{%% endif %%}{%% if test_condition %%}stashed{%% endif %%}%(delimiter)sTEST%(delimiter)s%(pickled_context)s{%% if 1 %%}test2{%% endif %%}{%% if test_condition2 %%}stashed{%% endif %%}%(delimiter)s' % dict(delimiter=settings.LITERAL_DELIMITER, pickled_context=pickled_context))

    def test_second_pass(self):
        context = Context({
            'test_var': 'TEST',
            'test_condition': True,
            'test_condition2': True,
        })
        first_render = compile_string(self.test_template, None).render(context)
        original_context = unpickle_context(first_render)
        second_render = second_pass_render(first_render, dictionary=original_context, context_instance=Context({'test_condition': False}))
        self.assertEqual(second_render, 'teststashedTESTtest2stashed')


# TODO: more tests for phased rendering and tests for middleware and header hacks
