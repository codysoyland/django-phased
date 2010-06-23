import re, base64
from django.template.context import BaseContext, RequestContext
from django.template import (Parser, Lexer, Token,
    TOKEN_TEXT, COMMENT_TAG_START, COMMENT_TAG_END, TemplateSyntaxError)
from django.utils.cache import cc_delim_re
from django.utils.functional import Promise, LazyObject
from django.http import HttpRequest
from django.contrib.messages.storage.base import BaseStorage

try:
    import cPickle as pickle
except ImportError:
    import pickle

from phased import settings

pickled_context_re = re.compile(r'.*%s stashed context: "(.*)" %s.*' % (COMMENT_TAG_START, COMMENT_TAG_END))
forbidden_classes = (Promise, LazyObject, HttpRequest, BaseStorage)

def second_pass_render(request, content):
    """
    Split on the literal delimiter and generate the token list by passing
    through text outside of literal blocks as single text tokens and tokenizing
    text inside the literal blocks. This ensures that nothing outside of the
    literal blocks is tokenized, thus eliminating the possibility of a template
    code injection vulnerability.
    """
    result = tokens = []
    for index, bit in enumerate(content.split(settings.LITERAL_DELIMITER)):
        if index % 2:
            tokens = Lexer(bit, None).tokenize()
        else:
            tokens.append(Token(TOKEN_TEXT, bit))
        context = RequestContext(request, unpickle_context(bit))
        result.append(Parser(tokens).parse().render(context))
    return "".join(result)

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

def flatten_context(context, remove_lazy=True):
    """
    Creates a dictionary from a Context instance by traversing
    its dicts list. Can remove unwanted subjects from the result,
    e.g. lazy objects.
    """
    flat_context = {}
    for context_dict in context.dicts:
        if remove_lazy:
            result = dict((k, v) for k, v in context_dict.iteritems() if not isinstance(v, forbidden_classes))
            flat_context.update(result)
        else:
            flat_context.update(context_dict)
    return flat_context

def unpickle_context(content, pattern=None):
    """
    Unpickle the context from the given content string or return None.
    """
    if pattern is None:
        pattern = pickled_context_re
    match = pattern.search(content)
    if match:
        return pickle.loads(base64.standard_b64decode(match.group(1)))
    return None

def pickle_context(context, template=None):
    """
    Pickle the given Context instance and do a few optimzations before.
    """
    if not isinstance(context, BaseContext):
        raise TemplateSyntaxError('Literal context is not a Context instance')
    pickled_context = pickle.dumps(flatten_context(context), protocol=pickle.HIGHEST_PROTOCOL)
    if template is None:
        template = '{# stashed context: "%s" #}'
    return template % base64.standard_b64encode(pickled_context)
