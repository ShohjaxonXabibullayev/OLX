from django.db import migrations
from django.contrib.auth.hashers import make_password

def create_superuser(apps, schema_editor):
    User = apps.get_model('users', 'User')
    if not User.objects.filter(email='admin@example.com').exists():
        User.objects.create(
            email='admin@example.com',
            full_name='Admin',
            password=make_password('adminpassword123'),
            is_superuser=True,
            is_staff=True,
            is_active=True,
            profile_type='INDIVIDUAL'
        )

def remove_superuser(apps, schema_editor):
    User = apps.get_model('users', 'User')
    User.objects.filter(email='admin@example.com').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_superuser, remove_superuser),
    ]
