from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('purohits', '0004_purohit_work_hours'),
    ]

    operations = [
        migrations.AddField(
            model_name='purohit',
            name='travel_note',
            field=models.CharField(
                blank=True,
                help_text='Optional travel beyond local neighborhoods, e.g. I travel to Gaya for Pind Daan.',
                max_length=240,
            ),
        ),
    ]
