from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0003_user_confirmed_email_user_regular_user_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='birthday',
            field=models.DateField(blank=True, default=None, null=True),
        ),
    ]
