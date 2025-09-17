from django.urls import path
from . import views

app_name = 'dogs'

urlpatterns = [
    path('', views.DogListView.as_view(), name='list'),
    path('<int:pk>/', views.DogDetailView.as_view(), name='detail'),
    path('add/', views.DogCreateView.as_view(), name='add'),
    path('<int:pk>/edit/', views.DogUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.DogDeleteView.as_view(), name='delete'),
    path('<int:pk>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('<int:pk>/order/', views.create_order, name='create_order'),
    path('order/<int:order_id>/accept/', views.accept_order, name='accept_order'),
    path('order/<int:order_id>/decline/', views.decline_order, name='decline_order'),
    path('order/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('order/<int:order_id>/complete/', views.complete_order, name='complete_order'),
    path('saved-search/create/', views.save_search, name='save_search'),
    path('order/<int:order_id>/tracking/', views.update_tracking, name='update_tracking'),
    # Dog cart
    path('cart/', views.dog_cart_view, name='cart'),
    path('<int:pk>/cart/add/', views.add_dog_to_cart, name='add_to_cart'),
    path('<int:pk>/cart/remove/', views.remove_dog_from_cart, name='remove_from_cart'),
    path('<int:pk>/report/', views.report_view, name='report_dog'),
]
