from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('project', '0004_create_default_admin'),
    ]

    operations = [
        migrations.AddField(
            model_name='aluno',
            name='reset_token',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='professor',
            name='reset_token',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='coordenador',
            name='reset_token',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='admin',
            name='reset_token',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
