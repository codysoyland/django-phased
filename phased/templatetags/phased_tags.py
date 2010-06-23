from django.template import (Library, Node, resolve_variable,
    TOKEN_BLOCK, TOKEN_COMMENT, TOKEN_TEXT, TOKEN_VAR,
    TemplateSyntaxError, VariableDoesNotExist, Context)
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


class LiteralNode(Node):
    def __init__(self, content, var_names):
        self.var_names = var_names
        self.content = content

    def __repr__(self):
        return "<Literal Node: '%s'>" % smart_str(self.content[:25], 'ascii',
                errors='replace')

    def render(self, context):
        stash = {}
        for var_name in self.var_names:
            if var_name[0] in ('"', "'") and var_name[-1] == var_name[0]:
                var_name = var_name[1:-1]
            try:
                stash[var_name] = resolve_variable(var_name, context)
            except VariableDoesNotExist:
                raise TemplateSyntaxError(
                    '"literal" tag got an unknown variable: %r' % var_name)
        pickled = None
        if not stash and settings.KEEP_CONTEXT:
            pickled = pickle_context(context)
        elif stash:
            pickled = pickle_context(Context(stash))
        return '%(delimiter)s%(content)s%(pickled)s%(delimiter)s' % {
            'delimiter': settings.LITERAL_DELIMITER,
            'content': self.content,
            'pickled': pickled or '',
        }


def do_literal(parser, token):
    """
    Template tag to denote a template section to render a second time via
    a middleware.

    Usage::

        {% load phased_tags %}
        {% literal with [var1] [var2] .. %}
            .. some content to be rendered a second time ..
        {% endliteral %}

    You can pass it a list of context variable names to automatically
    save those variables for the second pass rendering of the template,
    e.g.::

        {% load phased_tags %}
        {% literal with comment_count object %}
            There are {{ comment_count }} comments for "{{ object }}".
        {% endliteral %}

    Alternatively you can also set the ``PHASED_KEEP_CONTEXT`` setting to
    ``True`` to automatically keep the whole context for each literal block.

    Note: Lazy objects such as messages and csrf tokens aren't kept.

    """
    literal = ''.join({
        TOKEN_BLOCK: '{%% %s %%}',
        TOKEN_VAR: '{{ %s }}',
        TOKEN_COMMENT: '{# %s #}',
        TOKEN_TEXT: '%s',
    }[token.token_type] % token.contents for token in parse(parser))
    tokens = token.contents.split()
    if len(tokens) > 1 and tokens[1] != 'with':
        raise TemplateSyntaxError(u"'%r' tag requires the second argument to be 'with'." % tokens[0])
        if len(tokens) == 2:
            raise TemplateSyntaxError(u"'%r' tag requires at least one context variable name." % tokens[0])
    return LiteralNode(literal, tokens[2:])

register.tag('literal', do_literal)
