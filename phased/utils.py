import re
import base64
from django.conf import settings
from django.http import HttpRequest
from django.template import (Parser, Lexer, Token, TOKEN_TEXT,
    COMMENT_TAG_START, COMMENT_TAG_END, TemplateSyntaxError)
from django.template.context import BaseContext, RequestContext, Context
from django.utils.cache import cc_delim_re
from django.utils.functional import Promise, LazyObject
from django.contrib.messages.storage.base import BaseStorage
from django.utils.encoding import smart_str


def get_pickle():
    try:
        import cPickle as pickle
    except ImportError:
        import pickle  # noqa
    return pickle

pickled_context_re = re.compile(r'.*%s stashed context: "(.*)" %s.*' % (COMMENT_TAG_START, COMMENT_TAG_END))
forbidden_classes = (Promise, LazyObject, HttpRequest, BaseStorage)


def second_pass_render(request, content):
    """
    Split on the secret delimiter and generate the token list by passing
    through text outside of phased blocks as single text tokens and tokenizing
    text inside the phased blocks. This ensures that nothing outside of the
    phased blocks is tokenized, thus eliminating the possibility of a template
    code injection vulnerability.
    """
    result = tokens = []
    for index, bit in enumerate(content.split(settings.PHASED_SECRET_DELIMITER)):
        if index % 2:
            tokens = Lexer(bit, None).tokenize()
        else:
            tokens.append(Token(TOKEN_TEXT, bit))

        context = RequestContext(request,
            restore_csrf_token(request, unpickle_context(bit)))
        rendered = Parser(tokens).parse().render(context)

        if settings.PHASED_SECRET_DELIMITER in rendered:
            rendered = second_pass_render(request, rendered)
        result.append(rendered)

    return "".join(result)


def restore_csrf_token(request, storage=None):
    """
    Given the request and a the context used during the second render phase,
    this wil check if there is a CSRF cookie and restores if needed, to
    counteract the way the CSRF framework invalidates the CSRF token after
    each request/response cycle.
    """
    if storage is None:
        storage = {}
    try:
        request.META["CSRF_COOKIE"] = request.COOKIES[settings.CSRF_COOKIE_NAME]
    except KeyError:
        csrf_token = storage.get('csrf_token', None)
        if csrf_token:
            request.META["CSRF_COOKIE"] = csrf_token
    return storage


def backup_csrf_token(context, storage=None):
    """
    Get the CSRF token and convert it to a string (since it's lazy)
    """
    if storage is None:
        storage = Context()
    storage['csrf_token'] = smart_str(context.get('csrf_token', 'NOTPROVIDED'))
    return storage


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

    def _flatten(context):
        if isinstance(context, dict):
            for k, v in context.items():
                if isinstance(context, BaseContext):
                    _flatten(context)
                else:
                    flat_context[k] = v
        elif isinstance(context, BaseContext):
            for context_dict in context.dicts:
                _flatten(context_dict)

    # traverse the passed context and update the dictionary accordingly
    _flatten(context)

    if remove_lazy:
        only_allowed = lambda dic: not isinstance(dic[1], forbidden_classes)
        return dict(filter(only_allowed, flat_context.iteritems()))
    return flat_context


def unpickle_context(content, pattern=None):
    """
    Unpickle the context from the given content string or return None.
    """
    pickle = get_pickle()
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
    pickle = get_pickle()
    if not isinstance(context, BaseContext):
        raise TemplateSyntaxError('Phased context is not a Context instance')
    pickled_context = pickle.dumps(flatten_context(context), protocol=pickle.HIGHEST_PROTOCOL)
    if template is None:
        template = '{# stashed context: "%s" #}'
    return template % base64.standard_b64encode(pickled_context)
