DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'phased.sqlite',
    },
}

INSTALLED_APPS = [
    'phased',
]

TEST_RUNNER = 'discover_runner.DiscoverRunner'

SECRET_KEY = '0'

PHASED_KEEP_CONTEXT = True

MIDDLEWARE_CLASSES = (
    'phased.middleware.PhasedRenderMiddleware',
    'phased.middleware.PatchedVaryUpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
)
