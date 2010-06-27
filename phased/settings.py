from django.conf import settings
from django.utils.hashcompat import sha_constructor

def generate_secret_delimiter():
    return sha_constructor(getattr(settings, 'SECRET_KEY', '')).hexdigest()

SECRET_DELIMITER = getattr(settings, 'PHASED_SECRET_DELIMITER', generate_secret_delimiter())

KEEP_CONTEXT = getattr(settings, 'PHASED_KEEP_CONTEXT', False)
