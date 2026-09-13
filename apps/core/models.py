from django.db import models

class TimeStampedModel(models.Model):
    """Abstract base model with created_at and updated_at fields."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class City(models.Model):
    """Major cities where services are available."""
    name = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return self.name
        
    class Meta:
        verbose_name_plural = "Cities"

class Area(models.Model):
    """Specific areas/neighborhoods within a city."""
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='areas')
    name = models.CharField(max_length=100)
    pincode = models.CharField(max_length=6)

    def __str__(self):
        return f"{self.name}, {self.city.name}"

class Language(models.Model):
    """Languages spoken by Purohits for rituals."""
    name = models.CharField(max_length=50) # e.g., Telugu, Hindi, Sanskrit
    native_name = models.CharField(max_length=50, blank=True) # e.g., తెలుగు, हिन्दी
    
    def __str__(self):
        return self.name

class ServiceRequest(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='service_requests', null=True, blank=True)
    ticket_id = models.CharField(max_length=20, unique=True)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, default='general') # booking, payment, technical, purohit_verification
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.ticket_id:
            import random, string
            self.ticket_id = 'SR-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_id} - {self.subject}"

class Notification(models.Model):
    CHANNELS = (
        ('in_app', 'In-App'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
    )
    
    DELIVERY_STATUS = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    )
    
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=100)
    message = models.TextField()
    link = models.CharField(max_length=200, blank=True)
    
    # Delivery tracking
    channel = models.CharField(max_length=20, choices=CHANNELS, default='in_app')
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS, default='pending')
    delivery_reference = models.CharField(max_length=200, blank=True)  # SID for SMS, MessageID for email, etc.
    delivery_error = models.TextField(blank=True)  # Error details if delivery fails
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Read status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def unread(self):
        return self.notifications.filter(is_read=False)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['delivery_status']),
            models.Index(fields=['channel', 'delivery_status']),
        ]

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title} ({self.channel})"

class ChatMessage(models.Model):
    """Internal chat messages between customer and purohit for a booking."""
    booking = models.ForeignKey('bookings.Booking', on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='sent_messages')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['booking', '-created_at']),
            models.Index(fields=['sender', '-created_at']),
        ]

    def __str__(self):
        return f"From {self.sender.username} for Booking {self.booking.booking_id}"
    
    @property
    def is_from_customer(self):
        """Check if message is from customer."""
        return self.sender == self.booking.customer
    
    @property
    def is_from_purohit(self):
        """Check if message is from purohit."""
        return self.sender == self.booking.purohit.profile.user
    
    def get_recipient(self):
        """Get the recipient of the message."""
        if self.is_from_customer:
            return self.booking.purohit.profile.user
        else:
            return self.booking.customer
    
    @classmethod
    def get_unread_count_for_user(cls, user):
        """Get count of unread messages for a user."""
        return cls.objects.filter(is_read=False).exclude(sender=user).count()
    
    @classmethod
    def mark_booking_messages_as_read(cls, booking, user):
        """Mark all messages in a booking as read for a specific user."""
        return cls.objects.filter(
            booking=booking,
            is_read=False
        ).exclude(sender=user).update(is_read=True)
