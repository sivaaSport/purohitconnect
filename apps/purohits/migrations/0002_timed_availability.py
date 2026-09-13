# Generated manually for timed availability blocks

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('purohits', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='purohitavailability',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='purohitavailability',
            name='start_time',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='purohitavailability',
            name='end_time',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='purohitavailability',
            name='is_available',
            field=models.BooleanField(default=False, help_text='False means blocked/unavailable'),
        ),
        migrations.AlterModelOptions(
            name='purohitavailability',
            options={'ordering': ['date', 'start_time'], 'verbose_name_plural': 'Purohit Availabilities'},
        ),
    ]
