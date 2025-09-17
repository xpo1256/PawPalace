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
]
