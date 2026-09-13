from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0008_rename_bookings_bo_booking_created_idx_bookings_bo_booking_a35183_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='reschedule_reason',
            field=models.CharField(blank=True, help_text='Reason provided with the latest reschedule request', max_length=255),
        ),
        migrations.AlterField(
            model_name='bookinghistory',
            name='event',
            field=models.CharField(choices=[('status_change', 'Status Change'), ('reschedule_requested', 'Reschedule Requested'), ('reschedule_accepted', 'Reschedule Accepted'), ('reschedule_rejected', 'Reschedule Rejected'), ('reschedule_expired', 'Reschedule Expired'), ('cancellation', 'Cancellation'), ('payment_success', 'Payment Success'), ('ritual_started', 'Ritual Started'), ('ritual_completed', 'Ritual Completed'), ('code_generated', 'Verification Code Generated')], max_length=30),
        ),
    ]
