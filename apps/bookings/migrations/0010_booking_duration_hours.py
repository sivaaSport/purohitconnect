from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0009_reschedule_reason_and_expired_event'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='duration_hours',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Reserved ritual duration for this booking (copied from puja at booking time).',
                max_digits=4,
                null=True,
            ),
        ),
    ]
