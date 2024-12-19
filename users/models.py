from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # username остаётся обязательным полем для AbstractUser

    class Meta:
        permissions = [
            ("view_all_clients", "Can view all clients"),
            ("view_all_newsletters", "Can view all newsletters"),
            ("block_user", "Can block users"),
            ("disable_newsletter", "Can disable newsletters"),
        ]

    def __str__(self):
        return self.email
