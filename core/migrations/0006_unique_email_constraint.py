from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_userprofile_failed_otp_attempts_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE UNIQUE INDEX IF NOT EXISTS auth_user_email_unique ON auth_user (email);",
            reverse_sql="DROP INDEX IF EXISTS auth_user_email_unique;"
        )
    ]
