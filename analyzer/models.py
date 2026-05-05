from django.db import models

class ChatSession(models.Model):
    """Represents one uploaded WhatsApp chat file"""
    session_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    total_messages = models.IntegerField(default=0)
    total_members = models.IntegerField(default=0)
    device_type = models.CharField(max_length=20, default='unknown')

    def __str__(self):
        return f"{self.session_name} ({self.uploaded_at.date()})"


class Message(models.Model):
    """Represents a single message in a chat"""
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    timestamp = models.DateTimeField()
    sender = models.CharField(max_length=255)
    content = models.TextField()
    is_media = models.BooleanField(default=False)
    is_system = models.BooleanField(default=False)
    emoji_count = models.IntegerField(default=0)
    has_link = models.BooleanField(default=False)
    day = models.CharField(max_length=20)
    month = models.CharField(max_length=20)
    year = models.IntegerField()
    hour = models.IntegerField()

    def __str__(self):
        return f"{self.sender}: {self.content[:50]}"
