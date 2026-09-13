from datetime import time

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('purohits', '0003_purohitmedia'),
    ]

    operations = [
        migrations.AddField(
            model_name='purohit',
            name='work_start',
            field=models.TimeField(
                default=time(6, 0),
                help_text='Earliest bookable start time on open days.',
            ),
        ),
        migrations.AddField(
            model_name='purohit',
            name='work_end',
            field=models.TimeField(
                default=time(21, 0),
                help_text='Latest bookable end time on open days.',
            ),
        ),
    ]
