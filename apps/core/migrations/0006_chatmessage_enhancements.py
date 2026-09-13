# Generated migration for ChatMessage enhancements

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_alter_notification_options'),
    ]

    operations = [
        # Add updated_at field to ChatMessage
        migrations.AddField(
            model_name='chatmessage',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        
        # Add database indexes for faster queries
        migrations.AddIndex(
            model_name='chatmessage',
            index=models.Index(fields=['booking', '-created_at'], name='core_chatmes_booking_created_idx'),
        ),
        migrations.AddIndex(
            model_name='chatmessage',
            index=models.Index(fields=['sender', '-created_at'], name='core_chatmes_sender_created_idx'),
        ),
    ]
