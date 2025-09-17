from django.contrib import admin
from .models import Dog, Favorite, Order


@admin.register(Dog)
class DogAdmin(admin.ModelAdmin):
    """Admin configuration for Dog model"""
    
    list_display = ('name', 'breed', 'age', 'gender', 'price', 'status', 'seller', 'location', 'views_count', 'created_at')
    list_filter = ('breed', 'gender', 'status', 'is_vaccinated', 'is_neutered', 'is_featured', 'created_at')
    search_fields = ('name', 'breed', 'location', 'seller__username', 'seller__email')
    ordering = ('-created_at',)
    readonly_fields = ('views_count', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'breed', 'age', 'gender', 'price', 'seller')
        }),
        ('Details', {
            'fields': ('description', 'location', 'weight', 'color')
        }),
        ('Health & Vaccination', {
            'fields': ('is_vaccinated', 'is_neutered', 'health_certificate')
        }),
        ('Images', {
            'fields': ('image', 'image2', 'image3', 'image4')
        }),
        ('Status & Features', {
            'fields': ('status', 'is_featured')
        }),
        ('Metadata', {
            'fields': ('views_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('seller')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Admin configuration for Favorite model"""
    
    list_display = ('user', 'dog', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'dog__name', 'dog__breed')
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'dog')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin configuration for Order model"""
    
    list_display = ('id', 'buyer', 'dog', 'status', 'buyer_name', 'buyer_email', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('buyer__username', 'dog__name', 'buyer_name', 'buyer_email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Order Information', {
            'fields': ('buyer', 'dog', 'status')
        }),
        ('Contact Details', {
            'fields': ('buyer_name', 'buyer_email', 'buyer_phone')
        }),
        ('Additional Information', {
            'fields': ('message',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('buyer', 'dog')