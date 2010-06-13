from django.template import Parser, Lexer, Token, TOKEN_TEXT
from phased import LITERAL_DELIMITER
from django.utils.cache import cc_delim_re

def second_pass_render(content, context):
    """
    Split on the literal delimiter and generate the token list by passing
    through text outside of literal blocks as single text tokens and tokenizing
    text inside the literal blocks. This ensures that nothing outside of the
    literal blocks is tokenized, thus eliminating the possibility of a template
    code injection vulnerability.
    """
    tokens = []
    for index, bit in enumerate(content.split(LITERAL_DELIMITER)):
        if index % 2:
            tokens += Lexer(bit, None).tokenize()
        else:
            tokens.append(Token(TOKEN_TEXT, bit))
    return Parser(tokens).parse().render(context)

def drop_vary_headers(response, headers_to_drop):
    """
    Remove an item from the "Vary" header of an ``HttpResponse`` object.
    If no items remain, delete the "Vary" header.
    This does the opposite effect of django.utils.cache.patch_vary_headers.
    """
    if response.has_header('Vary'):
        vary_headers = cc_delim_re.split(response['Vary'])
    else:
        vary_headers = []

    headers_to_drop = [header.lower() for header in headers_to_drop]

    updated_vary_headers = []
    for header in vary_headers:
        if len(header):
            if header.lower() not in headers_to_drop:
                updated_vary_headers.append(header)

    if len(updated_vary_headers):
        response['Vary'] = ', '.join(updated_vary_headers)
    else:
        del response['Vary']
