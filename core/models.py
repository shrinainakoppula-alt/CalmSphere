from django.db import models
from django.contrib.auth.models import User

class MoodEntry(models.Model):

    MOOD_CHOICES = [
        ('happy', '😊 Happy'),
        ('sad', '😢 Sad'),
        ('stress', '😫 Stress'),
        ('calm', '😌 Calm'),
        ('angry', '😡 Angry'),
        ('excited', '🤩 Excited'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.mood}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    mobile = models.CharField(max_length=20, unique=True)
    is_admin = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    failed_otp_attempts = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} profile"


class OTPVerification(models.Model):
    PURPOSE_CHOICES = [
        ('register', 'Registration'),
        ('login', 'Login'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='otps')
    email = models.EmailField(null=True, blank=True)
    otp_hash = models.CharField(max_length=255)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default='login')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        target = self.user.username if self.user else self.email
        return f"OTP for {target} ({self.purpose}) - {'Verified' if self.is_verified else 'Pending'}"


class LoginActivity(models.Model):
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed_otp', 'Failed OTP'),
        ('locked', 'Account Locked'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_activities')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.status} at {self.timestamp}"


class UserReadingProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reading_progress')
    book_key = models.CharField(max_length=50)  # e.g., 'atomic', 'power-now', etc.
    current_page = models.IntegerField(default=0)
    current_sentence = models.IntegerField(default=0)
    percentage_completed = models.FloatField(default=0.0)
    last_read = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'book_key')

    def __str__(self):
        return f"{self.user.username} - {self.book_key} (Page {self.current_page})"


class ReadingAnalytics(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='reading_analytics')
    total_reading_time = models.IntegerField(default=0)  # in seconds
    total_listening_time = models.IntegerField(default=0)  # in seconds
    pages_completed = models.IntegerField(default=0)
    books_completed = models.IntegerField(default=0)
    reading_streak = models.IntegerField(default=0)
    last_reading_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - Streak: {self.reading_streak} days"


class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    session_key = models.CharField(max_length=255, null=True, blank=True)
    role = models.CharField(max_length=15, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.username} - {self.role} - {self.created_at}"



