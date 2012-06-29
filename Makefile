export DJANGO_SETTINGS_MODULE=phased.test_settings

test:
	coverage run --branch --source=phased `which django-admin.py` test phased
	coverage report --omit=phased/test*
