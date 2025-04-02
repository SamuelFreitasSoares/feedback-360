from django.db import migrations, models, connections
from django.db.migrations.operations.fields import AddField
from django.db.utils import OperationalError

def column_exists(tablename, columnname):
    """Check if a column exists in a table"""
    conn = connections['default']
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT COUNT(*) FROM pragma_table_info('{tablename}') WHERE name='{columnname}'"
    )
    return cursor.fetchone()[0] > 0

class ConditionalAddField(AddField):
    """Only add the field if it doesn't already exist"""
    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        # Get the model class
        model = to_state.apps.get_model(app_label, self.model_name)
        # Get the actual table name
        tablename = model._meta.db_table
        # Only add the field if it doesn't exist
        if not column_exists(tablename, self.name):
            super().database_forwards(app_label, schema_editor, from_state, to_state)
        
    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        # Always try to remove the column when rolling back
        try:
            super().database_backwards(app_label, schema_editor, from_state, to_state)
        except OperationalError:
            # Column probably doesn't exist, which is fine
            pass

class Migration(migrations.Migration):
    dependencies = [
        ('project', '0005_add_reset_token_fields'),
    ]

    operations = [
        ConditionalAddField(
            model_name='admin',
            name='reset_token',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
