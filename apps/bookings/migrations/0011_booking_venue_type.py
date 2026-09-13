from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0010_booking_duration_hours'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='venue_type',
            field=models.CharField(
                blank=True,
                help_text='Where the ritual happens: home, temple, teerth, purohit, other.',
                max_length=20,
            ),
        ),
    ]
