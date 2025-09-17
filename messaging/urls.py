from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('conversation/<int:pk>/', views.conversation_detail, name='conversation'),
    path('send/<int:dog_pk>/', views.send_message, name='send_message'),
    path('start/<int:user_pk>/', views.create_conversation, name='start_conversation'),
    path('message/<int:message_id>/read/', views.mark_message_read, name='mark_read'),
    path('conversation/<int:conversation_id>/messages/', views.get_conversation_messages, name='get_messages'),
]
