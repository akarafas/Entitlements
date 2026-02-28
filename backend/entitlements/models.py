from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    ROLE_SUPPORT = 'support'
    ROLE_DEVELOPER = 'developer'
    ROLE_CHOICES = [
        (ROLE_SUPPORT, 'Support'),
        (ROLE_DEVELOPER, 'Developer'),
    ]

    email = models.EmailField(unique=True)
    address = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_DEVELOPER)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']


class Product(models.Model):
    ACCESS_DIGITAL = 'digital'
    ACCESS_PRINT = 'print'
    ACCESS_PREMIUM = 'premium'
    ACCESS_CHOICES = [
        (ACCESS_DIGITAL, 'Digital'),
        (ACCESS_PRINT, 'Print'),
        (ACCESS_PREMIUM, 'Premium'),
    ]

    name = models.CharField(max_length=100, unique=True)
    access_type = models.CharField(max_length=20, choices=ACCESS_CHOICES)

    def __str__(self):
        return f'{self.name} ({self.access_type})'


class Entitlement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='entitlements')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='entitlements')
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    is_revoked = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'product', 'start_date')

    @property
    def is_expired(self):
        return self.end_date < timezone.now().date()

    @property
    def is_active(self):
        return not self.is_revoked and not self.is_expired


class PurchaseHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchase_history')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    date_start = models.DateField()
    date_end = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)


class AccessHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='access_history')
    page = models.CharField(max_length=200)
    accessed_at = models.DateTimeField(auto_now_add=True)


def calculate_end_date(start_date, length_days):
    return start_date + timedelta(days=length_days)
