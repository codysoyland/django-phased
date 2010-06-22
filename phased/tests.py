import re, unittest
from django.template import compile_string, Context, TemplateSyntaxError

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

class FancyTwoPhaseTestCase(TwoPhaseTestCase):
    def setUp(self):
        self.old_literal_delimiter = settings.LITERAL_DELIMITER
        settings.LITERAL_DELIMITER = "fancydelimiter"
        super(FancyTwoPhaseTestCase, self).setUp()

    def tearDown(self):
        settings.LITERAL_DELIMITER = self.old_literal_delimiter
        super(FancyTwoPhaseTestCase, self).tearDown()

    def test_literal(self):
        context = Context({'test_var': 'TEST'})
        first_render = compile_string(self.test_template, None).render(context)
        self.assertEqual(first_render, 'fancydelimiter{% if 1 %}test{% endif %}fancydelimiterTEST')

    def test_second_pass(self):
        first_render = compile_string(self.test_template, None).render(Context({'test_var': 'TEST'}))
        second_render = second_pass_render(first_render, context_instance=Context())
        self.assertEqual(second_render, 'testTEST')



class StashedTestCase(TwoPhaseTestCase):
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
        super(StashedTestCase, self).setUp()
        settings.KEEP_CONTEXT = True

    def test_literal(self):
        context = Context({'test_var': 'TEST'})
        pickled_context = pickle_context(context)
        first_render = compile_string(self.test_template, None).render(context)
        self.assertEqual(first_render, '%(delimiter)s{%% if 1 %%}test{%% endif %%}{%% if test_condition %%}stashed{%% endif %%}%(pickled_context)s%(delimiter)sTEST%(delimiter)s{%% if 1 %%}test2{%% endif %%}{%% if test_condition2 %%}stashed{%% endif %%}%(pickled_context)s%(delimiter)s' % dict(delimiter=settings.LITERAL_DELIMITER, pickled_context=pickled_context))

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


class PickyStashedTestCase(StashedTestCase):
    test_template = (
        '{% load phased_tags %}'
        '{% literal with "test_var" test_condition %}'
        '{% if 1 %}test{% endif %}'
        '{% if test_condition %}'
        'stashed'
        '{% endif %}'
        '{% endliteral %}'
        '{{ test_var }}'
    )
    def test_literal(self):
        context = Context({'test_var': 'TEST'})
        self.assertRaises(TemplateSyntaxError,
            compile_string(self.test_template, None).render, context)
        context = Context({
            'test_var': 'TEST',
            'test_condition': True,
        })
        pickled_context = pickle_context(context)
        first_render = compile_string(self.test_template, None).render(context)
        self.assertEqual(first_render, '%(delimiter)s{%% if 1 %%}test{%% endif %%}{%% if test_condition %%}stashed{%% endif %%}%(pickled_context)s%(delimiter)sTEST' % dict(delimiter=settings.LITERAL_DELIMITER, pickled_context=pickled_context))

    def test_second_pass(self):
        context = Context({
            'test_var': 'TEST',
            'test_var2': 'TEST2',
            'test_condition': True,
        })
        first_render = compile_string(self.test_template, None).render(context)
        original_context = unpickle_context(first_render)
        self.assertEqual(original_context.get('test_var'), 'TEST')
        second_render = second_pass_render(first_render, dictionary=original_context)
        self.assertEqual(second_render, 'teststashedTEST')


class UtilsTestCase(unittest.TestCase):

    def test_flatten(self):
        context = Context({'test_var': 'TEST'})
        context.update({'test_var': 'TEST2', 'abc': 'def'})
        self.assertEqual(flatten_context(context), {'test_var': 'TEST2', 'abc': 'def'})

    def test_pickling(self):
        self.assertRaises(TemplateSyntaxError, pickle_context, {})
        self.assertEqual(pickle_context(Context()), '{# stashed context: "gAJ9Lg==" #}')
        context = Context({'test_var': 'TEST'})
        template = '<!-- better be careful %s yikes -->'
        self.assertEqual(pickle_context(context), '{# stashed context: "gAJ9cQFVCHRlc3RfdmFycQJVBFRFU1RxA3Mu" #}')
        self.assertEqual(pickle_context(context, template), '<!-- better be careful gAJ9cQFVCHRlc3RfdmFycQJVBFRFU1RxA3Mu yikes -->')

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


# TODO: more tests for phased rendering and tests for middleware and header hacks
