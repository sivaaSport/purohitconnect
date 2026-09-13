from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pujas', '0002_package_duration_and_buffer'),
    ]

    operations = [
        migrations.AddField(
            model_name='puja',
            name='typical_venues',
            field=models.CharField(
                blank=True,
                default='home',
                help_text='Comma-separated venue codes: home, temple, teerth, purohit, other.',
                max_length=80,
            ),
        ),
        migrations.AddField(
            model_name='purohitpujapackage',
            name='venues',
            field=models.CharField(
                blank=True,
                help_text='Where this purohit performs the ritual. Empty falls back to catalog typical venues.',
                max_length=80,
            ),
        ),
        migrations.AddField(
            model_name='purohitpujapackage',
            name='venue_notes',
            field=models.CharField(
                blank=True,
                help_text='Optional place note, e.g. Trimbakeshwar only or I travel to Gaya.',
                max_length=240,
            ),
        ),
    ]
