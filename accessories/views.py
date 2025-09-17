from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView
from collections import defaultdict
import stripe
from django.conf import settings

from .forms import AccessoryForm, AccessorySearchForm
from .models import Accessory, AccessoryFavorite


class AccessoryListView(ListView):
    model = Accessory
    template_name = 'accessories/list.html'
    context_object_name = 'accessories'
    paginate_by = 12

    def get_queryset(self):
        queryset = Accessory.objects.filter(is_available=True, is_approved=True).order_by('-created_at')
        form = AccessorySearchForm(self.request.GET or None)
        if form.is_valid():
            query = form.cleaned_data.get('query')
            category = form.cleaned_data.get('category')
            min_price = form.cleaned_data.get('min_price')
            max_price = form.cleaned_data.get('max_price')
            brand = form.cleaned_data.get('brand')

            if query:
                queryset = queryset.filter(name__icontains=query)
            if category:
                queryset = queryset.filter(category=category)
            if min_price is not None:
                queryset = queryset.filter(price__gte=min_price)
            if max_price is not None:
                queryset = queryset.filter(price__lte=max_price)
            if brand:
                queryset = queryset.filter(brand__icontains=brand)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = AccessorySearchForm(self.request.GET or None)
        if self.request.user.is_authenticated and not self.request.user.is_seller:
            context['favorited_ids'] = set(
                AccessoryFavorite.objects.filter(user=self.request.user).values_list('accessory_id', flat=True)
            )
        return context


def accessories_shop(request):
    accessories = Accessory.objects.filter(is_available=True, is_approved=True).order_by('-created_at')
    return render(request, 'accessories/shop.html', {'accessories': accessories})


class AccessoryDetailView(DetailView):
    model = Accessory
    template_name = 'accessories/detail.html'
    context_object_name = 'accessory'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        accessory = self.object
        if self.request.user.is_authenticated:
            context['is_favorited'] = AccessoryFavorite.objects.filter(user=self.request.user, accessory=accessory).exists()
        context['related_accessories'] = Accessory.objects.filter(
            is_available=True, is_approved=True,
            category=accessory.category
        ).exclude(pk=accessory.pk).order_by('-created_at')[:4]
        return context


@login_required
def add_accessory(request):
    if request.method == 'POST':
        form = AccessoryForm(request.POST, request.FILES)
        if form.is_valid():
            accessory = form.save(commit=False)
            accessory.seller = request.user
            accessory.save()
            messages.success(request, 'Accessory added successfully.')
            return redirect(accessory.get_absolute_url())
    else:
        form = AccessoryForm()
    return render(request, 'accessories/add.html', {'form': form})


@login_required
def edit_accessory(request, pk):
    accessory = get_object_or_404(Accessory, pk=pk, seller=request.user)
    if request.method == 'POST':
        form = AccessoryForm(request.POST, request.FILES, instance=accessory)
        if form.is_valid():
            form.save()
            messages.success(request, 'Accessory updated successfully.')
            return redirect(accessory.get_absolute_url())
    else:
        form = AccessoryForm(instance=accessory)
    return render(request, 'accessories/edit.html', {'form': form, 'accessory': accessory})


@login_required
def delete_accessory(request, pk):
    accessory = get_object_or_404(Accessory, pk=pk, seller=request.user)
    if request.method == 'POST':
        accessory.delete()
        messages.success(request, 'Accessory deleted successfully.')
        return redirect(reverse('accessories:list'))
    return render(request, 'accessories/delete.html', {'accessory': accessory})


@login_required
def my_accessories(request):
    accessories = Accessory.objects.filter(seller=request.user).order_by('-created_at')
    return render(request, 'accessories/my_accessories.html', {'accessories': accessories})


@login_required
def toggle_accessory_favorite(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    accessory = get_object_or_404(Accessory, pk=pk)

    # Prevent sellers from favoriting accessories
    if request.user.is_seller:
        return JsonResponse({
            'error': 'Sellers cannot favorite accessories. Only buyers can add favorites.',
            'is_favorited': False
        }, status=400)

    # Prevent users from favoriting their own accessories
    if request.user == accessory.seller:
        return JsonResponse({
            'error': 'You cannot favorite your own accessory.',
            'is_favorited': False
        }, status=400)

    favorite, created = AccessoryFavorite.objects.get_or_create(
        user=request.user,
        accessory=accessory
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
        'favorites_count': accessory.favorited_by.count()
    })


@login_required
def favorite_accessories(request):
    if request.user.is_seller:
        messages.error(request, 'Sellers cannot access accessories favorites. Only buyers can favorite accessories.')
        return redirect('accounts:dashboard')

    favorites = AccessoryFavorite.objects.filter(user=request.user).select_related('accessory', 'accessory__seller').order_by('-created_at')

    return render(request, 'accessories/favorites.html', {
        'favorites': favorites,
    })


# -------- Cart (session-based) --------

def _get_cart(session):
    cart = session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}
    return cart


@login_required
def cart_view(request):
    cart = _get_cart(request.session)
    ids = [int(_id) for _id in cart.keys()]
    accessories = Accessory.objects.filter(id__in=ids)
    items = []
    total = 0
    for accessory in accessories:
        qty = int(cart.get(str(accessory.id), 1))
        line_total = accessory.price * qty
        total += line_total
        items.append({'accessory': accessory, 'quantity': qty, 'line_total': line_total})
    return render(request, 'accessories/cart.html', {'items': items, 'total': total})


@login_required
def add_to_cart(request, pk):
    if request.method != 'POST':
        return redirect('accessories:list')
    accessory = get_object_or_404(Accessory, pk=pk, is_available=True)
    cart = _get_cart(request.session)
    current = int(cart.get(str(accessory.id), 0))
    cart[str(accessory.id)] = min(current + 1, max(1, accessory.quantity or 1))
    request.session['cart'] = cart
    messages.success(request, f'Added "{accessory.name}" to cart.')
    return redirect(request.POST.get('next') or accessory.get_absolute_url())


@login_required
def update_cart(request, pk):
    if request.method != 'POST':
        return redirect('accessories:cart')
    accessory = get_object_or_404(Accessory, pk=pk)
    qty = int(request.POST.get('quantity', 1))
    qty = max(0, qty)
    cart = _get_cart(request.session)
    if qty == 0:
        cart.pop(str(accessory.id), None)
    else:
        cart[str(accessory.id)] = qty
    request.session['cart'] = cart
    return redirect('accessories:cart')


@login_required
def remove_from_cart(request, pk):
    accessory = get_object_or_404(Accessory, pk=pk)
    cart = _get_cart(request.session)
    if str(accessory.id) in cart:
        cart.pop(str(accessory.id))
        request.session['cart'] = cart
        messages.info(request, f'Removed "{accessory.name}" from cart.')
    return redirect('accessories:cart')


@login_required
def checkout_view(request):
    cart = _get_cart(request.session)
    if not cart:
        messages.info(request, 'Your cart is empty.')
        return redirect('accessories:cart')

    ids = [int(_id) for _id in cart.keys()]
    accessories = Accessory.objects.filter(id__in=ids, is_available=True, is_approved=True).select_related('seller')

    # Group items by seller for messaging-based checkout
    grouped = defaultdict(list)
    for accessory in accessories:
        grouped[accessory.seller].append({
            'accessory': accessory,
            'quantity': int(cart.get(str(accessory.id), 1)),
        })

    if request.method == 'POST':
        # On submit, redirect to messaging with a prefilled subject/content per seller
        seller_id = request.POST.get('seller_id')
        try:
            seller_id = int(seller_id)
        except Exception:
            seller_id = None
        if not seller_id:
            return redirect('accessories:checkout')

        # Build a summary message for that seller
        lines = []
        for item in grouped.get(next(s for s in grouped.keys() if s.id == seller_id), []):
            a = item['accessory']
            qty = item['quantity']
            lines.append(f"- {a.name} x{qty} (${a.price})")
        content = "Hello! I'd like to buy the following accessories from my cart:\n" + "\n".join(lines)
        request.session['prefill_message'] = content
        return redirect('messaging:start_conversation', user_pk=seller_id)

    return render(request, 'accessories/checkout.html', {
        'grouped_items': grouped,
    })


@login_required
def checkout_pay(request):
    # Create a single Stripe Checkout Session for all items (MVP)
    cart = _get_cart(request.session)
    if not cart:
        messages.info(request, 'Your cart is empty.')
        return redirect('accessories:cart')

    ids = [int(_id) for _id in cart.keys()]
    accessories = Accessory.objects.filter(id__in=ids, is_available=True, is_approved=True)

    if not settings.STRIPE_SECRET_KEY:
        messages.error(request, 'Payment is not configured. Contact support.')
        return redirect('accessories:checkout')

    stripe.api_key = settings.STRIPE_SECRET_KEY

    line_items = []
    for accessory in accessories:
        qty = int(cart.get(str(accessory.id), 1))
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': accessory.name,
                },
                'unit_amount': int(float(accessory.price) * 100),
            },
            'quantity': max(1, qty),
        })

    try:
        session = stripe.checkout.Session.create(
            mode='payment',
            payment_method_types=['card'],
            line_items=line_items,
            success_url=request.build_absolute_uri(reverse('accessories:checkout_success')),
            cancel_url=request.build_absolute_uri(reverse('accessories:checkout_cancel')),
            customer_email=request.user.email or None,
            metadata={'user_id': str(request.user.id)},
        )
    except Exception as e:
        messages.error(request, f'Payment error: {e}')
        return redirect('accessories:checkout')

    return redirect(session.url)


def checkout_success(request):
    # Clear cart on success
    request.session['cart'] = {}
    return render(request, 'accessories/checkout_success.html')


def checkout_cancel(request):
    messages.info(request, 'Payment cancelled.')
    return render(request, 'accessories/checkout_cancel.html')


