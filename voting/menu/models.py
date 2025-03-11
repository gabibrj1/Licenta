from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Appointment(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    date_time = models.DateTimeField()
    notes = models.TextField(blank=True, null=True)
    is_confirmed = models.BooleanField(default=False)
    confirmation_token = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Programare {self.name} - {self.date_time}"