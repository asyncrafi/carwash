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
phone = "$DJANGO_SUPERUSER_PHONE"
if phone and not User.objects.filter(phone=phone).exists():
    User.objects.create_superuser(
        phone=phone,
        username=phone,
        password="$DJANGO_SUPERUSER_PASSWORD",
        role="admin",
    )
    print(f"Superuser {phone} created")
EOF

exec "$@"
