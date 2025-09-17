from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q, Count
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Dog, Favorite, Order
from .forms import DogForm, OrderForm
from accounts.models import User


class HomeView(ListView):
    """Home page view with featured dogs and statistics"""
    model = Dog
    template_name = 'home.html'
    context_object_name = 'featured_dogs'
    
    def get_queryset(self):
        # Show featured dogs first, then recent dogs
        featured_dogs = Dog.objects.filter(status='available', is_featured=True).select_related('seller')
        recent_dogs = Dog.objects.filter(status='available', is_featured=False).select_related('seller').order_by('-created_at')
        
        # Combine featured and recent dogs, limit to 8 total
        all_dogs = list(featured_dogs) + list(recent_dogs)
        return all_dogs[:8]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get statistics
        context['total_dogs'] = Dog.objects.filter(status='available').count()
        context['total_sellers'] = User.objects.filter(role='seller').count()
        context['total_orders'] = Order.objects.filter(status='completed').count()
        
        # Get popular breeds
        popular_breeds = Dog.objects.filter(status='available').values('breed').annotate(
            count=Count('breed')
        ).order_by('-count')[:6]
        
        context['popular_breeds'] = [
            {'name': breed['breed'].title(), 'count': breed['count']} 
            for breed in popular_breeds
        ]
        
        return context


class DogListView(ListView):
    """List view for browsing all dogs"""
    model = Dog
    template_name = 'dogs/list.html'
    context_object_name = 'dogs'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Dog.objects.filter(status='available').select_related('seller')
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(breed__icontains=search) |
                Q(location__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Filter by breed
        breed = self.request.GET.get('breed')
        if breed:
            queryset = queryset.filter(breed__icontains=breed)
        
        # Filter by gender
        gender = self.request.GET.get('gender')
        if gender:
            queryset = queryset.filter(gender=gender)
        
        # Filter by price range
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Filter by age range
        min_age = self.request.GET.get('min_age')
        max_age = self.request.GET.get('max_age')
        if min_age:
            queryset = queryset.filter(age__gte=min_age)
        if max_age:
            queryset = queryset.filter(age__lte=max_age)
        
        # Filter by location
        location = self.request.GET.get('location')
        if location:
            queryset = queryset.filter(location__icontains=location)
        
        # Filter by health status
        if self.request.GET.get('vaccinated'):
            queryset = queryset.filter(is_vaccinated=True)
        if self.request.GET.get('neutered'):
            queryset = queryset.filter(is_neutered=True)
        
        # Sorting
        sort_by = self.request.GET.get('sort', '-created_at')
        valid_sorts = ['-created_at', 'created_at', 'price', '-price', 'name', '-name']
        if sort_by in valid_sorts:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get unique breeds for filter dropdown
        context['breeds'] = Dog.objects.filter(status='available').values_list('breed', flat=True).distinct()
        
        # Get unique locations for filter dropdown
        context['locations'] = Dog.objects.filter(status='available').values_list('location', flat=True).distinct()
        
        # Pass current filters to template
        context['current_search'] = self.request.GET.get('search', '')
        context['current_breed'] = self.request.GET.get('breed', '')
        context['current_gender'] = self.request.GET.get('gender', '')
        context['current_location'] = self.request.GET.get('location', '')
        context['current_sort'] = self.request.GET.get('sort', '-created_at')
        
        return context


class DogDetailView(DetailView):
    """Detail view for individual dog"""
    model = Dog
    template_name = 'dogs/detail.html'
    context_object_name = 'dog'
    
    def get_object(self):
        obj = super().get_object()
        # Increment view count
        obj.views_count += 1
        obj.save(update_fields=['views_count'])
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Check if user has favorited this dog
        if self.request.user.is_authenticated:
            context['is_favorited'] = Favorite.objects.filter(
                user=self.request.user, 
                dog=self.object
            ).exists()
        
        # Get similar dogs (same breed, different dog)
        context['similar_dogs'] = Dog.objects.filter(
            breed=self.object.breed,
            status='available'
        ).exclude(pk=self.object.pk).select_related('seller')[:4]
        
        # Get seller's other dogs
        context['seller_dogs'] = Dog.objects.filter(
            seller=self.object.seller,
            status='available'
        ).exclude(pk=self.object.pk).select_related('seller')[:4]
        
        return context


class DogCreateView(LoginRequiredMixin, CreateView):
    """Create view for adding new dogs (sellers only)"""
    model = Dog
    form_class = DogForm
    template_name = 'dogs/add.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_seller:
            messages.error(request, 'Only sellers can add dogs.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.seller = self.request.user
        messages.success(self.request, 'Dog added successfully!')
        return super().form_valid(form)


class DogUpdateView(LoginRequiredMixin, UpdateView):
    """Update view for editing dogs (owner only)"""
    model = Dog
    form_class = DogForm
    template_name = 'dogs/edit.html'
    
    def get_queryset(self):
        return Dog.objects.filter(seller=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Dog updated successfully!')
        return super().form_valid(form)


class DogDeleteView(LoginRequiredMixin, DeleteView):
    """Delete view for removing dogs (owner only)"""
    model = Dog
    template_name = 'dogs/delete.html'
    success_url = reverse_lazy('accounts:dashboard')
    
    def get_queryset(self):
        return Dog.objects.filter(seller=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Dog deleted successfully!')
        return super().delete(request, *args, **kwargs)


@login_required
def toggle_favorite(request, pk):
    """AJAX view to toggle favorite status"""
    if request.method == 'POST':
        dog = get_object_or_404(Dog, pk=pk)
        
        # Prevent sellers from favoriting dogs
        if request.user.is_seller:
            return JsonResponse({
                'error': 'Sellers cannot favorite dogs. Only buyers can add favorites.',
                'is_favorited': False
            }, status=400)
        
        # Prevent users from favoriting their own dogs
        if request.user == dog.seller:
            return JsonResponse({
                'error': 'You cannot favorite your own dog.',
                'is_favorited': False
            }, status=400)
        
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            dog=dog
        )
        
        if not created:
            favorite.delete()
            is_favorited = False
            message = 'Removed from favorites'
        else:
            is_favorited = True
            message = 'Added to favorites'
        
        return JsonResponse({
            'is_favorited': is_favorited,
            'message': message,
            'favorites_count': dog.favorited_by.count()
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def create_order(request, pk):
    """Create an order for a dog"""
    dog = get_object_or_404(Dog, pk=pk, status='available')
    
    # Prevent sellers from buying dogs
    if request.user.is_seller:
        messages.error(request, 'Sellers cannot purchase dogs. Only buyers can place orders.')
        return redirect('dogs:detail', pk=dog.pk)
    
    # Prevent users from buying their own dogs
    if request.user == dog.seller:
        messages.error(request, 'You cannot purchase your own dog.')
        return redirect('dogs:detail', pk=dog.pk)
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.buyer = request.user
            order.dog = dog
            order.save()
            
            # Update dog status to pending
            dog.status = 'pending'
            dog.save()
            
            messages.success(request, 'Order submitted successfully! The seller will contact you soon.')
            return redirect('dogs:detail', pk=dog.pk)
    else:
        form = OrderForm(initial={
            'buyer_name': request.user.full_name,
            'buyer_email': request.user.email,
            'buyer_phone': request.user.phone or '',
        })
    
    return render(request, 'dogs/order.html', {
        'form': form,
        'dog': dog
    })