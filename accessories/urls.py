from django.urls import path
from . import views

app_name = 'accessories'

urlpatterns = [
    path('', views.AccessoryListView.as_view(), name='list'),
    path('shop/', views.accessories_shop, name='shop'),
    path('detail/<int:pk>/', views.AccessoryDetailView.as_view(), name='detail'),
    path('add/', views.add_accessory, name='add'),
    path('edit/<int:pk>/', views.edit_accessory, name='edit'),
    path('delete/<int:pk>/', views.delete_accessory, name='delete'),
    path('my-accessories/', views.my_accessories, name='my_accessories'),
]
