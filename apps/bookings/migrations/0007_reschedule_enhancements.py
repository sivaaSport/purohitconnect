# Generated migration for reschedule logic enhancements

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0006_booking_started_at'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        # Add reschedule timestamp fields
        migrations.AddField(
            model_name='booking',
            name='reschedule_requested_at',
            field=models.DateTimeField(blank=True, help_text='When purohit requested reschedule', null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='reschedule_accepted_at',
            field=models.DateTimeField(blank=True, help_text='When customer accepted reschedule', null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='reschedule_rejected_at',
            field=models.DateTimeField(blank=True, help_text='When customer rejected reschedule', null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='reschedule_count',
            field=models.IntegerField(default=0, help_text='Number of times this booking was rescheduled'),
        ),
        
        # Update reschedule_status choices
        migrations.AlterField(
            model_name='booking',
            name='reschedule_status',
            field=models.CharField(
                choices=[('none', 'None'), ('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')],
                default='none',
                max_length=20
            ),
        ),
        
        # Update BookingHistory model to add new fields and change event field
        migrations.AddField(
            model_name='bookinghistory',
            name='old_value',
            field=models.CharField(blank=True, help_text='Previous value for field changes', max_length=100),
        ),
        migrations.AddField(
            model_name='bookinghistory',
            name='new_value',
            field=models.CharField(blank=True, help_text='New value for field changes', max_length=100),
        ),
        
        # Change event field to use choices
        migrations.AlterField(
            model_name='bookinghistory',
            name='event',
            field=models.CharField(
                choices=[
                    ('status_change', 'Status Change'),
                    ('reschedule_requested', 'Reschedule Requested'),
                    ('reschedule_accepted', 'Reschedule Accepted'),
                    ('reschedule_rejected', 'Reschedule Rejected'),
                    ('cancellation', 'Cancellation'),
                    ('payment_success', 'Payment Success'),
                    ('ritual_started', 'Ritual Started'),
                    ('ritual_completed', 'Ritual Completed'),
                    ('code_generated', 'Verification Code Generated'),
                ],
                max_length=30
            ),
        ),
        
        # Reorder BookingHistory to show latest first
        migrations.AlterModelOptions(
            name='bookinghistory',
            options={
                'ordering': ['-created_at'],
                'verbose_name_plural': 'Booking Histories',
            },
        ),
        
        # Add index for fast queries
        migrations.AddIndex(
            model_name='bookinghistory',
            index=models.Index(fields=['booking', '-created_at'], name='bookings_bo_booking_created_idx'),
        ),
    ]
