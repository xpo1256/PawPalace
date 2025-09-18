from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from PIL import Image
import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
import json

User = get_user_model()


class Dog(models.Model):
    """Dog model representing dogs for sale"""
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('sold', 'Sold'),
        ('pending', 'Pending'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=100)
    breed = models.CharField(max_length=100)
    age = models.PositiveIntegerField(help_text="Age in months")
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Details
    description = models.TextField()
    location = models.CharField(max_length=100)
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Weight in kg")
    color = models.CharField(max_length=50, blank=True, null=True)
    
    # Health & Vaccination
    is_vaccinated = models.BooleanField(default=False)
    is_neutered = models.BooleanField(default=False)
    health_certificate = models.FileField(upload_to='health_certificates/', blank=True, null=True)
    
    # Images
    image = models.ImageField(upload_to='dogs/', blank=True, null=True)
    image2 = models.ImageField(upload_to='dogs/', blank=True, null=True)
    image3 = models.ImageField(upload_to='dogs/', blank=True, null=True)
    image4 = models.ImageField(upload_to='dogs/', blank=True, null=True)
    
    # Status & Relations
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dogs_for_sale')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['breed']),
            models.Index(fields=['price']),
            models.Index(fields=['location']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.breed} (${self.price})"
    
    def get_absolute_url(self):
        return reverse('dogs:detail', kwargs={'pk': self.pk})
    
    @property
    def age_display(self):
        if self.age < 12:
            return f"{self.age} month{'s' if self.age != 1 else ''}"
        else:
            years = self.age // 12
            months = self.age % 12
            if months == 0:
                return f"{years} year{'s' if years != 1 else ''}"
            else:
                return f"{years} year{'s' if years != 1 else ''}, {months} month{'s' if months != 1 else ''}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Normalize and resize uploaded images so browsers can render them reliably
        if self.image:
            self._normalize_and_resize_field('image')
        if self.image2:
            self._normalize_and_resize_field('image2')
        if self.image3:
            self._normalize_and_resize_field('image3')
        if self.image4:
            self._normalize_and_resize_field('image4')
    
    def _normalize_and_resize_field(self, field_name: str, max_size=(1200, 900)) -> None:
        """Ensure uploaded image is browser-friendly (convert to JPEG) and resized."""
        try:
            field = getattr(self, field_name)
            if not field or not field.name:
                return
            path = field.path
            with Image.open(path) as img:
                # Convert to RGB for JPEG and handle images with alpha
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                # Resize
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

                # If file is not .jpg/.jpeg, rewrite to .jpg and update field
                root, ext = os.path.splitext(path)
                if ext.lower() not in ['.jpg', '.jpeg']:
                    new_path = root + '.jpg'
                    img.save(new_path, format='JPEG', optimize=True, quality=85)
                    try:
                        os.remove(path)
                    except Exception:
                        pass
                    # Update field to point to new path relative to MEDIA_ROOT
                    from django.conf import settings
                    rel = os.path.relpath(new_path, str(settings.MEDIA_ROOT))
                    field.name = rel.replace('\\', '/')
                    super().save(update_fields=[field_name])
                else:
                    img.save(path, format='JPEG', optimize=True, quality=85)
        except Exception:
            # Best-effort; do not break saving if processing fails
            pass


class Favorite(models.Model):
    """Model for users to save favorite dogs"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'dog')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.dog.name}"


class Order(models.Model):
    """Model for dog purchase orders"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Contact Information
    buyer_name = models.CharField(max_length=100)
    buyer_email = models.EmailField()
    buyer_phone = models.CharField(max_length=20)
    
    # Additional details
    message = models.TextField(blank=True, null=True, help_text="Message to seller")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.id} - {self.dog.name} by {self.buyer.username}"

    # Shipping/Tracking (optional if seller ships)
    SHIPMENT_STATUS_CHOICES = [
        ('none', 'Not Applicable'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
    ]
    shipment_status = models.CharField(max_length=20, choices=SHIPMENT_STATUS_CHOICES, default='none')
    carrier = models.CharField(max_length=50, blank=True, null=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    estimated_delivery = models.DateField(blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)


class SavedSearch(models.Model):
    """Saved search criteria for dogs with email alerts"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_searches')
    name = models.CharField(max_length=100)
    # Store filters as JSON (breed, gender, location, price range, age range, vaccinated, neutered, search)
    params = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"SavedSearch {self.name} by {self.user.username}"


class Report(models.Model):
    """Reports for moderation on users or dog listings"""

    TARGET_CHOICES = [
        ('dog', 'Dog Listing'),
        ('user', 'User'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('reviewing', 'Reviewing'),
        ('closed', 'Closed'),
    ]

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    target_type = models.CharField(max_length=10, choices=TARGET_CHOICES)
    dog = models.ForeignKey('Dog', on_delete=models.CASCADE, null=True, blank=True, related_name='reports')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='reports_received')
    reason = models.CharField(max_length=200)
    details = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report {self.id} on {self.target_type}"


def _dog_matches_params(dog: 'Dog', params: dict) -> bool:
    try:
        if params.get('breed') and params['breed'].lower() not in dog.breed.lower():
            return False
        if params.get('gender') and params['gender'] != dog.gender:
            return False
        if params.get('location') and params['location'].lower() not in dog.location.lower():
            return False
        if params.get('min_price') and float(dog.price) < float(params['min_price']):
            return False
        if params.get('max_price') and float(dog.price) > float(params['max_price']):
            return False
        if params.get('min_age') and int(dog.age) < int(params['min_age']):
            return False
        if params.get('max_age') and int(dog.age) > int(params['max_age']):
            return False
        if params.get('vaccinated') and not dog.is_vaccinated:
            return False
        if params.get('neutered') and not dog.is_neutered:
            return False
        if params.get('search'):
            q = params['search'].lower()
            if q not in dog.name.lower() and q not in dog.breed.lower() and q not in dog.location.lower() and q not in (dog.description or '').lower():
                return False
        return dog.status == 'available'
    except Exception:
        return False


@receiver(post_save, sender=Dog)
def notify_saved_searches(sender, instance: 'Dog', created: bool, **kwargs):
    if not created:
        return
    try:
        from .models import SavedSearch
        searches = SavedSearch.objects.select_related('user').all()
        for s in searches:
            if _dog_matches_params(instance, s.params):
                if s.user.email:
                    send_mail(
                        subject=f"New dog matches your search: {instance.name}",
                        message=f"{instance.name} ({instance.breed}) in {instance.location} for ${instance.price}. View: {settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost'}{instance.get_absolute_url()}",
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                        recipient_list=[s.user.email],
                        fail_silently=True,
                    )
    except Exception:
        pass