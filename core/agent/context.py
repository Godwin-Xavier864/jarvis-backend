from django.utils import timezone
from core.models import Task, Notification, UserActivity
from django.contrib.auth.models import User

from django.utils import timezone
from datetime import timedelta
from core.models import DaySpeciality
def build_day_speciality_context():
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)

    today_special = DaySpeciality.objects.filter(date=today).first()
    tomorrow_special = DaySpeciality.objects.filter(date=tomorrow).first()

    data = {}

    if today_special:
        data["today"] = {
            "date": str(today_special.date),
            "title": today_special.title,
            "description": today_special.description,
            "poster_hint": today_special.poster_hint,
        }
    else:
        data["today"] = None

    if tomorrow_special:
        data["tomorrow"] = {
            "date": str(tomorrow_special.date),
            "title": tomorrow_special.title,
            "description": tomorrow_special.description,
            "poster_hint": tomorrow_special.poster_hint,
        }
    else:
        data["tomorrow"] = None

    return data



def build_admin_context():
    from django.contrib.auth.models import User
    from core.models import (
        Profile,
        Task,
        Notification,
        UserActivity,
        ClientLead,
        UserReport,
    )

    data = {}

    # 👤 USERS (AdminUserListView)
    data["users"] = [
        {
            "id": u.id,
            "username": u.username,
            "designation": (
                Profile.objects.filter(user=u).first().designation
                if Profile.objects.filter(user=u).exists()
                else None
            ),
            "is_admin": u.is_staff,
            "date_joined": u.date_joined,
            "last_login": u.last_login,
        }
        for u in User.objects.all()
    ]

    # 📋 TASKS (AdminTaskListView)
    data["tasks"] = [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "status": t.status,
            "deadline": t.deadline,
            "amount_paid": t.amount_paid,
            "assigned_to": (
                t.assigned_to.username if t.assigned_to else None
            ),
            "completed_at": t.completed_at,
        }
        for t in Task.objects.select_related("assigned_to").all()
    ]

    # 🔔 NOTIFICATIONS (AdminNotificationView + UserNotificationView)
    data["notifications"] = list(
        Notification.objects.values(
            "title",
            "message",
            "is_important",
            "is_plan",
            "created_at",
        )
    )

    # 📈 USER ACTIVITY (AdminActivityView)
    data["activity"] = list(
        UserActivity.objects.select_related("user").values(
            "user__username",
            "date",
        )
    )

    # 📇 CLIENT LEADS
    data["clients"] = list(
        ClientLead.objects.values(
            "client_name",
            "phone_number",
            "description",
            "followup_notes",
            "status",
            "created_at",
            "updated_at",
            "created_by__username"
        )
    )

    # 📝 USER REPORTS (AdminReportListView)
    data["reports"] = list(
        UserReport.objects.select_related("user").values(
            "id",
            "user__username",
            "subject",
            "message",
            "created_at",
        )
    )

    # ⏱️ SYSTEM META (helps AI reasoning)
    data["system"] = {
        "current_time": timezone.now(),
        "total_users": User.objects.count(),
        "total_tasks": Task.objects.count(),
        "pending_tasks": Task.objects.filter(status__iexact="pending").count(),
        "completed_tasks": Task.objects.filter(status__iexact="completed").count(),
    }
        # 🎉 DAY SPECIALITIES (Today & Tomorrow)
    data["day_specialities"] = build_day_speciality_context()


    return data


def build_user_context(user):
    from core.models import Task, Notification

    return {
        "tasks": list(
            Task.objects.filter(assigned_to=user).values(
                "title",
                "description",
                "status",
                "deadline",
                "completed_at",
            )
        ),
        "notifications": list(
            Notification.objects.values(
                "title",
                "message",
                "is_important",
            )
        ),
        # 🎉 DAY SPECIALITIES (VISIBLE TO ALL USERS)
        "day_specialities": build_day_speciality_context(),
    }
