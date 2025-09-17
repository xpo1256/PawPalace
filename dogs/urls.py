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
]
