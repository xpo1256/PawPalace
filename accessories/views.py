from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Accessory, AccessoryCategory
from .forms import AccessoryForm, AccessorySearchForm


class AccessoryListView(ListView):
    """List view for all accessories"""
    model = Accessory
    template_name = 'accessories/list.html'
    context_object_name = 'accessories'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Accessory.objects.filter(is_available=True, is_approved=True).select_related('seller', 'accessory_category')
        
        # Search functionality
        search_query = self.request.GET.get('query')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(brand__icontains=search_query) |
                Q(category__icontains=search_query)
            )
        
        # Category filter
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Price range filter
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Brand filter
        brand = self.request.GET.get('brand')
        if brand:
            queryset = queryset.filter(brand__icontains=brand)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = AccessorySearchForm(self.request.GET)
        context['categories'] = Accessory.CATEGORY_CHOICES
        context['featured_accessories'] = Accessory.objects.filter(
            is_featured=True, 
            is_available=True, 
            is_approved=True
        )[:6]
        return context


class AccessoryDetailView(DetailView):
    """Detail view for individual accessories"""
    model = Accessory
    template_name = 'accessories/detail.html'
    context_object_name = 'accessory'
    
    def get_queryset(self):
        return Accessory.objects.filter(is_available=True, is_approved=True).select_related('seller', 'accessory_category')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        accessory = self.get_object()
        
        # Get related accessories from the same category
        context['related_accessories'] = Accessory.objects.filter(
            category=accessory.category,
            is_available=True,
            is_approved=True
        ).exclude(pk=accessory.pk)[:4]
        
        return context


@login_required
def add_accessory(request):
    """Add new accessory (sellers only)"""
    if not request.user.is_seller:
        messages.error(request, 'Only sellers can add accessories.')
        return redirect('accessories:list')
    
    if request.method == 'POST':
        form = AccessoryForm(request.POST, request.FILES)
        if form.is_valid():
            accessory = form.save(commit=False)
            accessory.seller = request.user
            accessory.save()
            messages.success(request, 'Accessory added successfully!')
            return redirect('accessories:detail', pk=accessory.pk)
    else:
        form = AccessoryForm()
    
    return render(request, 'accessories/add.html', {'form': form})


@login_required
def edit_accessory(request, pk):
    """Edit accessory (sellers only, their own accessories)"""
    accessory = get_object_or_404(Accessory, pk=pk)
    
    if not request.user.is_seller or accessory.seller != request.user:
        messages.error(request, 'You can only edit your own accessories.')
        return redirect('accessories:detail', pk=pk)
    
    if request.method == 'POST':
        form = AccessoryForm(request.POST, request.FILES, instance=accessory)
        if form.is_valid():
            form.save()
            messages.success(request, 'Accessory updated successfully!')
            return redirect('accessories:detail', pk=accessory.pk)
    else:
        form = AccessoryForm(instance=accessory)
    
    return render(request, 'accessories/edit.html', {'form': form, 'accessory': accessory})


@login_required
def delete_accessory(request, pk):
    """Delete accessory (sellers only, their own accessories)"""
    accessory = get_object_or_404(Accessory, pk=pk)
    
    if not request.user.is_seller or accessory.seller != request.user:
        messages.error(request, 'You can only delete your own accessories.')
        return redirect('accessories:detail', pk=pk)
    
    if request.method == 'POST':
        accessory.delete()
        messages.success(request, 'Accessory deleted successfully!')
        return redirect('accessories:list')
    
    return render(request, 'accessories/delete.html', {'accessory': accessory})


@login_required
def my_accessories(request):
    """View seller's own accessories"""
    if not request.user.is_seller:
        messages.error(request, 'Only sellers can view their accessories.')
        return redirect('accessories:list')
    
    accessories = Accessory.objects.filter(seller=request.user).order_by('-created_at')
    
    return render(request, 'accessories/my_accessories.html', {
        'accessories': accessories
    })


def accessories_shop(request):
    """Main shop page with featured accessories and categories"""
    featured_accessories = Accessory.objects.filter(
        is_featured=True, 
        is_available=True, 
        is_approved=True
    )[:8]
    
    categories = Accessory.CATEGORY_CHOICES
    recent_accessories = Accessory.objects.filter(
        is_available=True, 
        is_approved=True
    ).order_by('-created_at')[:6]
    
    return render(request, 'accessories/shop.html', {
        'featured_accessories': featured_accessories,
        'categories': categories,
        'recent_accessories': recent_accessories
    })
