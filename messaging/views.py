from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from .models import Message, Conversation
from .forms import MessageForm
from dogs.models import Dog
from accounts.models import User


@login_required
def inbox(request):
    """User's message inbox"""
    conversations = Conversation.objects.filter(
        participants=request.user
    ).prefetch_related('participants').order_by('-updated_at')
    
    # Add other participant for each conversation
    conversations_with_other = []
    for conversation in conversations:
        other_user = conversation.get_other_participant(request.user)
        conversations_with_other.append({
            'conversation': conversation,
            'other_user': other_user
        })
    
    return render(request, 'messaging/inbox.html', {
        'conversations_with_other': conversations_with_other
    })


@login_required
def conversation_detail(request, pk):
    """View a specific conversation"""
    conversation = get_object_or_404(
        Conversation,
        pk=pk,
        participants=request.user
    )
    
    messages_list = conversation.messages.select_related('sender', 'receiver').order_by('sent_at')
    
    # Mark messages as read
    messages_list.filter(receiver=request.user, is_read=False).update(is_read=True)
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.receiver = conversation.get_other_participant(request.user)
            message.dog = conversation.dog
            message.conversation = conversation
            message.save()
            
            # Update conversation timestamp
            conversation.save()
            
            return redirect('messaging:conversation', pk=conversation.pk)
    else:
        form = MessageForm()
    
    return render(request, 'messaging/conversation.html', {
        'conversation': conversation,
        'messages': messages_list,
        'form': form,
        'other_user': conversation.get_other_participant(request.user)
    })


@login_required
def send_message(request, dog_pk):
    """Send a message about a specific dog"""
    dog = get_object_or_404(Dog, pk=dog_pk)
    
    if request.user == dog.seller:
        messages.error(request, 'You cannot send a message to yourself.')
        return redirect('dogs:detail', pk=dog.pk)
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            # Get or create conversation
            conversation, created = Conversation.objects.get_or_create(
                dog=dog,
                defaults={'dog': dog}
            )
            
            # Add participants if conversation was just created
            if created:
                conversation.participants.add(request.user, dog.seller)
            
            # Create message
            message = form.save(commit=False)
            message.sender = request.user
            message.receiver = dog.seller
            message.dog = dog
            message.conversation = conversation
            message.save()
            
            # Update conversation timestamp
            conversation.save()
            
            messages.success(request, 'Message sent successfully!')
            return redirect('messaging:conversation', pk=conversation.pk)
    else:
        form = MessageForm(initial={
            'subject': f'Interested in {dog.name}',
            'content': f'Hi! I\'m interested in your {dog.breed} named {dog.name}. Could you tell me more about them?'
        })
    
    return render(request, 'messaging/send_message.html', {
        'form': form,
        'dog': dog
    })


@login_required
def create_conversation(request, user_pk):
    """Create a conversation with another user"""
    other_user = get_object_or_404(User, pk=user_pk)
    
    if request.user == other_user:
        messages.error(request, 'You cannot start a conversation with yourself.')
        return redirect('home')
    
    # Check if conversation already exists
    existing_conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(participants=other_user).first()
    
    if existing_conversation:
        return redirect('messaging:conversation', pk=existing_conversation.pk)
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            # Create conversation
            conversation = Conversation.objects.create()
            conversation.participants.add(request.user, other_user)
            
            # Create message
            message = form.save(commit=False)
            message.sender = request.user
            message.receiver = other_user
            message.save()
            
            messages.success(request, 'Conversation started!')
            return redirect('messaging:conversation', pk=conversation.pk)
    else:
        form = MessageForm()
    
    return render(request, 'messaging/start_conversation.html', {
        'form': form,
        'other_user': other_user
    })


@login_required
def mark_message_read(request, message_id):
    """Mark a specific message as read"""
    message = get_object_or_404(Message, id=message_id, receiver=request.user)
    message.mark_as_read()
    return JsonResponse({'status': 'success', 'read_at': message.read_at.isoformat()})


@login_required
def get_conversation_messages(request, conversation_id):
    """Get messages for a conversation (for real-time updates)"""
    conversation = get_object_or_404(
        Conversation,
        pk=conversation_id,
        participants=request.user
    )
    
    messages_list = conversation.messages.select_related('sender', 'receiver').order_by('sent_at')
    
    # Mark messages as read when viewing
    messages_list.filter(receiver=request.user, is_read=False).update(
        is_read=True, 
        read_at=timezone.now()
    )
    
    messages_data = []
    for message in messages_list:
        messages_data.append({
            'id': message.id,
            'content': message.content,
            'sender': message.sender.username,
            'sender_name': message.sender.first_name + ' ' + message.sender.last_name,
            'sent_at': message.sent_at.isoformat(),
            'is_read': message.is_read,
            'read_at': message.read_at.isoformat() if message.read_at else None,
            'is_sender': message.sender == request.user
        })
    
    return JsonResponse({'messages': messages_data})