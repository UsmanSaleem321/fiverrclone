from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    is_seller = models.BooleanField(default=False)

class Gig(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    seller = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="gigs")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
