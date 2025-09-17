from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView

from .forms import AccessoryForm, AccessorySearchForm
from .models import Accessory, AccessoryFavorite


class AccessoryListView(ListView):
    model = Accessory
    template_name = 'accessories/list.html'
    context_object_name = 'accessories'
    paginate_by = 12

    def get_queryset(self):
        queryset = Accessory.objects.filter(is_available=True).order_by('-created_at')
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
        return context


def accessories_shop(request):
    accessories = Accessory.objects.filter(is_available=True).order_by('-created_at')
    return render(request, 'accessories/shop.html', {'accessories': accessories})


class AccessoryDetailView(DetailView):
    model = Accessory
    template_name = 'accessories/detail.html'
    context_object_name = 'accessory'


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


