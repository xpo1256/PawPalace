from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class AccessoryCategory(models.Model):
    """Model for accessory categories"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, default='fas fa-paw')  # FontAwesome icon
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Accessory Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Accessory(models.Model):
    """Model for dog accessories and food"""
    
    CATEGORY_CHOICES = [
        ('food', 'Food & Treats'),
        ('toys', 'Toys & Play'),
        ('health', 'Health & Grooming'),
        ('safety', 'Safety & Training'),
        ('bedding', 'Bedding & Comfort'),
        ('clothing', 'Clothing & Accessories'),
        ('travel', 'Travel & Outdoor'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    accessory_category = models.ForeignKey(AccessoryCategory, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Images
    image = models.ImageField(upload_to='accessories/', blank=True, null=True)
    image2 = models.ImageField(upload_to='accessories/', blank=True, null=True)
    image3 = models.ImageField(upload_to='accessories/', blank=True, null=True)
    
    # Seller information
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accessories')
    
    # Product details
    brand = models.CharField(max_length=100, blank=True, null=True)
    size = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    material = models.CharField(max_length=100, blank=True, null=True)
    weight = models.CharField(max_length=50, blank=True, null=True)
    
    # Availability
    is_available = models.BooleanField(default=True)
    quantity = models.PositiveIntegerField(default=1)
    
    # Status
    is_featured = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Accessories"
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('accessories:detail', kwargs={'pk': self.pk})
    
    @property
    def primary_image(self):
        """Get the primary image for the accessory"""
        if self.image:
            return self.image
        return None
    
    @property
    def all_images(self):
        """Get all images for the accessory"""
        images = []
        if self.image:
            images.append(self.image)
        if self.image2:
            images.append(self.image2)
        if self.image3:
            images.append(self.image3)
        return images
    
    @property
    def is_seller(self):
        """Check if the current user is the seller"""
        return self.seller.role == 'seller'
