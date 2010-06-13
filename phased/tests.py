import unittest
from django.template import compile_string, Context
from phased.utils import second_pass_render
from phased import LITERAL_DELIMITER

class TwoPhaseTestCase(unittest.TestCase):
    test_template = (
        "{% load phased_tags %}"
        "{% literal %}"
        "{% if 1 %}test{% endif %}"
        "{% endliteral %}"
        "{{ test_var }}"
    )

    def test_literal(self):
        first_render = compile_string(self.test_template, None).render(Context({'test_var': 'TEST'}))
        self.assertEqual(first_render, '%s{%% if 1 %%}test{%% endif %%}%sTEST' % (LITERAL_DELIMITER, LITERAL_DELIMITER))

    def test_second_pass(self):
        first_render = compile_string(self.test_template, None).render(Context({'test_var': 'TEST'}))
        second_render = second_pass_render(first_render, Context())
        self.assertEqual(second_render, 'testTEST')

# TODO: more tests for phased rendering and tests for middleware and header hacks
