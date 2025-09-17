from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import User
from .forms import UserRegistrationForm, UserProfileForm
from .forms import SellerReviewForm
from dogs.models import Dog, Favorite, Order
from accessories.models import Accessory
from django.http import JsonResponse


class CustomLoginView(LoginView):
    """Custom login view"""
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        messages.success(self.request, f'Welcome back, {form.get_user().first_name or form.get_user().username}!')
        return super().form_valid(form)


class UserRegistrationView(CreateView):
    """User registration view"""
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('home')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.save()
        
        # Log the user in after registration
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        if user:
            login(self.request, user)
            role_display = "Seller" if user.is_seller else "Buyer"
            messages.success(self.request, f'Welcome to PawPalace, {user.first_name or user.username}! You are registered as a {role_display}.')
        
        return response
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


@login_required
def dashboard(request):
    """User dashboard view"""
    context = {}
    
    if request.user.is_seller:
        # Seller dashboard data
        context['my_dogs'] = Dog.objects.filter(seller=request.user).order_by('-created_at')
        context['total_dogs'] = context['my_dogs'].count()
        context['available_dogs'] = context['my_dogs'].filter(status='available').count()
        context['sold_dogs'] = context['my_dogs'].filter(status='sold').count()
        context['pending_orders'] = Order.objects.filter(
            dog__seller=request.user,
            status='pending'
        ).select_related('dog', 'buyer').order_by('-created_at')[:5]
        context['pending_orders_count'] = Order.objects.filter(
            dog__seller=request.user,
            status='pending'
        ).count()
        context['total_views'] = sum(dog.views_count for dog in context['my_dogs'])
        
        # Recent activity
        context['recent_orders'] = Order.objects.filter(
            dog__seller=request.user
        ).select_related('dog', 'buyer').order_by('-created_at')[:10]
        
    else:
        # Buyer dashboard data
        context['favorites'] = Favorite.objects.filter(
            user=request.user
        ).select_related('dog', 'dog__seller').order_by('-created_at')[:6]
        context['my_orders'] = Order.objects.filter(
            buyer=request.user
        ).select_related('dog', 'dog__seller').order_by('-created_at')[:10]
        context['total_favorites'] = Favorite.objects.filter(user=request.user).count()
        context['total_orders'] = context['my_orders'].count()
    
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile(request):
    """User profile view"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def favorites(request):
    """User favorites view (buyers only)"""
    if request.user.is_seller:
        messages.error(request, 'Sellers cannot access favorites. Only buyers can favorite dogs.')
        return redirect('accounts:dashboard')
    
    favorites_list = Favorite.objects.filter(
        user=request.user
    ).select_related('dog', 'dog__seller').order_by('-created_at')
    
    return render(request, 'accounts/favorites.html', {
        'favorites': favorites_list
    })


@login_required
def orders(request):
    """User orders view (buyers only)"""
    if request.user.is_seller:
        messages.error(request, 'Sellers cannot place orders. Only buyers can purchase dogs.')
        return redirect('accounts:seller_orders')
    
    orders_list = Order.objects.filter(
        buyer=request.user
    ).select_related('dog', 'dog__seller').order_by('-created_at')
    
    return render(request, 'accounts/orders.html', {
        'orders': orders_list
    })


@login_required
def seller_orders(request):
    """Seller orders view (orders for seller's dogs)"""
    if not request.user.is_seller:
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    orders_list = Order.objects.filter(
        dog__seller=request.user
    ).select_related('dog', 'buyer').order_by('-created_at')
    
    return render(request, 'accounts/seller_orders.html', {
        'orders': orders_list,
    })


def seller_profile(request, pk):
    """Public seller profile page with listings"""
    seller = User.objects.filter(pk=pk, role='seller').first()
    if not seller:
        messages.error(request, 'Seller not found.')
        return redirect('home')

    seller_dogs = Dog.objects.filter(seller=seller, status='available').order_by('-created_at')
    seller_accessories = Accessory.objects.filter(seller=seller, is_available=True).order_by('-created_at')

    # Reviews and form
    from .models import SellerReview
    can_review = False
    if request.user.is_authenticated and not request.user.is_seller and request.user != seller:
        # Buyer can review if has a completed order with this seller
        can_review = Order.objects.filter(buyer=request.user, dog__seller=seller, status='completed').exists()

    if request.method == 'POST' and can_review:
        form = SellerReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.reviewer = request.user
            review.seller = seller
            review.save()
            messages.success(request, 'Thank you for your review!')
            return redirect('accounts:seller_profile', pk=pk)
    else:
        form = SellerReviewForm()

    reviews = SellerReview.objects.filter(seller=seller).select_related('reviewer')
    avg_rating = reviews.aggregate(avg=models.Avg('rating'))['avg'] or 0

    context = {
        'seller_user': seller,
        'seller_dogs': seller_dogs,
        'seller_accessories': seller_accessories,
        'total_dogs': seller_dogs.count(),
        'total_accessories': seller_accessories.count(),
        'reviews': reviews,
        'avg_rating': avg_rating,
        'can_review': can_review,
        'review_form': form,
    }
    return render(request, 'accounts/seller_profile.html', context)


class CustomLogoutView(LogoutView):
    """Custom logout view"""
    
    def dispatch(self, request, *args, **kwargs):
        messages.success(request, 'You have been successfully logged out.')
        return super().dispatch(request, *args, **kwargs)


@login_required
def notifications_poll(request):
    """Lightweight polling endpoint for client notifications.
    Returns counts for unread messages, pending orders (for sellers), and favorites on user's items.
    """
    from messaging.models import Message
    data = {
        'unread_messages': 0,
        'seller_pending_orders': 0,
        'my_items_favorited_count': 0,
    }

    # Unread messages for any user
    data['unread_messages'] = Message.objects.filter(receiver=request.user, is_read=False).count()

    # Seller-specific: pending orders for their dogs
    if request.user.is_seller:
        data['seller_pending_orders'] = Order.objects.filter(dog__seller=request.user, status='pending').count()
        # Favorites on seller's dogs
        data['my_items_favorited_count'] = Favorite.objects.filter(dog__seller=request.user).count()
    else:
        # Buyer: favorites they have added (for badge updates)
        try:
            from accessories.models import AccessoryFavorite
            data['my_items_favorited_count'] = Favorite.objects.filter(user=request.user).count() + AccessoryFavorite.objects.filter(user=request.user).count()
        except Exception:
            data['my_items_favorited_count'] = Favorite.objects.filter(user=request.user).count()

    return JsonResponse(data)