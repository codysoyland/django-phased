from django.template import Library, TextNode,\
    TOKEN_BLOCK, TOKEN_COMMENT, TOKEN_TEXT, TOKEN_VAR
from django.utils.encoding import smart_str

from phased import settings
from phased.utils import pickle_context

register = Library()

def parse(parser):
    """
    Parse to the end of a literal block. This is different than Parser.parse()
    in that it does not generate Node objects; it simply yields tokens.
    """
    depth = 0
    while parser.tokens:
        token = parser.next_token()
        if token.token_type == TOKEN_BLOCK:
            if token.contents == 'literal':
                depth += 1
            elif token.contents == 'endliteral':
                depth -= 1
        if depth < 0:
            break
        yield token
    if not parser.tokens and depth >= 0:
        parser.unclosed_block_tag(('endliteral',))


class PhasedTextNode(TextNode):
    def __repr__(self):
        return "<Phased Text Node: '%s'>" % smart_str(self.s[:25], 'ascii',
                errors='replace')

    def render(self, context):
        if settings.KEEP_CONTEXT:
            self.s = '%s%s' % (pickle_context(context), self.s)
        return '%(delimiter)s%(content)s%(delimiter)s' % {
            'delimiter': settings.LITERAL_DELIMITER, 'content': self.s}


def do_literal(parser, token):
    """
    Template tag to denote a template section to render a second time.

    {% literal %}
        Hi, {{ user.username }}
    {% endliteral %}
    """
    literal = ''.join({
        TOKEN_BLOCK: '{%% %s %%}',
        TOKEN_VAR: '{{ %s }}',
        TOKEN_COMMENT: '{# %s #}',
        TOKEN_TEXT: '%s',
    }[token.token_type] % token.contents for token in parse(parser))
    return PhasedTextNode(literal)

register.tag('literal', do_literal)
