from django.conf import settings

def generate_secret_delimiter():
    try:
        from hashlib import sha1
    except ImportError:
        from sha import sha as sha1
    return sha1(getattr(settings, 'SECRET_KEY', '')).hexdigest()

LITERAL_DELIMITER = getattr(settings, 'LITERAL_DELIMITER', generate_secret_delimiter())
