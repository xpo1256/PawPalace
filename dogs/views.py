from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q, Count
from django.urls import reverse_lazy
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Dog, Favorite, Order
from .forms import DogForm, OrderForm, SavedSearchForm, ReportForm
from .models import Report
from .forms import DogForm, OrderForm, SavedSearchForm
from accounts.models import User
from .models import SavedSearch


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
        
        # Saved search form prefilled from current filters
        if self.request.user.is_authenticated and not self.request.user.is_seller:
            initial = {
                'search': self.request.GET.get('search', ''),
                'breed': self.request.GET.get('breed', ''),
                'gender': self.request.GET.get('gender', ''),
                'location': self.request.GET.get('location', ''),
                'min_price': self.request.GET.get('min_price'),
                'max_price': self.request.GET.get('max_price'),
                'min_age': self.request.GET.get('min_age'),
                'max_age': self.request.GET.get('max_age'),
                'vaccinated': bool(self.request.GET.get('vaccinated')),
                'neutered': bool(self.request.GET.get('neutered')),
            }
            context['saved_search_form'] = SavedSearchForm(initial=initial)
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
    dog = get_object_or_404(Dog, pk=pk)
    
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
            with transaction.atomic():
                # Re-fetch with lock to avoid race conditions
                dog_locked = Dog.objects.select_for_update().get(pk=dog.pk)
                if dog_locked.status != 'available':
                    messages.error(request, 'Sorry, this dog is not available anymore.')
                    return redirect('dogs:detail', pk=dog.pk)

                # Prevent duplicate active orders by same buyer
                if Order.objects.filter(buyer=request.user, dog=dog_locked, status__in=['pending', 'confirmed']).exists():
                    messages.info(request, 'You already have an active order for this dog.')
                    return redirect('dogs:detail', pk=dog.pk)

                order = form.save(commit=False)
                order.buyer = request.user
                order.dog = dog_locked
                order.save()

                # Update dog status to pending
                dog_locked.status = 'pending'
                dog_locked.save(update_fields=['status'])

            # Ensure a conversation exists and notify via message and email (best-effort)
            try:
                from messaging.models import Conversation, Message
                conversation = Conversation.objects.filter(dog=dog).filter(participants=request.user).filter(participants=dog.seller).first()
                if not conversation:
                    conversation = Conversation.objects.create(dog=dog)
                    conversation.participants.add(request.user, dog.seller)
                Message.objects.create(
                    sender=request.user,
                    receiver=dog.seller,
                    dog=dog,
                    conversation=conversation,
                    subject=f'New order for {dog.name}',
                    content=f'Hi {dog.seller.first_name or dog.seller.username}, I have placed an order for {dog.name}. Looking forward to your confirmation.'
                )
            except Exception:
                pass

            # Email notifications (console backend in dev)
            try:
                send_mail(
                    subject=f'New order placed for {dog.name}',
                    message=f'Buyer {request.user.username} placed an order for {dog.name}. Log in to review.',
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                    recipient_list=[dog.seller.email] if dog.seller.email else [],
                    fail_silently=True,
                )
                if request.user.email:
                    send_mail(
                        subject=f'Order submitted for {dog.name}',
                        message='Your order was submitted. The seller will review and respond shortly.',
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                        recipient_list=[request.user.email],
                        fail_silently=True,
                    )
            except Exception:
                pass

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


@login_required
@require_POST
def accept_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, status='pending')
    # Only the seller of the dog can accept
    if request.user != order.dog.seller:
        messages.error(request, 'You do not have permission to accept this order.')
        return redirect('accounts:seller_orders')
    order.status = 'confirmed'
    order.save(update_fields=['status', 'updated_at'])
    # Email notify buyer
    try:
        if order.buyer.email:
            send_mail(
                subject=f'Your order for {order.dog.name} was accepted',
                message='The seller accepted your order. You can coordinate next steps via Messages.',
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                recipient_list=[order.buyer.email],
                fail_silently=True,
            )
    except Exception:
        pass
    messages.success(request, 'Order accepted. Please coordinate with the buyer via messages.')
    return redirect('accounts:seller_orders')


@login_required
@require_POST
def decline_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, status='pending')
    if request.user != order.dog.seller:
        messages.error(request, 'You do not have permission to decline this order.')
        return redirect('accounts:seller_orders')
    order.status = 'cancelled'
    order.save(update_fields=['status', 'updated_at'])
    # Revert dog to available
    try:
        order.dog.status = 'available'
        order.dog.save(update_fields=['status'])
    except Exception:
        pass
    # Notify buyer
    try:
        if order.buyer.email:
            send_mail(
                subject=f'Your order for {order.dog.name} was declined',
                message='The seller declined your order. You may explore other listings.',
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                recipient_list=[order.buyer.email],
                fail_silently=True,
            )
    except Exception:
        pass
    messages.info(request, 'Order declined.')
    return redirect('accounts:seller_orders')


@login_required
@require_POST
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    # Buyer can cancel when pending or confirmed; seller can also cancel if needed
    if request.user != order.buyer and request.user != order.dog.seller:
        messages.error(request, 'You do not have permission to cancel this order.')
        return redirect('accounts:orders')
    if order.status in ['completed', 'cancelled']:
        messages.info(request, 'This order is already finalized.')
        return redirect('accounts:orders')
    order.status = 'cancelled'
    order.save(update_fields=['status', 'updated_at'])
    # If was pending/confirmed, free the dog
    try:
        if order.dog.status in ['pending']:
            order.dog.status = 'available'
            order.dog.save(update_fields=['status'])
    except Exception:
        pass
    messages.success(request, 'Order cancelled.')
    return redirect('accounts:orders' if request.user == order.buyer else 'accounts:seller_orders')


@login_required
@require_POST
def complete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, status='confirmed')
    # Only seller can mark completed
    if request.user != order.dog.seller:
        messages.error(request, 'You do not have permission to complete this order.')
        return redirect('accounts:seller_orders')
    order.status = 'completed'
    order.dog.status = 'sold'
    order.dog.save(update_fields=['status'])
    order.save(update_fields=['status', 'updated_at'])
    # Notify buyer
    try:
        if order.buyer.email:
            send_mail(
                subject=f'Order completed for {order.dog.name}',
                message='Congratulations! The order is marked completed. Please leave a review for the seller.',
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                recipient_list=[order.buyer.email],
                fail_silently=True,
            )
    except Exception:
        pass
    messages.success(request, 'Order marked as completed. Congratulations!')
    return redirect('accounts:seller_orders')


@login_required
@require_POST
def save_search(request):
    if request.user.is_seller:
        return JsonResponse({'error': 'Sellers cannot save searches.'}, status=400)
    form = SavedSearchForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'error': 'Invalid form'}, status=400)
    params = form.build_params()
    SavedSearch.objects.create(user=request.user, name=form.cleaned_data['name'], params=params)
    messages.success(request, 'Search saved. We will email you when new matching dogs are listed.')
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def update_tracking(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.user != order.dog.seller:
        messages.error(request, 'You do not have permission to update this order.')
        return redirect('accounts:seller_orders')
    shipment_status = request.POST.get('shipment_status')
    carrier = request.POST.get('carrier')
    tracking_number = request.POST.get('tracking_number')
    estimated_delivery = request.POST.get('estimated_delivery')
    allowed = {'processing', 'shipped', 'in_transit', 'delivered'}
    if shipment_status not in allowed:
        shipment_status = 'processing'
    order.shipment_status = shipment_status
    order.carrier = carrier or None
    order.tracking_number = tracking_number or None
    if estimated_delivery:
        try:
            from datetime import datetime
            order.estimated_delivery = datetime.strptime(estimated_delivery, '%Y-%m-%d').date()
        except Exception:
            pass
    # Set timestamps heuristically
    from django.utils import timezone
    if shipment_status == 'shipped' and not order.shipped_at:
        order.shipped_at = timezone.now()
    if shipment_status == 'delivered':
        order.delivered_at = timezone.now()
    order.save()
    messages.success(request, 'Tracking updated.')
    return redirect('accounts:seller_orders')


@login_required
def report_view(request, pk=None):
    # Report a dog or a user (from seller profile)
    target_dog = None
    reported_user = None
    if pk:
        target_dog = get_object_or_404(Dog, pk=pk)
        reported_user = target_dog.seller
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            if target_dog and report.target_type == 'dog':
                report.dog = target_dog
            if reported_user and report.target_type == 'user':
                report.reported_user = reported_user
            report.save()
            messages.success(request, 'Report submitted. Our team will review it.')
            return redirect(target_dog.get_absolute_url() if target_dog else 'home')
    else:
        form = ReportForm()
    return render(request, 'dogs/report.html', {'form': form, 'dog': target_dog})


# -------- Session-based Dog Cart (one-per-dog) --------

def _get_dog_cart(session):
    cart = session.get('dog_cart', {})
    if not isinstance(cart, dict):
        cart = {}
    return cart


@login_required
def dog_cart_view(request):
    cart = _get_dog_cart(request.session)
    ids = [int(_id) for _id in cart.keys()]
    dogs_qs = Dog.objects.filter(id__in=ids)
    items = []
    for dog in dogs_qs:
        items.append({'dog': dog})
    return render(request, 'dogs/cart.html', {'items': items})


@login_required
def add_dog_to_cart(request, pk):
    if request.method != 'POST':
        return redirect('dogs:detail', pk=pk)
    dog = get_object_or_404(Dog, pk=pk, status='available')
    # Sellers cannot add, nor can owner
    if request.user.is_seller or request.user == dog.seller:
        messages.error(request, 'Only buyers can add dogs to cart and not their own listings.')
        return redirect('dogs:detail', pk=dog.pk)
    cart = _get_dog_cart(request.session)
    # Only allow one entry per dog (value always 1)
    cart[str(dog.id)] = 1
    request.session['dog_cart'] = cart
    messages.success(request, f'Added "{dog.name}" to dog cart.')
    return redirect(request.POST.get('next') or dog.get_absolute_url())


@login_required
def remove_dog_from_cart(request, pk):
    dog = get_object_or_404(Dog, pk=pk)
    cart = _get_dog_cart(request.session)
    if str(dog.id) in cart:
        cart.pop(str(dog.id))
        request.session['dog_cart'] = cart
        messages.info(request, f'Removed "{dog.name}" from dog cart.')
    return redirect('dogs:cart')