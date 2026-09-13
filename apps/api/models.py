import secrets
from django.conf import settings
from django.db import models
from django.utils import timezone


class MobileAuthToken(models.Model):
    """Bearer token for the Flutter / API client."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mobile_tokens',
    )
    key = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True)
    user_agent = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user_id} · {self.key[:8]}…'

    @classmethod
    def issue(cls, user, user_agent=''):
        token = cls.objects.create(
            user=user,
            key=secrets.token_hex(32),
            user_agent=(user_agent or '')[:255],
        )
        return token

    def touch(self):
        self.last_used_at = timezone.now()
        self.save(update_fields=['last_used_at'])
