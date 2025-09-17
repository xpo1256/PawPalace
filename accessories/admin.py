from django.contrib import admin
from .models import Accessory, AccessoryCategory, AccessoryFavorite


@admin.register(AccessoryCategory)
class AccessoryCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(Accessory)
class AccessoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'seller', 'category', 'price', 'is_available', 'is_featured', 'is_approved', 'created_at']
    list_filter = ['category', 'is_available', 'is_featured', 'is_approved', 'created_at']
    search_fields = ['name', 'description', 'brand', 'seller__username']
    list_editable = ['is_available', 'is_featured', 'is_approved']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'price', 'category', 'accessory_category')
        }),
        ('Images', {
            'fields': ('image', 'image2', 'image3')
        }),
        ('Product Details', {
            'fields': ('brand', 'size', 'color', 'material', 'weight')
        }),
        ('Availability', {
            'fields': ('is_available', 'quantity')
        }),
        ('Status', {
            'fields': ('is_featured', 'is_approved')
        }),
        ('Seller', {
            'fields': ('seller',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(AccessoryFavorite)
class AccessoryFavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'accessory', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'accessory__name']
