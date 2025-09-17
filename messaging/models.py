from django.db import models
from django.contrib.auth import get_user_model
from dogs.models import Dog

User = get_user_model()


class Message(models.Model):
    """Model for messages between buyers and sellers"""
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE, related_name='messages', blank=True, null=True)
    conversation = models.ForeignKey('Conversation', on_delete=models.CASCADE, related_name='messages', blank=True, null=True)
    
    subject = models.CharField(max_length=200, blank=True, null=True)
    content = models.TextField()
    
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username}"
    
    def mark_as_read(self):
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


class Conversation(models.Model):
    """Model to group messages between two users about a specific dog"""
    
    participants = models.ManyToManyField(User, related_name='conversations')
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE, related_name='conversations', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        participants = ", ".join([user.username for user in self.participants.all()])
        dog_info = f" about {self.dog.name}" if self.dog else ""
        return f"Conversation between {participants}{dog_info}"
    
    @property
    def last_message(self):
        return self.messages.first()
    
    def get_other_participant(self, user):
        """Get the other participant in the conversation"""
        return self.participants.exclude(id=user.id).first()