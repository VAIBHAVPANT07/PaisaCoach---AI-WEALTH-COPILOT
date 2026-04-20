from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_chatmessage'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='age',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
