from django.template import Library, TextNode,\
    TOKEN_BLOCK, TOKEN_COMMENT, TOKEN_TEXT, TOKEN_VAR
from phased import LITERAL_DELIMITER

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

def do_literal(parser, token):
    literal = ''.join({
        TOKEN_BLOCK: '{%% %s %%}',
        TOKEN_VAR: '{{ %s }}',
        TOKEN_COMMENT: '{# %s #}',
        TOKEN_TEXT: '%s',
    }[token.token_type] % token.contents for token in parse(parser))
    return TextNode('%s%s%s' % (LITERAL_DELIMITER, literal, LITERAL_DELIMITER))

register.tag('literal', do_literal)
