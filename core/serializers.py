from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task, Notification

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'


from .models import ClientLead


class ClientLeadSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(
        source="created_by.username",
        read_only=True,
    )

    class Meta:
        model = ClientLead
        fields = [
            "id",
            "client_name",
            "phone_number",
            "description",
            "followup_notes",
            "status",
            "created_by",
            "created_by_username",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_by", "created_at", "updated_at"]
        extra_kwargs = {
            "client_name": {"required": False},
            "phone_number": {"required": False},
            "description": {"required": False},
            "followup_notes": {"required": False},
            "status": {"required": False},
        }

        

from core.models import UserReport


class UserReportSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )

    class Meta:
        model = UserReport
        fields = [
            "id",
            "subject",
            "message",
            "username",
            "created_at",
        ]


from rest_framework import serializers
from .models import DaySpeciality

class DaySpecialitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DaySpeciality
        fields = "__all__"