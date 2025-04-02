from django.db import migrations

def create_admin_user(apps, schema_editor):
    Admin = apps.get_model('project', 'Admin')
    
    # Check if any admin already exists
    if Admin.objects.count() == 0:
        Admin.objects.create(
            nomeAdmin='Admin',
            emailAdmin='admin@feedback360.com',
            senhaAdmin='admin123'
        )

def reverse_func(apps, schema_editor):
    Admin = apps.get_model('project', 'Admin')
    Admin.objects.filter(emailAdmin='admin@feedback360.com').delete()

class Migration(migrations.Migration):
    dependencies = [
        ('project', '0003_admin'),
    ]

    operations = [
        migrations.RunPython(create_admin_user, reverse_func),
    ]
