#!/bin/sh
cd decide/
cp local_settings.deploy.py local_settings.py
./manage.py createsuperuser --noinput
./manage.py collectstatic --noinput
./manage.py makemigrations
./manage.py migrate
gunicorn -w 5 decide.wsgi:application --timeout=500
echo "DEBUG: DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME}"
echo "DEBUG: DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD}"
