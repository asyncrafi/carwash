#!/bin/bash
set -e

if [ -z "$DJANGO_SETTINGS_MODULE" ]; then
    export DJANGO_SETTINGS_MODULE=config.production
fi

echo "Running migrations..."
python manage.py migrate --noinput

echo "Creating superuser if not exists..."
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
email = "$DJANGO_SUPERUSER_EMAIL"
if email and not User.objects.filter(email=email).exists():
    User.objects.create_superuser(
        email=email,
        username=email,
        password="$DJANGO_SUPERUSER_PASSWORD",
        role="admin",
    )
    print(f"Superuser {email} created")
EOF

exec "$@"
