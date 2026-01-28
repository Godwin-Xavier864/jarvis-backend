from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    designation = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.username} - {self.designation}"


class Task(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    amount_paid = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    null=True,
    blank=True,
)

    deadline = models.DateField()
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title


class Notification(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_important = models.BooleanField(default=False)
    is_plan = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"{self.user.username} - {self.date}"
    

# core/models.py
class AgentChat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10)  # user | assistant
    content = models.TextField()
    task_id = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    
from django.db import models
from django.contrib.auth.models import User

class ClientLead(models.Model):
    STATUS_CHOICES = [
        ("new", "New Lead"),              # ✅ ADD THIS
        ("project", "Converted to Project"),
        ("held", "On Hold"),
        ("rejected", "Rejected"),
    ]
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_client_leads",
    )

    # 👇 OWNER (used for filtering per user)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="client_leads",
    )


    

    client_name = models.CharField(max_length=200)

    phone_number = models.CharField(
        max_length=20,
        blank=True,       # ✅ ALLOW EMPTY
        null=True,
    )

    description = models.TextField(
        blank=True,       # ✅ ALLOW EMPTY
        null=True,
        help_text="What the client initially wanted",
    )

    followup_notes = models.TextField(
        blank=True,
        null=True,
        help_text="What the client said after contact",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="new",    # ✅ DEFAULT MATCHES FLUTTER
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client_name} ({self.status})"


from django.db import models
from django.contrib.auth.models import User


class UserReport(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reports",
    )

    subject = models.CharField(
        max_length=255,
        help_text="Short title of the report",
    )

    message = models.TextField(
        help_text="Detailed report from user",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.subject}"




class DaySpeciality(models.Model):
    date = models.DateField(unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    poster_hint = models.CharField(
        max_length=255,
        blank=True,
        help_text="Short hint for poster generation"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.date} - {self.title}"
