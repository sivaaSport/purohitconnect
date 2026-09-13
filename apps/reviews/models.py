from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import TimeStampedModel
from apps.accounts.models import CustomUser
from apps.purohits.models import Purohit
from apps.bookings.models import Booking

class Review(TimeStampedModel):
    reviewer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reviews_written')
    purohit = models.ForeignKey(Purohit, on_delete=models.CASCADE, related_name='reviews')
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200)
    comment = models.TextField()
    
    # Sub-ratings specific to Purohits
    punctuality_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    knowledge_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    communication_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    
    is_verified = models.BooleanField(default=True)  # True because it's tied to a booking
    purohit_response = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update Purohit average rating
        reviews = self.purohit.reviews.all()
        if reviews.exists():
            avg = sum(r.rating for r in reviews) / reviews.count()
            self.purohit.avg_rating = round(avg, 2)
            self.purohit.total_reviews = reviews.count()
            self.purohit.save()

    def __str__(self):
        return f"Review for {self.purohit.name} by {self.reviewer.username} ({self.rating}/5)"
