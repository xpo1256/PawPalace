from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from PIL import Image
import os

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
    image = models.ImageField(upload_to='dogs/')
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
        
        # Resize main image
        if self.image:
            self._resize_image(self.image.path)
    
    def _resize_image(self, image_path, max_size=(800, 600)):
        """Resize image to optimize storage and loading times"""
        try:
            with Image.open(image_path) as img:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                img.save(image_path, optimize=True, quality=85)
        except Exception:
            pass  # Handle gracefully if image processing fails


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