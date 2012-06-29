from django.conf import settings
from django.utils.hashcompat import sha_constructor

if not hasattr(settings, 'PHASED_SECRET_DELIMITER'):
    settings.PHASED_SECRET_DELIMITER = sha_constructor(getattr(settings, 'SECRET_KEY', '')).hexdigest()

# quoting the sekrit delimiter to make sure Debug Toolbar doesn't render it
settings.PHASED_SECRET_DELIMITER = '"%s"' % settings.PHASED_SECRET_DELIMITER
