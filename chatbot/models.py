from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Message(models.Model):
    text = models.TextField()
    is_bot = models.BooleanField(default=False)
    session_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.text[:50]

class AttachmentStatus(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    status = models.CharField(max_length=20)    
