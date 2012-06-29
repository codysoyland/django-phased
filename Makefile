export DJANGO_SETTINGS_MODULE=phased.test_settings

test:
	flake8 phased --ignore=E501
	coverage run --branch --source=phased `which django-admin.py` test phased
	coverage report --omit=phased/test*
